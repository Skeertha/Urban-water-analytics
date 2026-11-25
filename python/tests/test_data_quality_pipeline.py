import importlib.util
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "05_data_quality_pipeline.py"
)

spec = importlib.util.spec_from_file_location(
    "data_quality_pipeline", SCRIPT_PATH
)
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class TestDataQualityPipeline(unittest.TestCase):

    def setUp(self):
        pipeline.issues = []
        pipeline.summary = []
        pipeline.dataframes = {}

    def test_numeric_range_validation(self):
        pipeline.dataframes["weather_daily"] = pd.DataFrame({
            "humidity_pct": [50, 120]
        })

        pipeline.check_numeric(
            "weather_daily",
            "humidity_pct",
            minimum=0,
            maximum=100
        )

        self.assertEqual(len(pipeline.issues), 1)
        self.assertEqual(
            pipeline.issues[0]["issue_type"],
            "INVALID_RANGE"
        )

    def test_foreign_key_validation(self):
        pipeline.dataframes["zones"] = pd.DataFrame({
            "zone_id": ["Z01"]
        })
        pipeline.dataframes["pipe_network"] = pd.DataFrame({
            "pipe_id": ["P01"],
            "zone_id": ["Z99"]
        })

        pipeline.validate_foreign_keys()

        self.assertTrue(any(
            issue["issue_type"] == "FOREIGN_KEY_ERROR"
            for issue in pipeline.issues
        ))

    def test_invalid_date_order(self):
        pipeline.dataframes["leakage_incidents"] = pd.DataFrame({
            "reported_date": ["2023-05-10"],
            "resolved_date": ["2023-05-05"]
        })

        pipeline.validate_dates()

        self.assertTrue(any(
            issue["issue_type"] == "DATE_ORDER_ERROR"
            for issue in pipeline.issues
        ))

    def test_business_rule_validation(self):
        pipeline.dataframes["consumption_daily"] = pd.DataFrame({
            "billed_consumption_liters": [120],
            "production_volume_liters": [100]
        })
        pipeline.dataframes["leakage_incidents"] = pd.DataFrame({
            "severity": ["Critical"]
        })

        pipeline.validate_business_rules()

        issue_types = {
            issue["issue_type"]
            for issue in pipeline.issues
        }

        self.assertIn("BUSINESS_RULE_ERROR", issue_types)
        self.assertIn("INVALID_CATEGORY", issue_types)

    def test_duplicate_business_key_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            pd.DataFrame({
                "zone_id": ["Z01", "Z01"],
                "zone_name": ["North", "North"],
                "zone_type": ["Residential", "Residential"],
                "population": [1000, 1000],
                "num_households": [300, 300],
                "area_sq_km": [2.5, 2.5]
            }).to_csv(temp_path / "zones.csv", index=False)

            original_raw_dir = pipeline.RAW_DIR
            original_datasets = pipeline.DATASETS

            try:
                pipeline.RAW_DIR = temp_path
                pipeline.DATASETS = {
                    "zones": original_datasets["zones"]
                }

                pipeline.load_datasets()

                self.assertEqual(
                    sum(
                        issue["issue_type"] == "DUPLICATE_KEY"
                        for issue in pipeline.issues
                    ),
                    2
                )
            finally:
                pipeline.RAW_DIR = original_raw_dir
                pipeline.DATASETS = original_datasets


if __name__ == "__main__":
    unittest.main(verbosity=2)
