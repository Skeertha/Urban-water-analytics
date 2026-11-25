
from pathlib import Path
import json
import pandas as pd


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# DATASET CONFIGURATION
# --------------------------------------------------

DATASETS = {
    "zones": {
        "file": "zones.csv",
        "columns": [
            "zone_id", "zone_name", "zone_type",
            "population", "num_households", "area_sq_km"
        ],
        "keys": ["zone_id"],
    },
    "reservoirs": {
        "file": "reservoirs.csv",
        "columns": [
            "reservoir_id", "zone_id", "reservoir_name",
            "capacity_ml", "commissioned_year"
        ],
        "keys": ["reservoir_id"],
    },
    "pipe_network": {
        "file": "pipe_network.csv",
        "columns": [
            "pipe_id", "zone_id", "length_km",
            "diameter_mm", "material", "install_year",
            "avg_pressure_bar"
        ],
        "keys": ["pipe_id"],
    },
    "weather_daily": {
        "file": "weather_daily.csv",
        "columns": [
            "date", "zone_id", "temp_c",
            "rainfall_mm", "humidity_pct"
        ],
        "keys": ["date", "zone_id"],
    },
    "consumption_daily": {
        "file": "consumption_daily.csv",
        "columns": [
            "date", "zone_id", "population_est",
            "billed_consumption_liters",
            "production_volume_liters",
            "avg_pressure_bar"
        ],
        "keys": ["date", "zone_id"],
    },
    "leakage_incidents": {
        "file": "leakage_incidents.csv",
        "columns": [
            "incident_id", "zone_id", "pipe_id",
            "reported_date", "resolved_date",
            "severity", "estimated_volume_lost_liters"
        ],
        "keys": ["incident_id"],
    },
    "billing_monthly": {
        "file": "billing_monthly.csv",
        "columns": [
            "zone_id", "billing_month",
            "billed_kilo_liters", "revenue_expected",
            "collection_rate", "revenue_collected"
        ],
        "keys": ["zone_id", "billing_month"],
    },
}


# --------------------------------------------------
# REPORT STORAGE
# --------------------------------------------------

issues = []
summary = []
dataframes = {}


def add_issue(dataset, row_number, column, issue_type, details):
    issues.append({
        "dataset": dataset,
        "row_number": row_number,
        "column": column,
        "issue_type": issue_type,
        "details": details,
    })


# --------------------------------------------------
# LOAD AND STRUCTURAL VALIDATION
# --------------------------------------------------

def load_datasets():

    for dataset, config in DATASETS.items():

        path = RAW_DIR / config["file"]

        if not path.exists():
            add_issue(
                dataset, None, None,
                "MISSING_FILE", f"File not found: {path.name}"
            )
            continue

        try:
            df = pd.read_csv(path)
        except Exception as error:
            add_issue(
                dataset, None, None,
                "READ_ERROR", str(error)
            )
            continue

        dataframes[dataset] = df

        for column in config["columns"]:
            if column not in df.columns:
                add_issue(
                    dataset, None, column,
                    "MISSING_COLUMN",
                    f"Required column '{column}' is absent"
                )

        missing_columns = [
            column for column in config["columns"]
            if column not in df.columns
        ]

        if missing_columns:
            continue

        for column in config["columns"]:
            blank_rows = df.index[
                df[column].isna()
                | df[column].astype(str).str.strip().eq("")
            ]

            for index in blank_rows:
                add_issue(
                    dataset, int(index) + 2, column,
                    "MISSING_VALUE",
                    "Required value is blank"
                )

        key_columns = config["keys"]

        duplicate_mask = df.duplicated(
            subset=key_columns, keep=False
        )

        for index in df.index[duplicate_mask]:
            add_issue(
                dataset, int(index) + 2,
                ",".join(key_columns),
                "DUPLICATE_KEY",
                "Duplicate business key"
            )


# --------------------------------------------------
# NUMERIC VALIDATION
# --------------------------------------------------

