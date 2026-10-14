
from pathlib import Path
import json
import sqlite3

import pandas as pd

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "data" / "urban_water_analytics.sqlite"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Load the original CSV files
files = {
    "consumption_daily": "consumption_daily.csv",
    "weather_daily": "weather_daily.csv",
    "billing_monthly": "billing_monthly.csv",
    "zones": "zones.csv",
    "pipe_network": "pipe_network.csv",
    "leakage_incidents": "leakage_incidents.csv",
    "reservoirs": "reservoirs.csv",
}

tables = {}

for table_name, filename in files.items():
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing source file: {path}")

    tables[table_name] = pd.read_csv(path)
    print(f"Loaded {filename}: {len(tables[table_name])} rows")

# Data-quality report
report = {}

for name, df in tables.items():
    report[name] = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": list(df.columns),
    }

# Check the actual consumption columns before transforming
consumption = tables["consumption_daily"].copy()

required = [
    "date",
    "zone_id",
    "production_volume_liters",
    "billed_consumption_liters",
]

missing_columns = [
    col for col in required if col not in consumption.columns
]

if missing_columns:
    raise ValueError(
        f"Check the consumption CSV column names: {missing_columns}. "
        f"Available columns: {list(consumption.columns)}"
    )

# Validate dates and numeric values
consumption["date"] = pd.to_datetime(
    consumption["date"], errors="coerce"
)

report["consumption_daily"]["invalid_dates"] = int(
    consumption["date"].isna().sum()
)

for col in [
    "production_volume_liters",
    "billed_consumption_liters",
]:
    consumption[col] = pd.to_numeric(
        consumption[col], errors="coerce"
    )

    report["consumption_daily"][f"invalid_{col}"] = int(
        consumption[col].isna().sum()
    )

report["consumption_daily"]["negative_production_rows"] = int(
    (consumption["production_volume_liters"] < 0).sum()
)

report["consumption_daily"]["negative_billed_rows"] = int(
    (consumption["billed_consumption_liters"] < 0).sum()
)

# Transform zone-level records into a daily city-wide summary
valid = consumption.dropna(
    subset=[
        "date",
        "production_volume_liters",
        "billed_consumption_liters",
    ]
).copy()

daily = (
    valid.groupby("date", as_index=False)
    .agg(
        total_production_liters=(
            "production_volume_liters", "sum"
        ),
        total_billed_liters=(
            "billed_consumption_liters", "sum"
        ),
        zones_reporting=("zone_id", "nunique"),
    )
)

daily["nrw_liters"] = (
    daily["total_production_liters"]
    - daily["total_billed_liters"]
)

daily["nrw_pct"] = (
    daily["nrw_liters"]
    / daily["total_production_liters"].where(
        daily["total_production_liters"] != 0
    )
    * 100
)

daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")

# Save transformed output and quality report
summary_path = PROCESSED_DIR / "citywide_etl_summary.csv"
report_path = PROCESSED_DIR / "etl_quality_report.json"

daily.to_csv(summary_path, index=False)

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

# Load original tables and transformed summary into SQLite
with sqlite3.connect(DB_PATH) as conn:
    for name, df in tables.items():
        df.to_sql(name, conn, if_exists="replace", index=False)

    daily.to_sql(
        "citywide_etl_summary",
        conn,
        if_exists="replace",
        index=False,
    )

print("\nETL pipeline completed.")
print(f"Daily summary: {summary_path}")
print(f"Quality report: {report_path}")
print(f"SQLite database: {DB_PATH}")
print(f"Daily summary rows: {len(daily)}")
