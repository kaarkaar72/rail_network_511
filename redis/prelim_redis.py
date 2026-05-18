import os
import json
import logging
import pandas as pd
import redis
from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

BQ_PROJECT = os.getenv("BQ_PROJECT_ID", "rail-511")
BQ_DATASET = os.getenv("BQ_DATASET", "rail_data")
GCP_SA_KEYFILE = os.getenv("GCP_SA_KEYFILE", "./service-account.json")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


def load_geo(bq_client, r):
    geo_query = f"""
    SELECT location_id, location_name, latitude, longitude
    FROM `{BQ_PROJECT}.{BQ_DATASET}.dim_geo`
    """
    geo_df = bq_client.query(geo_query).to_dataframe()
    logging.info(f"Loading {len(geo_df)} geo records into Redis...")

    pipe = r.pipeline(transaction=False)
    for _, row in geo_df.iterrows():
        key = f"geo:{row['location_id']}"
        value = json.dumps({
            "location_name": row['location_name'],
            "lat": row['latitude'],
            "lon": row['longitude']
        })
        pipe.set(key, value)
    pipe.execute()
    logging.info("dim_geo loaded into Redis")


def load_schedules(bq_client, r):
    schedule_query = f"""
    SELECT schedule_id, train_uid, stp_indicator, schedule_start_date, schedule_end_date,
           mon_service, tue_service, wednes_service, thrus_service, fri_service, sat_service, sun_service
    FROM `{BQ_PROJECT}.{BQ_DATASET}.dim_train_schedule`
    """
    schedule_df = bq_client.query(schedule_query).to_dataframe()
    logging.info(f"Loading {len(schedule_df)} schedule records into Redis...")

    # Group by train_uid for efficient batch writes
    schedules_by_uid = {}
    for _, row in schedule_df.iterrows():
        uid = row["train_uid"]
        record = {
            "schedule_id": row["schedule_id"],
            "stp_indicator": row["stp_indicator"],
            "start_date": row["schedule_start_date"].isoformat(),
            "end_date": row["schedule_end_date"].isoformat(),
            "mon": bool(row["mon_service"]),
            "tue": bool(row["tue_service"]),
            "wed": bool(row["wednes_service"]),
            "thu": bool(row["thrus_service"]),
            "fri": bool(row["fri_service"]),
            "sat": bool(row["sat_service"]),
            "sun": bool(row["sun_service"])
        }
        schedules_by_uid.setdefault(uid, []).append(record)

    pipe = r.pipeline(transaction=False)
    for uid, records in schedules_by_uid.items():
        pipe.set(f"schedule:{uid}", json.dumps(records))
    pipe.execute()
    logging.info("dim_schedule loaded into Redis")


def main():
    creds = service_account.Credentials.from_service_account_file(GCP_SA_KEYFILE)
    bq_client = bigquery.Client(project=BQ_PROJECT, credentials=creds)
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    load_geo(bq_client, r)
    load_schedules(bq_client, r)
    logging.info("Redis warm-up complete.")


if __name__ == "__main__":
    main()
