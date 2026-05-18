import streamlit as st
import pandas as pd
from datetime import datetime
from utils.bq_helpers import *
from utils.redis_helpers import *
from utils.map_helpers import *
from streamlit_autorefresh import st_autorefresh

stations_df = load_all_stations()
set_stations_df(stations_df)
st.set_page_config(page_title="UK Rail Route Browser ", layout="wide")
st.title("UK Network Rail Tracker")
tab_live, tab_routes, tab_station, tab_performance = st.tabs(["📡 Live Trains", "🗺️ Route Browser", "🚉 Station Search","🚆Performance"])
with tab_live:
    st.subheader("Live Trains")
    refresh_interval_sec = 30
    count = st_autorefresh(interval=refresh_interval_sec * 1000, limit=None, key="live_trains_auto")
    station_choice = st.selectbox("Filter by Station:", options=["All"] + sorted(stations_df["location_name"].unique()))
    redis_df = get_live_trains_for_station(station_choice)
    bq_df = get_bq_snapshot_for_station(station_choice)
    if not redis_df.empty and not bq_df.empty:
        combined_df = pd.concat([redis_df, bq_df[~bq_df["Train ID"].isin(redis_df["Train ID"])]]).reset_index(drop=True)
    elif not redis_df.empty:
        combined_df = redis_df
    elif not bq_df.empty:
        combined_df = bq_df
    else:
        combined_df = pd.DataFrame(columns=[
            "Train ID", "Train UID", "Operator", "Current Station",
            "Next Station", "Planned Type", "Planned Time", "Variation", "Status", "Last Update"
        ])

    if combined_df.empty:
        st.info("No live trains available at the moment.")
    else:
        st.dataframe(combined_df, use_container_width=True)

    train_options = combined_df["Train ID"].dropna().unique().tolist()
    selected_train = st.selectbox("Select a train to show its route & live position:", options=[""] + train_options)
    if selected_train:
        info = safe_json_load(r.get(f"train3:{selected_train}")) or {}
        train_uid = info.get("train_uid")
        if train_uid:
            format_string = "%Y-%m-%dT%H:%M:%S.%f"
            s_date = datetime.strptime(info["last_update"], format_string).date()
            route_df, coords = fetch_route_meta_for_date(train_uid,s_date,None)
            df_meta,df_schedule = draw_table(route_df)
            st.subheader(f"Schedule Information for {train_uid}")
            st.write(df_meta)
            st.subheader("Timetable")
            st.write(df_schedule) 
            if coords:
                route_layer = make_route_layer(train_uid, coords)
                station_layer, text_layer = make_station_layer(list(route_df["stops"].iloc[0]))
                live_layers = make_live_layers(info)
                layers = [layer for layer in [route_layer, station_layer, text_layer] if layer] + live_layers
                view_state = get_view_state(coords)
                st.pydeck_chart(draw_pydeck_map(layers, view_state))