def check_numeric(dataset, column, minimum=None,
                  maximum=None, strictly_positive=False):

    if dataset not in dataframes:
        return

    df = dataframes[dataset]

    if column not in df.columns:
        return

    values = pd.to_numeric(df[column], errors="coerce")

    for index, value in values.items():

        if pd.isna(value):
            if pd.notna(df.loc[index, column]):
                add_issue(
                    dataset, int(index) + 2, column,
                    "INVALID_NUMBER",
                    f"Cannot convert '{df.loc[index, column]}' to a number"
                )
            continue

        invalid = False
        reason = ""

        if strictly_positive and value <= 0:
            invalid = True
            reason = "Value must be greater than zero"

        elif minimum is not None and value < minimum:
            invalid = True
            reason = f"Value must be at least {minimum}"

        elif maximum is not None and value > maximum:
            invalid = True
            reason = f"Value must not exceed {maximum}"

        if invalid:
            add_issue(
                dataset, int(index) + 2, column,
                "INVALID_RANGE", reason
            )


def validate_numeric_rules():

    positive_rules = {
        "zones": [
            "population", "num_households", "area_sq_km"
        ],
        "reservoirs": ["capacity_ml"],
        "pipe_network": [
            "length_km", "diameter_mm", "avg_pressure_bar"
        ],
        "consumption_daily": [
            "population_est", "avg_pressure_bar"
        ],
    }

    for dataset, columns in positive_rules.items():
        for column in columns:
            check_numeric(
                dataset, column, strictly_positive=True
            )

    check_numeric("weather_daily", "rainfall_mm", minimum=0)
    check_numeric("weather_daily", "humidity_pct", minimum=0, maximum=100)
    check_numeric("weather_daily", "temp_c", minimum=-30, maximum=60)

    check_numeric(
        "consumption_daily",
        "billed_consumption_liters",
        minimum=0
    )
    check_numeric(
        "consumption_daily",
        "production_volume_liters",
        minimum=0
    )

    check_numeric(
        "leakage_incidents",
        "estimated_volume_lost_liters",
        minimum=0
    )

    check_numeric(
        "billing_monthly",
        "billed_kilo_liters",
        minimum=0
    )
    check_numeric(
        "billing_monthly",
        "revenue_expected",
        minimum=0
    )
    check_numeric(
        "billing_monthly",
        "revenue_collected",
        minimum=0
    )
    check_numeric(
        "billing_monthly",
        "collection_rate",
        minimum=0,
        maximum=1
    )


# --------------------------------------------------
# CROSS-DATASET VALIDATION
# --------------------------------------------------

def validate_foreign_keys():

    relationships = [
        ("reservoirs", "zone_id", "zones", "zone_id"),
        ("pipe_network", "zone_id", "zones", "zone_id"),
        ("weather_daily", "zone_id", "zones", "zone_id"),
        ("consumption_daily", "zone_id", "zones", "zone_id"),
        ("leakage_incidents", "zone_id", "zones", "zone_id"),
        ("leakage_incidents", "pipe_id", "pipe_network", "pipe_id"),
        ("billing_monthly", "zone_id", "zones", "zone_id"),
    ]

    for child, child_col, parent, parent_col in relationships:

        if child not in dataframes or parent not in dataframes:
            continue

        child_df = dataframes[child]
        parent_df = dataframes[parent]

        if child_col not in child_df.columns:
            continue

        if parent_col not in parent_df.columns:
            continue

        parent_values = set(
            parent_df[parent_col].dropna().astype(str)
        )

        for index, value in child_df[child_col].items():

            if pd.isna(value):
                continue

            if str(value) not in parent_values:
                add_issue(
                    child, int(index) + 2, child_col,
                    "FOREIGN_KEY_ERROR",
                    f"Value '{value}' not found in {parent}.{parent_col}"
                )


# --------------------------------------------------
# DATE AND BUSINESS RULE VALIDATION
# --------------------------------------------------

