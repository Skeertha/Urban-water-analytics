
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from . import test_data_quality_pipeline as base

pipeline = base.pipeline


class TestDataQualityEdgeCases(unittest.TestCase):

    def setUp(self):
        pipeline.issues = []
        pipeline.summary = []
        pipeline.dataframes = {}

    def test_missing_file_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_dir = pipeline.RAW_DIR
            original_datasets = pipeline.DATASETS

            try:
                pipeline.RAW_DIR = Path(temp_dir)
                pipeline.DATASETS = {
                    "zones": original_datasets["zones"]
                }

                pipeline.load_datasets()

                self.assertTrue(any(
                    issue["issue_type"] == "MISSING_FILE"
                    for issue in pipeline.issues
                ))
            finally:
                pipeline.RAW_DIR = original_dir
                pipeline.DATASETS = original_datasets

    def test_missing_column_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            pd.DataFrame({
                "zone_id": ["Z01"]
            }).to_csv(temp_path / "zones.csv", index=False)

            original_dir = pipeline.RAW_DIR
            original_datasets = pipeline.DATASETS

            try:
                pipeline.RAW_DIR = temp_path
                pipeline.DATASETS = {
                    "zones": original_datasets["zones"]
                }

                pipeline.load_datasets()

                self.assertTrue(any(
                    issue["issue_type"] == "MISSING_COLUMN"
                    for issue in pipeline.issues
                ))
            finally:
                pipeline.RAW_DIR = original_dir
                pipeline.DATASETS = original_datasets

    def test_blank_value_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            pd.DataFrame({
                "zone_id": ["Z01"],
                "zone_name": ["North"],
                "zone_type": ["Residential"],
                "population": [1000],
                "num_households": [None],
                "area_sq_km": [2.5]
            }).to_csv(temp_path / "zones.csv", index=False)

            original_dir = pipeline.RAW_DIR
            original_datasets = pipeline.DATASETS

            try:
                pipeline.RAW_DIR = temp_path
                pipeline.DATASETS = {
                    "zones": original_datasets["zones"]
                }

                pipeline.load_datasets()

                self.assertTrue(any(
                    issue["issue_type"] == "MISSING_VALUE"
                    and issue["column"] == "num_households"
                    for issue in pipeline.issues
                ))
            finally:
                pipeline.RAW_DIR = original_dir
                pipeline.DATASETS = original_datasets

    def test_invalid_numeric_detection(self):
        pipeline.dataframes["weather_daily"] = pd.DataFrame({
            "humidity_pct": ["invalid"]
        })

        pipeline.check_numeric(
            "weather_daily",
            "humidity_pct",
            minimum=0,
            maximum=100
        )

        self.assertTrue(any(
            issue["issue_type"] == "INVALID_NUMBER"
            for issue in pipeline.issues
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
