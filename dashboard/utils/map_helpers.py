# utils/map_helpers.py
import pandas as pd
import geopandas as gpd
import pydeck as pdk
from shapely.geometry import LineString
from utils.bq_helpers import *
from typing import List, Dict, Tuple, Optional

stations_df = None

def set_stations_df(df):
    global stations_df
    stations_df = df

ASSOC_COLOR = {
    "join": [0, 200, 0],      # green
    "divide": [255, 140, 0],  # orange
    "next": [155, 48, 255],   # purple
}

def make_route_layer(selected_uid, coords, width=200, color=[255,0,0]):
    if not coords or len(coords) < 2:
        return None
    line = LineString(coords)
    sel_gdf = gpd.GeoDataFrame([{"train_uid": selected_uid, "geometry": line}], geometry="geometry")
    return pdk.Layer(
        "GeoJsonLayer",
        sel_gdf,
        pickable=True,
        stroked=True,
        filled=False,
        get_line_color=color,
        get_line_width=width
    )

def make_assoc_layer(assoc_df,q_date):
    assoc_layers = []
    for _,assoc_row in assoc_df.iterrows():
        assoc_uid = assoc_row['assoc_train_uid']
        assoc_type = assoc_row['associated_type']
        assoc_location = assoc_row['assoc_location']
        assoc_meta, assoc_coords = fetch_route_meta_for_date(assoc_uid,q_date)
        assoc_stops = list(assoc_meta["stops"].tolist()[0])


        route_layer = make_route_layer(assoc_uid,assoc_coords,100,ASSOC_COLOR.get(assoc_type, [200, 200, 200]))
        assoc_layers.append(route_layer)

        station_layer,text_layer = make_station_layer(assoc_stops)
        assoc_layers.append(station_layer)
        assoc_layers.append(text_layer)

        assoc_station_row = stations_df[stations_df["location_name"] == assoc_location]
        if not assoc_station_row.empty:
            assoc_layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    assoc_station_row,
                    get_position='[longitude, latitude]',
                    get_fill_color=[100,100,100],
                    get_radius=600,
                )
            )
    return assoc_layers

def make_station_layer(stops: list):
    station_layer,text_layer = [],[]
    if stops and len(stops) > 1:
        route_stations = stations_df[stations_df["location_name"].isin(stops)].copy()
        route_stations["color_rgb"] = [[0, 250, 0] for _ in range(len(route_stations))]
        station_layer = pdk.Layer("ScatterplotLayer", route_stations,
                                get_position='[longitude, latitude]',
                                get_fill_color='color_rgb', get_radius=300, pickable=True)
        text_layer = pdk.Layer("TextLayer", route_stations,
                            get_position='[longitude, latitude]',
                            get_text="location_name", get_size=12,
                            get_color=[255,255,255], get_alignment_baseline="'bottom'")
    return station_layer,text_layer
   



def make_live_layers(info: Dict) -> List[pdk.Layer]:
    """
    Create layers for live train position and trail.
    """
    layers = []
    if not info:
        return layers

    train = info.get("train_id")
    lat = info.get("latitude")
    lon = info.get("longitude")
    trail = info.get("trail", [])

    # Live train point
    if lat and lon:
        df_point = pd.DataFrame([{"train_id": train, "longitude": lon, "latitude": lat}])
        point_layer = pdk.Layer(
            "ScatterplotLayer",
            df_point,
            get_position='[longitude, latitude]',
            get_fill_color=[255, 215, 0],
            get_radius=300,
            pickable=True
        )
        layers.append(point_layer)

    # Trail
    if trail and len(trail) > 1:
        df_trail = pd.DataFrame([{"train_id": train, "path": trail}])
        trail_layer = pdk.Layer(
            "PathLayer",
            df_trail,
            get_path="path",
            get_color=[255, 255, 255],
            width_scale=1,
            get_width=40,
            pickable=False
        )
        layers.append(trail_layer)

    return layers

def get_view_state(coords):
    if not coords:
        return pdk.ViewState(latitude=52.5, longitude=-1.5, zoom=6, pitch=0)
    lats = [c[1] for c in coords]
    lons = [c[0] for c in coords]
    return pdk.ViewState(latitude=sum(lats)/len(lats), longitude=sum(lons)/len(lons), zoom=10, pitch=0)

def draw_pydeck_map(layers: List[pdk.Layer], view_state: Optional[pdk.ViewState] = None) -> pdk.Deck:
    """
    Return a PyDeck Deck object for Streamlit.
    """
    if view_state is None:
        view_state = pdk.ViewState(latitude=52.5, longitude=-1.5, zoom=6, pitch=0)
    return pdk.Deck(layers=layers, initial_view_state=view_state, tooltip={"text": "{location_name}"})

def draw_table(route_df):
    print(route_df)
    stops = list(route_df["stops"].tolist()[0])
    stops_type = list(route_df["stops_type"].tolist()[0])  
    pub_start_times = list(route_df["tt_arr_pub"].tolist()[0])
    pub_end_times = list(route_df["tt_dep_pub"].tolist()[0])
    tt_start_times = list(route_df["tt_arr_wtt"].tolist()[0])
    tt_end_times = list(route_df["tt_dep_wtt"].tolist()[0])
    tt_pass_times = list(route_df["tt_pass_wtt"].tolist()[0])
    platforms = list(route_df["platforms"].tolist()[0])
    df_meta_table = pd.DataFrame({"HC":route_df["train_signalling_id"],
            "TOC":   route_df["toc_name"],
            "Schedule Status": route_df["stp"],
            "Transportation":route_df["train_category"],
            "Type": route_df["train_status_desc"],
            "Mode": route_df["power_type_desc"],
            "Speed of Travel": route_df["planned_speed"]})
    df_sch_table = pd.DataFrame({
                    "Station": stops,
                    "Platform": platforms,
                    "Type" : stops_type,
                    "Arr (Public)": pub_start_times,
                    "Dep (Public)": pub_end_times,
                    "Arr (Timetable)": tt_start_times,
                    "Dep (Timetable)": tt_end_times,
                    "Pass (Timetable)": tt_pass_times,
            })

    return df_meta_table,df_sch_table


