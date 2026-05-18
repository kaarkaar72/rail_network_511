# utils/bq_helpers.py
import os
import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# -------------------- CONFIG --------------------
BQ_PROJECT = os.getenv("BQ_PROJECT_ID", "rail-511")
BQ_DATASET = os.getenv("BQ_DATASET", "rail_data")
SA_JSON = os.getenv("GCP_SA_KEYFILE", "./service-account.json")

creds = service_account.Credentials.from_service_account_file(SA_JSON)
bq_client = bigquery.Client(project=BQ_PROJECT, credentials=creds)

# -------------------- BASIC HELPERS --------------------

@st.cache_data(ttl=3600)  # cache for 1 hour
def get_train_uids_for_date(query_date: date):
    """
    Return a small dataframe containing train_uid and summary metadata for the given date.
    We only fetch ID and light columns so the select list is small.
    """
    sql = f"""
    WITH s AS (
      SELECT train_uid,
            COALESCE(train_category,"UNKNOWN") as train_category,
            COALESCE(train_status_desc,"UNKNOWN") as train_status_desc,
            COALESCE(power_type_desc,"UNKNOWN") as power_type_desc
      FROM `{BQ_PROJECT}.{BQ_DATASET}.dim_train_schedule` dts
      WHERE DATE('{query_date.isoformat()}') BETWEEN schedule_start_date AND schedule_end_date
        AND (
        (EXTRACT(DAYOFWEEK FROM DATE('{query_date.isoformat()}')) = 2 AND mon_service) OR
        (EXTRACT(DAYOFWEEK FROM DATE('{query_date.isoformat()}')) = 3 AND tue_service) OR
        (EXTRACT(DAYOFWEEK FROM DATE('{query_date.isoformat()}')) = 4 AND wednes_service ) OR
        (EXTRACT(DAYOFWEEK FROM DATE('{query_date.isoformat()}')) = 5 AND thrus_service ) OR
        (EXTRACT(DAYOFWEEK FROM DATE('{query_date.isoformat()}')) = 6 AND fri_service ) OR
        (EXTRACT(DAYOFWEEK FROM DATE('{query_date.isoformat()}')) = 7 AND sat_service ) OR
        (EXTRACT(DAYOFWEEK FROM DATE('{query_date.isoformat()}')) = 1 AND sun_service )
        )
    )
    SELECT DISTINCT train_uid,train_category,train_status_desc,power_type_desc
    FROM s
    ORDER BY train_uid
    """
    df = bq_client.query(sql).to_dataframe()
    return df