with tab_routes:
    st.subheader("Route Browser (on-demand geometry)")
    q_date = st.date_input("Date for routes", datetime.utcnow().date())
    train_uids_df = get_train_uids_for_date(q_date)
    for key in ["category_filter", "status_filter", "power_filter"]:
        if key not in st.session_state:
            st.session_state[key] = []
    
    
    # Apply filters
    filtered_df = train_uids_df.copy()
    if st.session_state["category_filter"]:
        filtered_df = filtered_df[
            filtered_df["train_category"].isin(st.session_state["category_filter"])
        ]

    if st.session_state["status_filter"]:
        filtered_df = filtered_df[
            filtered_df["train_status_desc"].isin(st.session_state["status_filter"])
        ]

    if st.session_state["power_filter"]:
        filtered_df = filtered_df[
            filtered_df["power_type_desc"].isin(st.session_state["power_filter"])
        ]

    col1, col2, col3 = st.columns(3)

    category_filter = col1.multiselect(
        "Train Category",
        options=sorted(train_uids_df["train_category"].dropna().unique().tolist()),
        default=st.session_state["category_filter"],
        key="category_filter"
    )

    status_filter = col2.multiselect(
        "Train Status",
        options=sorted(filtered_df["train_status_desc"].dropna().unique().tolist()),
        default=st.session_state["status_filter"],
        key="status_filter"
    )

    power_filter = col3.multiselect(
        "Power Type",
        options=sorted(filtered_df["power_type_desc"].dropna().unique().tolist()),
        default=st.session_state["power_filter"],
        key="power_filter"
    )

    # Now apply all filters to compute final set:
    final_filtered_df = train_uids_df.copy()

    if category_filter:
        final_filtered_df = final_filtered_df[
            final_filtered_df["train_category"].isin(category_filter)
        ]

    if status_filter:
        final_filtered_df = final_filtered_df[
            final_filtered_df["train_status_desc"].isin(status_filter)
        ]

    if power_filter:
        final_filtered_df = final_filtered_df[
            final_filtered_df["power_type_desc"].isin(power_filter)
        ]


    # UID pick list
    uid_options = final_filtered_df["train_uid"].tolist()
    selected_uid = st.selectbox("Select Train UID", uid_options)
    if selected_uid:
        assoc_df = fetch_assocs_for_uid(selected_uid, q_date)
        route_df, coords = fetch_route_meta_for_date(selected_uid, q_date)
        df_meta,df_schedule = draw_table(route_df)
        st.subheader(f"Schedule Information for {selected_uid}")
        st.write(df_meta)
        st.subheader("Timetable")
        st.write(df_schedule) 
        st.subheader("Service Associations")
        st.markdown("""
        These are relationships where the selected train **joins**, **divides**, or **continues** with another
        train service at a specific station.
        """)
        st.write(assoc_df[["associated_type", "assoc_train_uid", "assoc_location"]])
        if coords:
            route_layer = make_route_layer(selected_uid, coords)
            station_layer, text_layer = make_station_layer(list(route_df["stops"].iloc[0]))
            assoc_layers = make_assoc_layer(assoc_df, q_date)
            layers = [layer for layer in [route_layer, station_layer, text_layer] if layer] + assoc_layers
            view_state = get_view_state(coords)
            st.pydeck_chart(draw_pydeck_map(layers, view_state))

