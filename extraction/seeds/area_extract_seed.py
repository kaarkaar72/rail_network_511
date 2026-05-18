import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

url = "https://wiki.openraildata.com/index.php/List_of_Train_Describers"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Find the first table with class wikitable
table = soup.find("table", class_="wikitable")

# Get all rows
rows = table.find_all("tr")

data = []
# header row to identify columns
headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

for row in rows[1:]:
    cols = row.find_all(["td", "th"])
    text_cols = [col.get_text(strip=True) for col in cols]
    if len(text_cols) == len(headers):
        data.append(text_cols)

# Create DataFrame
df = pd.DataFrame(data, columns=headers)

# Normalize column names
df = df.rename(columns={
    "ID": "area_id",
    "Name": "name",
    "SIG": "sig",
    "RTE": "rte",
    "LAT": "lat",
    "TRK": "trk",
    "PTS": "pts",
    "LXG": "lxg",
    "Commissioning": "commissioning"
})

# Columns to convert to boolean
boolean_cols = ["sig", "rte", "lat", "trk", "pts", "lxg"]

# Convert ✔ to True, blank or ? to False
for col in boolean_cols:
    df[col] = df[col].apply(lambda x: True if x == "✔" else False)

# Save CSV
os.makedirs("data", exist_ok=True)
csv_path = "data/td_area.csv"
df.to_csv(csv_path, index=False)
print(f"✅ Saved cleaned TD area seed to {csv_path}")
