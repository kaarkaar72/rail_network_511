import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

url = "https://wiki.openraildata.com/index.php/STANOX_Areas"
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
    "STANOX Code": "stanox_code",
    "BR Region": "br_region",
    "Main Locations": "locations"
})

df['stanox_code'] = df['stanox_code'].str.slice(0, 2)

# Save CSV
os.makedirs("data", exist_ok=True)
csv_path = "data/stanox.csv"
df.to_csv(csv_path, index=False)
print(f"✅ Saved cleaned stanox seed to {csv_path}")