@st.cache_data(ttl=3600)  # cache for 1 hour
def fetch_route_meta_for_date(train_uid: str = None, query_date: date = None, station: str = None):
    """
    Fetch route-level metadata (flat) for the date.
    We'll return train_uid and arrays of stops + timetable arrays (as JSON-encoded strings).
    This should be used for search or to populate a small 'index' list.
    """
    sql = f"""
    WITH s AS (
        SELECT
            dts.train_uid,
            dts.train_signalling_id,
            dtoc.toc_name,
            dts.short_term_planning_schedule_indicator as stp,
            dts.train_category,
            dts.train_category_desc,
            dts.train_status_desc,
            dts.reservations_desc,
            dts.operating_characteristic_desc,
            dts.power_type_desc,
            dts.planned_speed,
            fsl.loc_offset,
            fsl.location_type_desc,
            dg.location_name,
            dg.longitude,
            dg.latitude,
            fsl.arrival_public_timetable_time AS arr_pub,
            fsl.departure_public_timetable_time AS dep_pub,
            fsl.arrival_working_timetable_time AS arr_wtt,
            fsl.departure_working_timetable_time AS dep_wtt,
            fsl.passing_working_timetable_time AS pass_wtt,
            fsl.platform,
            dts.mon_service,
            dts.tue_service,
            dts.wednes_service,
            dts.thrus_service,
            dts.fri_service,
            dts.sat_service,
            dts.sun_service
        FROM `{BQ_PROJECT}.{BQ_DATASET}.fact_train_scheduled_location` fsl
        JOIN `{BQ_PROJECT}.{BQ_DATASET}.dim_train_schedule` dts
            ON fsl.schedule_id = dts.schedule_id
        JOIN `{BQ_PROJECT}.{BQ_DATASET}.dim_geo` dg
            ON fsl.location_id = dg.location_id
        LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.dim_toc` dtoc
            ON dts.atoc_code = dtoc.toc_schedule_code
        WHERE  (@train_uid IS NULL OR dts.train_uid = @train_uid)
          AND dg.latitude IS NOT NULL 
          AND dg.longitude IS NOT NULL
          AND DATE(@query_date) BETWEEN dts.schedule_start_date AND dts.schedule_end_date
          AND (
                (EXTRACT(DAYOFWEEK FROM DATE(@query_date)) = 2 AND mon_service) OR
                (EXTRACT(DAYOFWEEK FROM DATE(@query_date)) = 3 AND tue_service) OR
                (EXTRACT(DAYOFWEEK FROM DATE(@query_date)) = 4 AND wednes_service) OR
                (EXTRACT(DAYOFWEEK FROM DATE(@query_date)) = 5 AND thrus_service) OR
                (EXTRACT(DAYOFWEEK FROM DATE(@query_date)) = 6 AND fri_service) OR
                (EXTRACT(DAYOFWEEK FROM DATE(@query_date)) = 7 AND sat_service) OR
                (EXTRACT(DAYOFWEEK FROM DATE(@query_date)) = 1 AND sun_service)
          )
    ), t as(
    SELECT
        train_uid,
        stp,
        toc_name,
        train_signalling_id,
        train_status_desc,
        train_category,
        train_category_desc,
        reservations_desc,
        operating_characteristic_desc,
        planned_speed,
        power_type_desc,
        ARRAY_AGG(location_name ORDER BY loc_offset) AS stops,
        ARRAY_AGG(location_type_desc ORDER BY loc_offset) AS stops_type,
        ARRAY_AGG(STRUCT(longitude,latitude) ORDER BY loc_offset) AS route_path,
        ARRAY_AGG(COALESCE(CAST(arr_pub AS STRING), '--') ORDER BY loc_offset) AS tt_arr_pub,
        ARRAY_AGG(COALESCE(CAST(dep_pub AS STRING), '--') ORDER BY loc_offset) AS tt_dep_pub,
        ARRAY_AGG(COALESCE(CAST(arr_wtt AS STRING), '--') ORDER BY loc_offset) AS tt_arr_wtt,
        ARRAY_AGG(COALESCE(CAST(dep_wtt AS STRING), '--') ORDER BY loc_offset) AS tt_dep_wtt,
        ARRAY_AGG(COALESCE(CAST(pass_wtt AS STRING), '--') ORDER BY loc_offset) AS tt_pass_wtt,
        ARRAY_AGG(COALESCE(platform, '--') ORDER BY loc_offset) AS platforms
    FROM s
    GROUP BY train_uid, stp,toc_name,train_signalling_id, planned_speed, train_category, 
             train_category_desc, train_status_desc, power_type_desc,
             reservations_desc, operating_characteristic_desc
    )

    SELECT *
    FROM t
    WHERE (@station IS NULL OR @station IN UNNEST(stops))
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("train_uid", "STRING", train_uid),
            bigquery.ScalarQueryParameter("query_date", "DATE", query_date),
            bigquery.ScalarQueryParameter("station", "STRING", station),
        ]
    )
    df = bq_client.query(sql,job_config=job_config).to_dataframe()

    coords = []
    if not df.empty and "route_path" in df.columns and not df["route_path"].isna().all():
        try:
            coords = [(c["longitude"], c["latitude"]) for c in df["route_path"].iloc[0]]
        except Exception:
            coords = []

    return df, coords

@st.cache_data(ttl=3600)  # cache for 1 hour
def fetch_assocs_for_uid(train_uid: str, assoc_date: date) -> pd.DataFrame:
    sql = f"""
        WITH s AS (
            SELECT
                da.assoc_train_uid,
                da.associated_type,
                da.assoc_location

            FROM `{BQ_PROJECT}.{BQ_DATASET}.dim_train_association` da
            WHERE (@train_uid IS NULL OR da.main_train_uid = @train_uid)
            AND DATE(@assoc_date) BETWEEN da.assoc_start_date AND da.assoc_end_date
            AND (
                    (EXTRACT(DAYOFWEEK FROM DATE(@assoc_date)) = 2 AND mon_service) OR
                    (EXTRACT(DAYOFWEEK FROM DATE(@assoc_date)) = 3 AND tue_service) OR
                    (EXTRACT(DAYOFWEEK FROM DATE(@assoc_date)) = 4 AND wednes_service) OR
                    (EXTRACT(DAYOFWEEK FROM DATE(@assoc_date)) = 5 AND thrus_service) OR
                    (EXTRACT(DAYOFWEEK FROM DATE(@assoc_date)) = 6 AND fri_service) OR
                    (EXTRACT(DAYOFWEEK FROM DATE(@assoc_date)) = 7 AND sat_service) OR
                    (EXTRACT(DAYOFWEEK FROM DATE(@assoc_date)) = 1 AND sun_service)
            )
        )
        SELECT DISTINCT *
        FROM s
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("train_uid", "STRING", train_uid),
            bigquery.ScalarQueryParameter("assoc_date", "DATE", assoc_date),
        ]
    )
    df = bq_client.query(sql,job_config=job_config).to_dataframe()
    return df