with tab_station:
    st.subheader("Station Train Search")
    if "run_station_search" not in st.session_state:
        st.session_state.run_station_search = False
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.now().date()
    if "selected_time" not in st.session_state:
        st.session_state.selected_time = datetime.now().time()
    if "window_min" not in st.session_state:
        st.session_state.window_min = 180
    
    with st.form(key='my_form',width='stretch',height='stretch'):
        station_choice = st.selectbox("Select a Station", options=sorted(stations_df["location_name"].unique()))
        selected_date = st.date_input("Date", value=st.session_state.selected_date)
        selected_time = st.time_input("Time", value=st.session_state.selected_time)
        window_min = st.number_input("Time window (minutes)", min_value=0, max_value=720, value=st.session_state.window_min)
        submit_button = st.form_submit_button(label='Submit')
    
    if submit_button:
        st.session_state.selected_date = selected_date
        st.session_state.selected_time = selected_time
        st.session_state.window_min = window_min
        st.session_state.run_station_search = True
    
    if st.session_state.run_station_search:
        with st.spinner("Searching routes..."):
            query_dt = datetime.combine(selected_date, selected_time if selected_time else datetime.now().time())
            results_df = search_routes_for_station_on_datetime(station_choice,selected_date,query_dt,window_min)
            if results_df.empty:
                st.info("No services found in the time window.")
            else:
                results_df["display_time_str"] = results_df["display_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
                display = results_df[["train_uid", "origin stop", "last stop","display_time","platform"]].rename(columns={
                    "train_uid": "Train UID",
                    "platform": "Platform",
                    "display_time_str": "Time",
                    "origin stop": "Origin",
                    "last stop": "Last"
                })
                st.dataframe(display, use_container_width=True)

                # Allow selection to show route map and timetable
                selected_uid = st.selectbox("Select a Train to view route/timetable", options=display["Train UID"].unique())
                if selected_uid:
                    route_df, coords = fetch_route_meta_for_date(selected_uid, selected_date)
                    if coords:
                        route_layer = make_route_layer(selected_uid, coords)
                        station_layer, text_layer = make_station_layer(list(route_df["stops"].iloc[0]))
                        layers = [layer for layer in [route_layer, station_layer, text_layer] if layer]
                        view_state =  get_view_state(coords)
                        st.pydeck_chart(draw_pydeck_map(layers, view_state))


with tab_performance:
    delay_tab, station_perf_tab, route_perf_tab = st.tabs(["Delay Analytics","Station Performance","Routes"])
    df = load_performance()
    df2 = load_station_perf()
    df3 = load_route_perf()
    with delay_tab:
        st.header("Delay Analytics")
        # selected_date = st.date_input("Service Date", None)


        # TOC selection
        selected_toc = st.selectbox(
            "Train Operating Company (TOC)",
            options=sorted(df["toc_name"].dropna().unique().tolist()) + ["All"],
            index=0
        )

        # if selected_date:
        #     df = df[df["service_date"] == pd.to_datetime(selected_date)]
        if selected_toc != "All":
            df = df[df["toc_name"] == selected_toc]

        if df.empty:
            st.warning("No data available for the selected filters.")

        import altair as alt
        mapping = {'on_time':1,'slight_delay':2,'delay':3,'major_delay':4}
        df['delay_cat_num'] = df['delay_category'].map(mapping)
        a = df.pivot_table(values='delay_cat_num',aggfunc='count',index='toc_name',columns='delay_category',fill_value = 0)
        b = a.div(a.sum(axis=1), axis=0)*100
        df_p = b.reset_index().melt('toc_name', var_name='delay_category', value_name='percent')
        
        chart = (
        alt.Chart(df_p)
        .mark_bar()
        .encode(
            x=alt.X('percent:Q', stack='normalize', title='Percentage'),
            y=alt.Y('toc_name:N', title='TOC Name'),
            color=alt.Color('delay_category:N', title='Delay Category',sort=["on_time","slight_delay","delay","major_delay"]),
                    tooltip=['toc_name', 'delay_category', 'percent']
                )
            )

        st.altair_chart(chart, use_container_width=True)

        if selected_toc != "All":
            st.subheader(f"{selected_toc} Routes")
            a = df.pivot_table(values='delay_cat_num',aggfunc='count',index='route_desc',columns='delay_category',fill_value = 0)
            b = a.div(a.sum(axis=1), axis=0)*100
            df_p = b.reset_index().melt('route_desc', var_name='delay_category', value_name='percent')

            chart = (
            alt.Chart(df_p)
            .mark_bar()
            .encode(
                x=alt.X('percent:Q', stack='normalize', title='Percentage'),
                y=alt.Y('route_desc:N', title='train uid'),
                color=alt.Color('delay_category:N', title='Delay Category',sort=["on_time","slight_delay","delay","major_delay"]),
                        tooltip=['route_desc', 'delay_category', 'percent']
                    )
                )

            st.altair_chart(chart, use_container_width=True)
        # --------- Table ---------
        st.subheader("Detailed Records")
        st.dataframe(df)

    with station_perf_tab:
        st.subheader("Filters")

        stations = sorted(df2["location_name"].unique().tolist())
        selected_station = st.selectbox("Station", ['All']+stations,index=0)
        if selected_station != 'All':
            df_station = df2[df2["location_name"] == selected_station]
        else:
            df_station = df2

        total_events = int(df_station["total_events"].sum())
        delays = df_station["sum_delay_mins"].sum()
        pct_on_time = df_station["pct_on_time"].mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Events", f"{total_events:,}")
        col2.metric("Total Delay (mins)", f"{delays:,}")
        col3.metric("On-time %", f"{pct_on_time:.1%}")

        # -----------------------------
        # Delay Distribution
        # -----------------------------
        st.subheader("Delay Distribution (event counts)")

        dist_row = df_station.iloc[0]
        dist_df = pd.DataFrame({
            "category": ["On Time", "1-5 min", "6-10 min", ">10 min"],
            "count": [
                dist_row["on_time_events"],
                dist_row["slight_delay_events"],
                dist_row["delay_events"],
                dist_row["major_delay_events"],
            ]
        })

        chart = (
            alt.Chart(dist_df)
            .mark_bar()
            .encode(
                x=alt.X("category:N", title="Delay Category"),
                y=alt.Y("count:Q", title="Events"),
                # color = alt.Color('delay_type',sort=['on_time'])
                tooltip=["category", "count"]
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)

        # -----------------------------
        # Worst TOC Contributors
        # -----------------------------
        st.subheader("Worst TOCs Contributing to Delay")

        worst_df = df_station[["toc", "delay"]].sort_values("delay", ascending=False)
        st.dataframe(worst_df, use_container_width=True)

        # -----------------------------
        # Leaderboard Table
        # -----------------------------
        st.subheader("Station Leaderboard for This Date")

        leaderboard = (
            df2.groupby(["station_id", "location_name"])
            .agg(
                total_events=("total_events", "sum"),
                sum_delay_mins=("sum_delay_mins", "sum"),
                avg_delay=("avg_delay_mins", "mean"),
                pct_on_time=("pct_on_time", "mean"),
            )
            .reset_index()
            .sort_values("sum_delay_mins", ascending=False)
        )

        st.dataframe(leaderboard, use_container_width=True)
    with route_perf_tab:
        st.subheader("Filters")

        stations = sorted(df3["route_desc"].unique().tolist())
        selected_station = st.selectbox("Route", ['All']+stations,index=0)
        if selected_station != 'All':
            df_station = df3[df3["route_desc"] == selected_station]
        else:
            df_station = df3

        total_events = int(df_station["total_events"].sum())
        delays = df_station["sum_delay_mins"].sum()
        # pct_on_time = df_station["pct_on_time"].mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Events", f"{total_events:,}")
        col2.metric("Total Delay (mins)", f"{delays:,}")
        # col3.metric("On-time %", f"{pct_on_time:.1%}")

        # -----------------------------
        # Delay Distribution
        # -----------------------------
        st.subheader("Delay Distribution (event counts)")

        dist_row = df_station.iloc[0]
        dist_df = pd.DataFrame({
            "category": ["On Time", "1-5 min", "6-10 min", ">10 min"],
            "count": [
                dist_row["on_time_events"],
                dist_row["slight_delay_events"],
                dist_row["delay_events"],
                dist_row["major_delay_events"],
            ]
        })

        chart = (
            alt.Chart(dist_df)
            .mark_bar()
            .encode(
                x=alt.X("category:N", title="Delay Category"),
                y=alt.Y("count:Q", title="Events"),
                # color = alt.Color('delay_type',sort=['on_time'])
                tooltip=["category", "count"]
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)

        # -----------------------------
        # Worst TOC Contributors
        # -----------------------------
        st.subheader("Worst TOCs Contributing to Delay")

        worst_df = df_station[["train_uid","route_desc", "sum_delay_mins"]].sort_values("sum_delay_mins", ascending=False)
        st.dataframe(worst_df, use_container_width=True)

        # -----------------------------
        # Leaderboard Table
        # -----------------------------
        st.subheader("Station Leaderboard for This Date")

        leaderboard = (
            df_station.groupby(["train_uid","route_desc"])
            .agg(
                total_events=("total_events", "sum"),
                sum_delay_mins=("sum_delay_mins", "sum"),
            )
            .reset_index()
            .sort_values("sum_delay_mins", ascending=False)
        )

        st.dataframe(leaderboard, use_container_width=True)