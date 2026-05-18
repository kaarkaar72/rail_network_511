import requests
import os
import pandas as pd
from io import StringIO

# URL for the CSV (NaPTAN Open Data CSV export)
# You can adjust the endpoint for stop points, rail, bus, etc.
CSV_URL = "https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=csv"

response = requests.get(CSV_URL)
response.raise_for_status()

# Read CSV into pandas directly from the text
naptan_df = pd.read_csv(StringIO(response.text))
cols = ['ATCOCode','CommonName','Street','Indicator','Bearing',
        'LocalityName','ParentLocalityName','GridType','Easting','Northing','Longitude','Latitude','StopType',
        'CreationDateTime','ModificationDateTime','Status']
naptan_df = naptan_df[cols]

os.makedirs("data", exist_ok=True)
csv_path = "data/stops.csv"
naptan_df.to_csv(csv_path, index=False)
print(f"✅ Saved cleaned seed to {csv_path}")