@st.cache_data(ttl=3600)  # cache for 1 hour
def get_bq_snapshot_for_station(station_name: str = None) -> pd.DataFrame:
    if station_name and station_name != "All":
        sql = f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.live_train`
        WHERE location_name = @station
        ORDER BY scheduled_event_timestamp
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("station", "STRING", station_name)]
        )
    else:
        sql = f"SELECT * FROM `{BQ_PROJECT}.{BQ_DATASET}.live_train` ORDER BY scheduled_event_timestamp"
        job_config = None

    return bq_client.query(sql, job_config=job_config).to_dataframe()

@st.cache_data(ttl=3600)  # cache for 1 hour
def load_all_stations() -> pd.DataFrame:
    sql = f"SELECT location_id, location_name, latitude, longitude FROM `{BQ_PROJECT}.{BQ_DATASET}.dim_geo` WHERE latitude IS NOT NULL"
    return bq_client.query(sql).to_dataframe()

@st.cache_data(ttl=3600)  # cache for 1 hour
def load_performance():
    sql = f"""
    SELECT *
    FROM `{BQ_PROJECT}.{BQ_DATASET}.train_delay`
    """
    df = bq_client.query(sql).to_dataframe()
    return df

def load_station_perf():
    sql = f"""
    WITH s AS (
    SELECT
        dl.station_id,
        dl.location_name,
        DATE(tsv.planned_timestamp) AS service_date,

        -- core metrics
        SUM(timetable_variation) AS sum_delay_mins,
        COUNT(*) AS total_events,
        SUM(CASE WHEN event_type = 'DEPARTURE' THEN 1 ELSE 0 END) AS total_departures,
        SUM(CASE WHEN event_type = 'ARRIVAL' THEN 1 ELSE 0 END) AS total_arrivals,

        -- delay buckets
        SUM(CASE WHEN timetable_variation <= 0 THEN 1 ELSE 0 END) AS on_time_events,
        SUM(CASE WHEN timetable_variation BETWEEN 1 AND 5 THEN 1 ELSE 0 END) AS slight_delay_events,
        SUM(CASE WHEN timetable_variation BETWEEN 6 AND 10 THEN 1 ELSE 0 END) AS delay_events,
        SUM(CASE WHEN timetable_variation > 10 THEN 1 ELSE 0 END) AS major_delay_events,

        -- top 5 worst TOCs
        ARRAY_AGG(
        STRUCT(
            dt.toc_name AS toc,
            timetable_variation AS delay
        )
        ORDER BY timetable_variation DESC
        LIMIT 5
        ) AS worst_tocs

    FROM `rail_data.fact_train_movement` tsv
    LEFT JOIN `rail_data.dim_location` dl
        ON tsv.location_id = dl.location_id
    LEFT JOIN `rail_data.dim_toc` dt
        ON tsv.toc_id = dt.toc_id

    WHERE tsv.actual_timestamp IS NOT NULL
    GROUP BY 1,2,3
    )

    SELECT
    station_id,
    location_name,
    service_date,
    sum_delay_mins,
    total_events,
    total_departures,
    total_arrivals,
    on_time_events,
    slight_delay_events,
    delay_events,
    major_delay_events,
    SAFE_DIVIDE(on_time_events, total_events) AS pct_on_time,
    SAFE_DIVIDE(sum_delay_mins, NULLIF(total_events,0)) AS avg_delay_mins,
    toc,
    delay

    FROM s, UNNEST(worst_tocs)
    WHERE location_name IS NOT NULL
    ORDER BY service_date DESC, sum_delay_mins DESC

    """
    df = bq_client.query(sql).to_dataframe()
    return df


def load_route_perf():
    sql = f"""
    WITH s AS (
    SELECT
        dts.schedule_id,
        dts.train_uid,
        DATE(tsv.planned_timestamp) AS service_date,

        -- core metrics
        SUM(timetable_variation) AS sum_delay_mins,
        COUNT(*) AS total_events,
        SUM(CASE WHEN event_type = 'DEPARTURE' THEN 1 ELSE 0 END) AS total_departures,
        SUM(CASE WHEN event_type = 'ARRIVAL' THEN 1 ELSE 0 END) AS total_arrivals,

        -- delay buckets
        SUM(CASE WHEN timetable_variation <= 0 THEN 1 ELSE 0 END) AS on_time_events,
        SUM(CASE WHEN timetable_variation BETWEEN 1 AND 5 THEN 1 ELSE 0 END) AS slight_delay_events,
        SUM(CASE WHEN timetable_variation BETWEEN 6 AND 10 THEN 1 ELSE 0 END) AS delay_events,
        SUM(CASE WHEN timetable_variation > 10 THEN 1 ELSE 0 END) AS major_delay_events,

    FROM `rail_data.fact_train_movement` tsv
    LEFT JOIN `rail_data.dim_train_schedule`dts
        ON tsv.schedule_id = dts.schedule_id

    WHERE tsv.actual_timestamp IS NOT NULL
    GROUP BY 1,2,3
    )

    SELECT
    s.train_uid,origin,terminating,route_desc,service_date,sum_delay_mins,total_events,total_departures,total_arrivals,on_time_events,slight_delay_events,delay_events,major_delay_events
    FROM s
    LEFT JOIN `rail_data.route_start_stop` rss on s.train_uid = rss.train_uid and s.schedule_id = rss.schedule_id
    WHERE route_desc is not null
    """
    df = bq_client.query(sql).to_dataframe()
    return df



def search_routes_for_station_on_datetime(station_choice,selected_date,query_dt,window_min):
    meta_df, coords = fetch_route_meta_for_date(None, selected_date, station_choice)
    results_df = pd.DataFrame()
    if not meta_df.empty:
        results = []

        for _, r in meta_df.iterrows():
            stops = r["stops"].tolist()
            tt_arr = r["tt_arr_pub"].tolist()
            tt_dep = r["tt_dep_pub"].tolist()
            tt_pass = r["tt_pass_wtt"].tolist()
            platforms = r["platforms"].tolist()

            if station_choice not in stops:
                continue
            idx = stops.index(station_choice)
            arr_pub_t = tt_arr[idx] if idx < len(tt_arr) else None
            dep_pub_t = tt_dep[idx] if idx < len(tt_dep) else None
            pass_pub_t = tt_pass[idx] if idx < len(tt_pass) else None
            display_time = dep_pub_t or arr_pub_t or pass_pub_t

            # convert to datetime
            try:
                display_dt = datetime.combine(selected_date, datetime.strptime(display_time, "%H:%M:%S").time())
            except:
                display_dt = None

            if display_dt is None:
                continue

            lower = query_dt - timedelta(minutes=window_min)
            upper = query_dt + timedelta(minutes=window_min)
            if not (lower <= display_dt <= upper):
                continue

            results.append({
                "train_uid": r["train_uid"],
                "platform": platforms[idx],
                "origin stop": stops[0],
                "last stop": stops[-1],
                "display_time": display_dt,
            })

        results_df = pd.DataFrame(results).sort_values("display_time") if results else pd.DataFrame()
    return results_df