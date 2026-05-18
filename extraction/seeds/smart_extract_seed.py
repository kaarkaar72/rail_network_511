import requests
import gzip
import datetime
import os
import pandas as pd
import json
import tempfile
from dotenv import load_dotenv
import logging
import sys


# Load credentials and env vars
load_dotenv()

#Constants
USERNAME = os.getenv("STOMP_USER", "user")
PASSWORD = os.getenv("STOMP_PASS", "pass")

#Temps for extracting and converting
temp_dir = tempfile.gettempdir()
LOCAL_TMP_PATH = os.path.join(temp_dir, "smart.json.gz")
#Dataset Link
SMART_URL  = "https://publicdatafeeds.networkrail.co.uk/ntrod/SupportingFileAuthenticate?type=SMART"


def download_smart_to_file(url, username, password, dest_path):
    response = requests.get(url, auth=(username, password), allow_redirects=True)
    if response.status_code != 200:
        raise Exception(f"Failed to download file: {response.status_code}")

    with open(dest_path, "wb") as f:
        f.write(response.content)
    print("Downloaded schedule file to", dest_path)


def transform_raw_to_df(input_gzip_path):
    with gzip.open(input_gzip_path, mode="rt") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    flat_df = pd.json_normalize(df['BERTHDATA'])
    return flat_df



if __name__ == "__main__":
    #Download and convert file to parquets
    download_smart_to_file(SMART_URL, USERNAME, PASSWORD, LOCAL_TMP_PATH)
    df = transform_raw_to_df(LOCAL_TMP_PATH)
    os.makedirs("data", exist_ok=True)
    csv_path = "data/td_smart.csv"
    df = df.rename(columns={
              "STEPTYPE":"step_type",
              "FROMBERTH":"from_berth",
              "TOBERTH":"to_berth",
              "STANOX":"stanox",
              "EVENT":"event",
              "PLATFORM":"platform",
              "TOLINE":"to_line",
              "BERTHOFFSET":"berth_offset",
              "ROUTE":"route",
              "FROMLINE":"from_line",
              "TD":"td",
              "COMMENT":"comment",
              "STANME":"stanme"
              })
    df.to_csv(csv_path,index=False)                            
    logging.info(f"Saved SMART CSV to {csv_path}")
