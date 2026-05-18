import os
import redis
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

MAX_TRAIL_POINTS = 20
STALE_MINUTES = 5
REDIS_DB = "train3"

def safe_json_load(s):
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None

def get_all_train_positions_redis(prefix=f"{REDIS_DB}:*") -> list:
    keys = r.keys(prefix)
    data = []
    for k in keys:
        raw = r.get(k)
        info = safe_json_load(raw)
        if info:
            data.append(info)
    return data

def get_live_trains_for_station(station_name: str):
    """
    Fetch all trains currently at or approaching the station from Redis.
    Returns a DataFrame with train_id, train_uid, operator, location, next_station, and last_update.
    """
    all_live = get_all_train_positions_redis()  
    if not all_live:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_live)
    # Keep only trains currently at this station or heading there
    if station_name != 'All':
        df = df[(df["location_name"] == station_name) | (df["next_station"] == station_name)]
    
    if df.empty:
        return pd.DataFrame()
    
    df["Train ID"] = df["train_id"]
    df["Train UID"] = df.get("train_uid", None)
    df["Operator"] = df.get("toc_name", "")
    df["Current Station"] = df.get("location_name", "")
    df["Next Station"] = df.get("next_station", "")
    df["Planned Type"] = df.get("planned_event_type")
    df["Planned Time"] = df.get("planned_timestamp", "")
    df["Variation"] = df.get("timetable_variation", "")
    df["Status"] = df.get("variation_status", "")
    df["Last Update"] = df.get("last_update", "")
    
    return df[[
        "Train ID", "Train UID", "Operator", "Current Station",
        "Next Station", "Planned Type", "Planned Time", "Variation", "Status", "Last Update"
    ]]