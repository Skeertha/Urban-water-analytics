"""Plot the saved NRW forecasting test predictions.

Run from the project root:
    python python/07_plot_nrw_forecast.py

Expected input: results/nrw_forecast_predictions.csv
Output: results/nrw_forecast_comparison.png
"""
from pathlib import Path
import sys

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Matplotlib is missing. Install it with: python -m pip install matplotlib")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "results" / "nrw_forecast_predictions.csv"
OUTPUT = ROOT / "results" / "nrw_forecast_comparison.png"

if not INPUT.exists():
    sys.exit(
        f"Cannot find {INPUT}. Run python python/06_nrw_forecasting.py first, "
        "then run this script again."
    )

df = pd.read_csv(INPUT, parse_dates=["date"])
required = [
    "date",
    "actual_nrw_pct",
    "previous_day_baseline_prediction",
    "linear_regression_prediction",
    "random_forest_prediction",
]
missing = [column for column in required if column not in df.columns]
if missing:
    sys.exit(f"Missing expected columns in {INPUT.name}: {', '.join(missing)}")

fig, ax = plt.subplots(figsize=(13, 6))
ax.plot(df["date"], df["actual_nrw_pct"], label="Actual NRW", linewidth=2.0)
ax.plot(
    df["date"], df["previous_day_baseline_prediction"],
    label="Previous-day baseline", linewidth=1.3, alpha=0.85
)
ax.plot(
    df["date"], df["linear_regression_prediction"],
    label="Linear Regression", linewidth=1.3, alpha=0.85
)
ax.plot(
    df["date"], df["random_forest_prediction"],
    label="Random Forest", linewidth=1.3, alpha=0.85
)
ax.set_title("Daily NRW Forecast Comparison — Holdout Test Period")
ax.set_xlabel("Date")
ax.set_ylabel("NRW (%)")
ax.grid(True, alpha=0.25)
ax.legend()
fig.tight_layout()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT, dpi=180, bbox_inches="tight")
plt.close(fig)
print(f"Chart saved to: {OUTPUT}")
