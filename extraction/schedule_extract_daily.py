import requests
import gzip
import datetime
import os
import pandas as pd
import json
import tempfile
import logging
import sys
from dotenv import load_dotenv
from google.cloud import bigquery
from google.cloud import storage
from google.oauth2 import service_account
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load env vars first so all os.getenv() calls pick them up
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(asctime)s %(name)s [%(levelname)s]: %(message)s'
)

# Constants — all driven from environment
GCP_SA_KEYFILE = os.getenv("GCP_SA_KEYFILE", "./service-account.json")
USERNAME = os.getenv("STOMP_USER", "user")
PASSWORD = os.getenv("STOMP_PASS", "pass")
BQ_PROJECT = os.getenv("BQ_PROJECT_ID", "rail-511")
BQ_DATASET = os.getenv("BQ_DATASET", "rail_data")
BQ_TABLE = os.getenv("BQ_TABLE", "rail_schedule_raw")
BUCKET_NAME = os.getenv("GCS_BUCKET", "rail_storage")

# Temp paths for extracting and converting
temp_dir = tempfile.gettempdir()
LOCAL_TMP_PATH = os.path.join(temp_dir, "schedule.json.gz")
SCHEDULE_URL = "https://publicdatafeeds.networkrail.co.uk/ntrod/CifFileAuthenticate?type=CIF_ALL_FULL_DAILY&day=toc-full"

# GCP credentials and BigQuery client
creds = service_account.Credentials.from_service_account_file(GCP_SA_KEYFILE)
bq_client = bigquery.Client(project=BQ_PROJECT, credentials=creds)
table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"


def download_schedule_to_file(url, username, password, dest_path):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=10, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    logging.info(f"Downloading schedule from {url}")
    response = session.get(url, auth=(username, password), allow_redirects=True, timeout=120)
    if response.status_code != 200:
        raise Exception(f"Failed to download file: HTTP {response.status_code}")

    with open(dest_path, "wb") as f:
        f.write(response.content)
    logging.info(f"Downloaded schedule file to {dest_path}")


def upload_to_gcs(bucket_name, output_files, dest_blob_name):
    logging.info(f"Starting upload to GCS at {dest_blob_name}")
    client = storage.Client(credentials=creds)
    bucket = client.bucket(bucket_name)

    for file_path in output_files:
        if file_path.endswith(".parquet"):
            blob_name = os.path.join(dest_blob_name, os.path.basename(file_path))
            blob = bucket.blob(blob_name)
            logging.info(f"Uploading {file_path} to gs://{bucket_name}/{blob_name}")
            blob.upload_from_filename(file_path)
            logging.info("Upload complete")


def load_gcs_pq_to_bq(gcs_uri, project, dataset, table):
    client = bigquery.Client(project=project, credentials=creds)
    table_ref = client.dataset(dataset).table(table)
    schema = [
        bigquery.SchemaField("record_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("payload", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("ingest_ts", "TIMESTAMP", mode="REQUIRED"),
    ]
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        schema=schema,
        time_partitioning=bigquery.TimePartitioning(field="ingest_ts", type_=bigquery.TimePartitioningType.DAY),
        write_disposition="WRITE_APPEND"
    )
    load_job = client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)
    load_job.result()
    logging.info(f"Loaded to BigQuery table: {table}")
    t = bq_client.get_table(table_id)
    logging.info(f"Table now has {t.num_rows} rows: {table_id}")


def transform_raw_to_loadable_parquet(input_gzip_path, output_dir, batch_size=100000):
    batch = []
    file_count = 0
    output_file_paths = []

    def write_batch(batch_data, file_num):
        df = pd.DataFrame(batch_data)
        df['payload'] = df['payload'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else None)
        df['ingest_ts'] = pd.Timestamp.utcnow()
        parquet_path = os.path.join(output_dir, f"output_{file_num}.parquet")
        df.to_parquet(parquet_path, index=False)
        logging.info(f"Wrote batch {file_num} with {len(df)} rows to {parquet_path}")
        output_file_paths.append(parquet_path)

    with gzip.open(input_gzip_path, mode="rt") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                rt = next(iter(obj.keys()))
                payload = obj[rt]
                batch.append({"record_type": rt, "payload": payload})
                if len(batch) >= batch_size:
                    write_batch(batch, file_count)
                    file_count += 1
                    batch = []
            except Exception as e:
                logging.error(f"Error parsing line: {e}")
                continue

    if batch:
        write_batch(batch, file_count)

    logging.info(f"Converted {input_gzip_path} to {len(output_file_paths)} parquet files in {output_dir}")
    return output_file_paths


if __name__ == "__main__":
    # Download CIF schedule file
    download_schedule_to_file(SCHEDULE_URL, USERNAME, PASSWORD, LOCAL_TMP_PATH)

    # Transform to Parquet
    pq_paths = transform_raw_to_loadable_parquet(LOCAL_TMP_PATH, temp_dir, 100000)

    # Upload to GCS
    blob_name = f"schedule/{datetime.datetime.now().strftime('%Y%m%d')}/"
    upload_to_gcs(BUCKET_NAME, pq_paths, blob_name)

    # Load into BigQuery
    gcs_uri = f"gs://{BUCKET_NAME}/{blob_name}output_*.parquet"
    load_gcs_pq_to_bq(gcs_uri, BQ_PROJECT, BQ_DATASET, BQ_TABLE)
