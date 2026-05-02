from pathlib import Path

import pandas as pd

# ---------------------------------------------------------
# 02_prepare_inflation_data.py
# Purpose:
# Transform raw Banxico inflation data from long format to
# wide monthly time series format.
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_PATH = BASE_DIR / "data" / "raw" / "banxico_inflation_series_long.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TABLES_DIR = BASE_DIR / "outputs" / "tables"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RAW_PATH, parse_dates=["date"])

# Keep only the columns needed for analysis.
df = df[["date", "series_name", "value"]].copy()

# Convert from long to wide format.
wide = (
    df.pivot(index="date", columns="series_name", values="value")
    .reset_index()
    .sort_values("date")
)

wide.columns.name = None

# Ensure monthly frequency and check missing values.
wide = wide.set_index("date").asfreq("MS").reset_index()

# Rename columns to shorter analytical names.
wide = wide.rename(
    columns={
        "headline_inflation_annual": "headline",
        "core_inflation_annual": "core",
        "non_core_inflation_annual": "non_core",
    }
)

# Add simple derived variables.
wide["headline_change"] = wide["headline"].diff()
wide["core_change"] = wide["core"].diff()
wide["non_core_change"] = wide["non_core"].diff()

wide["headline_ma_3"] = wide["headline"].rolling(window=3).mean()
wide["headline_ma_12"] = wide["headline"].rolling(window=12).mean()

# Save processed dataset.
processed_path = PROCESSED_DIR / "inflation_monthly_processed.csv"
wide.to_csv(processed_path, index=False, encoding="utf-8-sig")

# Create a small summary table.
summary = pd.DataFrame(
    {
        "variable": ["headline", "core", "non_core"],
        "observations": [
            wide["headline"].notna().sum(),
            wide["core"].notna().sum(),
            wide["non_core"].notna().sum(),
        ],
        "start_date": [
            wide.loc[wide["headline"].notna(), "date"].min(),
            wide.loc[wide["core"].notna(), "date"].min(),
            wide.loc[wide["non_core"].notna(), "date"].min(),
        ],
        "end_date": [
            wide.loc[wide["headline"].notna(), "date"].max(),
            wide.loc[wide["core"].notna(), "date"].max(),
            wide.loc[wide["non_core"].notna(), "date"].max(),
        ],
        "mean": [
            wide["headline"].mean(),
            wide["core"].mean(),
            wide["non_core"].mean(),
        ],
        "std": [
            wide["headline"].std(),
            wide["core"].std(),
            wide["non_core"].std(),
        ],
        "min": [
            wide["headline"].min(),
            wide["core"].min(),
            wide["non_core"].min(),
        ],
        "max": [
            wide["headline"].max(),
            wide["core"].max(),
            wide["non_core"].max(),
        ],
    }
)

summary_path = TABLES_DIR / "inflation_series_summary.csv"
summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

print("Inflation data prepared successfully.")
print(f"Processed dataset saved to: {processed_path}")
print(f"Summary table saved to: {summary_path}")
print(f"Rows: {wide.shape[0]}")
print(f"Columns: {wide.shape[1]}")
print("\nColumns:")
print(list(wide.columns))
print("\nMissing values:")
print(wide.isna().sum())
print("\nFirst rows:")
print(wide.head().to_string(index=False))
print("\nLast rows:")
print(wide.tail().to_string(index=False))