"""
04_leak_anomaly_detection.py
------------------------------
Flags likely leak/burst days per zone by detecting anomalous gaps between
production and billed consumption (i.e., spikes in Non-Revenue Water)
using an Isolation Forest. Cross-checks flagged days against the known
leakage_incidents.csv to sanity-check detection quality.

Outputs:
    outputs/figures/anomaly_example_zone.png
    data/processed/leak_anomaly_flags.csv
    Console: detection precision/recall vs. logged incidents
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.ensemble import IsolationForest

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
FIG = BASE / "outputs" / "figures"
PROC = BASE / "data" / "processed"


def load():
    consumption = pd.read_csv(RAW / "consumption_daily.csv", parse_dates=["date"])
    leaks = pd.read_csv(RAW / "leakage_incidents.csv", parse_dates=["reported_date", "resolved_date"])
    zones = pd.read_csv(RAW / "zones.csv")
    return consumption, leaks, zones


def engineer_nrw_features(consumption):
    df = consumption.copy()
    df["nrw_liters"] = df["production_volume_liters"] - df["billed_consumption_liters"]
    df["nrw_pct"] = df["nrw_liters"] / df["production_volume_liters"] * 100

    # zone-level rolling baseline so the model judges each zone against
    # its own normal behaviour rather than a citywide average
    df = df.sort_values(["zone_id", "date"])
    df["nrw_pct_roll_mean_30"] = (df.groupby("zone_id")["nrw_pct"]
                                   .transform(lambda s: s.shift(1).rolling(30, min_periods=10).mean()))
    df["nrw_pct_deviation"] = df["nrw_pct"] - df["nrw_pct_roll_mean_30"]
    df["pressure_zscore"] = (df.groupby("zone_id")["avg_pressure_bar"]
                              .transform(lambda s: (s - s.mean()) / s.std()))
    df = df.dropna().reset_index(drop=True)
    return df


def detect_anomalies(df, contamination=0.03):
    features = ["nrw_pct", "nrw_pct_deviation", "pressure_zscore"]
    flagged_frames = []
    for zone_id, g in df.groupby("zone_id"):
        model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
        g = g.copy()
        g["anomaly_score"] = model.fit_predict(g[features])
        g["is_anomaly"] = g["anomaly_score"] == -1
        flagged_frames.append(g)
    return pd.concat(flagged_frames, ignore_index=True)


def evaluate_against_known_leaks(flagged, leaks):
    # build a set of (zone_id, date) pairs that fall inside a known leak window
    known_days = set()
    for _, r in leaks.iterrows():
        for d in pd.date_range(r["reported_date"], r["resolved_date"]):
            known_days.add((r["zone_id"], d.normalize()))

    flagged = flagged.copy()
    flagged["is_known_leak_day"] = flagged.apply(
        lambda r: (r["zone_id"], r["date"].normalize()) in known_days, axis=1
    )

    tp = ((flagged["is_anomaly"]) & (flagged["is_known_leak_day"])).sum()
    fp = ((flagged["is_anomaly"]) & (~flagged["is_known_leak_day"])).sum()
    fn = ((~flagged["is_anomaly"]) & (flagged["is_known_leak_day"])).sum()

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    print(f"Flagged anomaly days: {flagged['is_anomaly'].sum()} / {len(flagged)}")
    print(f"True positives (overlap w/ known leak windows): {tp}")
    print(f"Precision: {precision:.2%}  Recall: {recall:.2%}  F1: {f1:.2%}")
    return flagged


def plot_example_zone(flagged, zone_id="Z02"):
    g = flagged[flagged["zone_id"] == zone_id].sort_values("date")
    plt.figure(figsize=(12, 5))
    plt.plot(g["date"], g["nrw_pct"], label="NRW %", color="#1f77b4", linewidth=1)
    anomalies = g[g["is_anomaly"]]
    plt.scatter(anomalies["date"], anomalies["nrw_pct"], color="red", label="Flagged anomaly", zorder=5, s=25)
    plt.title(f"Non-Revenue Water % with Detected Anomalies — Zone {zone_id}")
    plt.ylabel("NRW %")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "anomaly_example_zone.png", dpi=150)
    plt.close()


def main():
    consumption, leaks, zones = load()
    df = engineer_nrw_features(consumption)
    flagged = detect_anomalies(df)
    flagged = evaluate_against_known_leaks(flagged, leaks)

    cols = ["date", "zone_id", "nrw_pct", "nrw_pct_deviation", "pressure_zscore",
            "is_anomaly", "is_known_leak_day"]
    flagged[cols].to_csv(PROC / "leak_anomaly_flags.csv", index=False)

    plot_example_zone(flagged, zone_id="Z02")
    print(f"\nSaved flagged anomalies to: {PROC / 'leak_anomaly_flags.csv'}")
    print(f"Saved example chart to: {FIG / 'anomaly_example_zone.png'}")


if __name__ == "__main__":
    main()
