import os
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------
# 01_download_banxico_data.py
# Purpose:
# Download headline, core and non-core annual inflation
# series from Banco de México SIE API and save them as raw CSV.
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

BANXICO_TOKEN = os.getenv("BANXICO_TOKEN")

if not BANXICO_TOKEN:
    raise ValueError(
        "BANXICO_TOKEN was not found. Create a .env file with: "
        "BANXICO_TOKEN=your_token_here"
    )

SERIES = {
    "SP30578": "headline_inflation_annual",
    "SP74662": "core_inflation_annual",
    "SP74665": "non_core_inflation_annual",
}

START_DATE = "2000-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

headers = {
    "Bmx-Token": BANXICO_TOKEN
}

all_series = []
metadata_rows = []

for series_id, series_name in SERIES.items():
    url = (
        f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/"
        f"{series_id}/datos/{START_DATE}/{END_DATE}"
    )

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"Banxico API request failed for {series_id}. "
            f"Status code: {response.status_code}\\n"
            f"Response text: {response.text[:500]}"
        )

    data = response.json()

    series = data["bmx"]["series"][0]
    series_title = series.get("titulo", "")
    observations = series.get("datos", [])

    if not observations:
        raise RuntimeError(
            f"The API returned no observations for {series_id}. "
            "Check the series ID, token or date range."
        )

    df = pd.DataFrame(observations)

    df["date"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df["value"] = (
        df["dato"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace({"N/E": None})
    )

    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df[["date", "value"]].dropna().sort_values("date")

    df["series_id"] = series_id
    df["series_name"] = series_name
    df["series_title"] = series_title
    df["download_date"] = datetime.today().strftime("%Y-%m-%d")

    all_series.append(df)

    metadata_rows.append(
        {
            "series_id": series_id,
            "series_name": series_name,
            "series_title": series_title,
            "start_date": START_DATE,
            "end_date": END_DATE,
            "download_date": datetime.today().strftime("%Y-%m-%d"),
            "api_url_without_token": url,
            "observations": len(df),
            "first_observation": df["date"].min().date(),
            "last_observation": df["date"].max().date(),
        }
    )

raw_long = pd.concat(all_series, ignore_index=True)

output_path = RAW_DIR / "banxico_inflation_series_long.csv"
raw_long.to_csv(output_path, index=False, encoding="utf-8-sig")

metadata = pd.DataFrame(metadata_rows)
metadata_path = RAW_DIR / "banxico_inflation_metadata.csv"
metadata.to_csv(metadata_path, index=False, encoding="utf-8-sig")

print("Banxico inflation series downloaded successfully.")
print(f"Series downloaded: {len(SERIES)}")
print(f"Raw data saved to: {output_path}")
print(f"Metadata saved to: {metadata_path}")
print("\nMetadata:")
print(metadata.to_string(index=False))

print("\nFirst rows:")
print(raw_long.head().to_string(index=False))

print("\nLast rows:")
print(raw_long.tail().to_string(index=False))