def validate_dates():

    date_rules = {
        "weather_daily": ["date"],
        "consumption_daily": ["date"],
        "leakage_incidents": [
            "reported_date", "resolved_date"
        ],
        "billing_monthly": ["billing_month"],
    }

    for dataset, columns in date_rules.items():

        if dataset not in dataframes:
            continue

        df = dataframes[dataset]

        for column in columns:

            if column not in df.columns:
                continue

            parsed = pd.to_datetime(
                df[column], errors="coerce"
            )

            for index in df.index[parsed.isna()]:
                add_issue(
                    dataset, int(index) + 2, column,
                    "INVALID_DATE",
                    f"Invalid date: {df.loc[index, column]}"
                )

    if "leakage_incidents" in dataframes:

        df = dataframes["leakage_incidents"]

        if {"reported_date", "resolved_date"}.issubset(df.columns):

            reported = pd.to_datetime(
                df["reported_date"], errors="coerce"
            )
            resolved = pd.to_datetime(
                df["resolved_date"], errors="coerce"
            )

            invalid = (
                reported.notna()
                & resolved.notna()
                & (resolved < reported)
            )

            for index in df.index[invalid]:
                add_issue(
                    "leakage_incidents", int(index) + 2,
                    "resolved_date",
                    "DATE_ORDER_ERROR",
                    "Resolved date is earlier than reported date"
                )


# --------------------------------------------------
# ADDITIONAL BUSINESS RULES
# --------------------------------------------------

def validate_business_rules():

    if "consumption_daily" in dataframes:

        df = dataframes["consumption_daily"]

        billed = pd.to_numeric(
            df["billed_consumption_liters"], errors="coerce"
        )
        production = pd.to_numeric(
            df["production_volume_liters"], errors="coerce"
        )

        invalid = (
            billed.notna()
            & production.notna()
            & (production < billed)
        )

        for index in df.index[invalid]:
            add_issue(
                "consumption_daily", int(index) + 2,
                "production_volume_liters",
                "BUSINESS_RULE_ERROR",
                "Production volume is lower than billed consumption"
            )

    if "leakage_incidents" in dataframes:

        df = dataframes["leakage_incidents"]

        if "severity" in df.columns:

            allowed = {"Low", "Medium", "High"}

            for index, value in df["severity"].items():

                if pd.notna(value) and str(value).strip() not in allowed:
                    add_issue(
                        "leakage_incidents", int(index) + 2,
                        "severity",
                        "INVALID_CATEGORY",
                        f"Unexpected severity: {value}"
                    )


# --------------------------------------------------
# GENERATE REPORTS
# --------------------------------------------------

def generate_reports():

    issue_df = pd.DataFrame(
        issues,
        columns=[
            "dataset", "row_number", "column",
            "issue_type", "details"
        ]
    )

    issue_path = OUTPUT_DIR / "data_quality_issues.csv"
    issue_df.to_csv(issue_path, index=False)

    total_rows = 0

    for dataset, config in DATASETS.items():

        df = dataframes.get(dataset)

        if df is None:
            row_count = 0
            dataset_issues = sum(
                issue["dataset"] == dataset for issue in issues
            )
            missing_count = 0
            duplicate_count = 0

        else:
            row_count = len(df)
            total_rows += row_count

            dataset_issues = sum(
                issue["dataset"] == dataset for issue in issues
            )

            missing_count = sum(
                issue["dataset"] == dataset
                and issue["issue_type"] == "MISSING_VALUE"
                for issue in issues
            )

            duplicate_count = sum(
                issue["dataset"] == dataset
                and issue["issue_type"] == "DUPLICATE_KEY"
                for issue in issues
            )

        summary.append({
            "dataset": dataset,
            "rows": row_count,
            "missing_values": missing_count,
            "duplicate_key_rows": duplicate_count,
            "total_issues": dataset_issues,
            "status": "PASS" if dataset_issues == 0 else "FAIL",
        })

    report = {
        "project": "Urban Water Analytics",
        "validation_type": "Raw CSV data quality validation",
        "total_rows": total_rows,
        "total_issues": len(issues),
        "overall_status": "PASS" if not issues else "FAIL",
        "datasets": summary,
    }

    report_path = OUTPUT_DIR / "etl_quality_report.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n===== ETL DATA QUALITY REPORT =====")
    print(pd.DataFrame(summary).to_string(index=False))
    print(f"\nTotal rows checked: {total_rows}")
    print(f"Total issues found: {len(issues)}")
    print(f"Overall status: {report['overall_status']}")
    print(f"\nJSON report: {report_path}")
    print(f"CSV issues: {issue_path}")


# --------------------------------------------------
# MAIN EXECUTION
# --------------------------------------------------

def main():

    load_datasets()
    validate_numeric_rules()
    validate_foreign_keys()
    validate_dates()
    validate_business_rules()
    generate_reports()


if __name__ == "__main__":
    main()
