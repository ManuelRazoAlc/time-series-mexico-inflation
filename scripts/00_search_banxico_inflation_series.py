import os
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

BANXICO_TOKEN = os.getenv("BANXICO_TOKEN")

if not BANXICO_TOKEN:
    raise ValueError("BANXICO_TOKEN not found in .env")

# Candidate series IDs related to inflation.
# The script will print the title returned by Banxico for each one.
CANDIDATE_SERIES = [
    "SP74662",
    "SP74663",
    "SP74664",
    "SP74665",
    "SF61745",
    "SF60634",
    "SF43718",
    "SF43773",
]

START_DATE = "2000-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

headers = {
    "Bmx-Token": BANXICO_TOKEN
}

print("Testing candidate Banxico inflation series")
print("=========================================\n")

for series_id in CANDIDATE_SERIES:
    url = (
        f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/"
        f"{series_id}/datos/{START_DATE}/{END_DATE}"
    )

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"{series_id}: request failed with status {response.status_code}")
            continue

        data = response.json()
        series = data["bmx"]["series"][0]

        title = series.get("titulo", "No title")
        observations = series.get("datos", [])

        first_date = observations[0]["fecha"] if observations else "No data"
        last_date = observations[-1]["fecha"] if observations else "No data"

        print(f"Series ID: {series_id}")
        print(f"Title: {title}")
        print(f"Observations: {len(observations)}")
        print(f"First date: {first_date}")
        print(f"Last date: {last_date}")
        print("-" * 60)

    except Exception as e:
        print(f"{series_id}: error -> {e}")
        print("-" * 60)