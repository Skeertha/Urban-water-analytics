
import json
import sqlite3
import unittest
from pathlib import Path

import pandas as pd

# Find the project root from this test file.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

SUMMARY_FILE = PROCESSED_DIR / "citywide_etl_summary.csv"
REPORT_FILE = PROCESSED_DIR / "etl_quality_report.json"
DATABASE_FILE = DATA_DIR / "urban_water_analytics.sqlite"


class TestETLPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        for file_path in (SUMMARY_FILE, REPORT_FILE, DATABASE_FILE):
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Missing output: {file_path}. "
                    "Run python/05_etl_quality_pipeline.py first."
                )

        cls.summary = pd.read_csv(SUMMARY_FILE)
        with open(REPORT_FILE, encoding="utf-8") as file:
            cls.report = json.load(file)

    def test_daily_summary_has_rows(self):
        self.assertGreater(len(self.summary), 0)

    def test_daily_summary_has_no_duplicate_dates(self):
        self.assertEqual(
            self.summary["date"].duplicated().sum(), 0
        )

    def test_required_columns_exist(self):
        required = {
            "date",
            "total_production_liters",
            "total_billed_liters",
            "nrw_liters",
            "nrw_pct",
        }
        self.assertTrue(required.issubset(self.summary.columns))

    def test_nrw_liters_calculation(self):
        expected = (
            self.summary["total_production_liters"]
            - self.summary["total_billed_liters"]
        )
        difference = (self.summary["nrw_liters"] - expected).abs()
        self.assertTrue((difference < 0.01).all())

    def test_quality_report_has_no_missing_cells(self):
        # Matches the JSON structure produced by the pipeline.
        tables = self.report.get("tables", self.report)

        if isinstance(tables, dict):
            entries = tables.values()
        elif isinstance(tables, list):
            entries = tables
        else:
            self.fail("Unexpected quality-report structure.")

        for entry in entries:
            if isinstance(entry, dict):
                missing = entry.get(
                    "missing_cells",
                    entry.get("missing_values", 0)
                )
                self.assertEqual(
                    missing, 0,
                    f"Missing values found in report entry: {entry}"
                )

    def test_database_contains_daily_summary(self):
        with sqlite3.connect(DATABASE_FILE) as connection:
            result = connection.execute(
                "SELECT COUNT(*) FROM citywide_etl_summary"
            ).fetchone()[0]

        self.assertEqual(result, len(self.summary))


if __name__ == "__main__":
    unittest.main(verbosity=2)
import json
import sqlite3
import unittest
from pathlib import Path

import pandas as pd