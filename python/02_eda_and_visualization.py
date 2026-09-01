"""
02_eda_and_visualization.py
----------------------------
Exploratory data analysis for the Urban Water Supply Intelligence project.
Loads the CSVs from data/raw, computes key KPIs (mirroring sql/02_analysis_queries.sql)
and saves chart images to outputs/figures/ for use in the README / Power BI storytelling.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid")

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
FIG = BASE / "outputs" / "figures"
PROC = BASE / "data" / "processed"
FIG.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)


def load_data():
    zones = pd.read_csv(RAW / "zones.csv")
    consumption = pd.read_csv(RAW / "consumption_daily.csv", parse_dates=["date"])
    weather = pd.read_csv(RAW / "weather_daily.csv", parse_dates=["date"])
    leaks = pd.read_csv(RAW / "leakage_incidents.csv", parse_dates=["reported_date", "resolved_date"])
    billing = pd.read_csv(RAW / "billing_monthly.csv", parse_dates=["billing_month"])
    return zones, consumption, weather, leaks, billing


def citywide_trend(consumption):
    daily = consumption.groupby("date")[["billed_consumption_liters", "production_volume_liters"]].sum()
    daily["nrw_pct"] = (daily["production_volume_liters"] - daily["billed_consumption_liters"]) \
        / daily["production_volume_liters"] * 100
    daily_ml = daily / [1_000_000, 1_000_000, 1]  # convert liters -> ML, keep pct as is
    daily_ml.columns = ["billed_ML", "production_ML", "nrw_pct"]

    fig, ax1 = plt.subplots(figsize=(12, 5))
    daily_ml["billed_ML"].rolling(14).mean().plot(ax=ax1, label="Billed (14d avg, ML)", color="#1f77b4")
    daily_ml["production_ML"].rolling(14).mean().plot(ax=ax1, label="Production (14d avg, ML)", color="#ff7f0e")
    ax1.set_ylabel("Megaliters / day")
    ax1.set_title("City-wide Water Production vs. Billed Consumption (14-day rolling avg)")
    ax1.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(FIG / "citywide_production_vs_billed.png", dpi=150)
    plt.close()

    daily_ml.to_csv(PROC / "citywide_daily_summary.csv")
    return daily_ml


def per_capita_by_zone(consumption, zones):
    m = consumption.merge(zones[["zone_id", "zone_name", "zone_type"]], on="zone_id")
    m["per_capita_lpd"] = m["billed_consumption_liters"] / m["population_est"]
    monthly = (m.set_index("date").groupby(["zone_name"])["per_capita_lpd"]
               .resample("MS").mean().reset_index())

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=monthly, x="date", y="per_capita_lpd", hue="zone_name")
    plt.title("Average Per-Capita Daily Consumption by Zone (monthly)")
    plt.ylabel("Liters / person / day")
    plt.xlabel("")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG / "per_capita_by_zone.png", dpi=150)
    plt.close()


def seasonality_heatmap(consumption):
    df = consumption.copy()
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    pivot = (df.groupby(["year", "month"])["billed_consumption_liters"]
             .sum().div(1_000_000).unstack(level=0))

    plt.figure(figsize=(8, 6))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlGnBu", cbar_kws={"label": "Billed ML"})
    plt.title("Monthly City-wide Billed Consumption (ML) by Year")
    plt.ylabel("Month")
    plt.xlabel("Year")
    plt.tight_layout()
    plt.savefig(FIG / "seasonality_heatmap.png", dpi=150)
    plt.close()


def weather_correlation(consumption, weather):
    merged = consumption.merge(weather, on=["zone_id", "date"])
    corr = merged[["billed_consumption_liters", "temp_c", "rainfall_mm", "humidity_pct"]].corr()

    plt.figure(figsize=(5, 4))
    sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
    plt.title("Consumption vs. Weather Correlation")
    plt.tight_layout()
    plt.savefig(FIG / "weather_correlation.png", dpi=150)
    plt.close()

    print("\nCorrelation of billed consumption with weather variables:")
    print(corr["billed_consumption_liters"].drop("billed_consumption_liters"))


def leakage_summary(leaks, zones):
    m = leaks.merge(zones[["zone_id", "zone_name"]], on="zone_id")
    summary = (m.groupby("zone_name")
               .agg(incidents=("incident_id", "count"),
                    liters_lost=("estimated_volume_lost_liters", "sum"))
               .sort_values("liters_lost", ascending=False))
    summary["ML_lost"] = summary["liters_lost"] / 1_000_000

    plt.figure(figsize=(9, 5))
    sns.barplot(x=summary.index, y="ML_lost", data=summary, color="#d62728")
    plt.xticks(rotation=40, ha="right")
    plt.ylabel("Estimated Megaliters Lost")
    plt.title("Estimated Water Lost to Leakage Incidents by Zone")
    plt.tight_layout()
    plt.savefig(FIG / "leakage_by_zone.png", dpi=150)
    plt.close()

    summary.to_csv(PROC / "leakage_summary_by_zone.csv")
    print("\nLeakage summary by zone:\n", summary)


def revenue_risk(billing, zones):
    m = billing.merge(zones[["zone_id", "zone_name"]], on="zone_id")
    summary = (m.groupby("zone_name")
               .agg(avg_collection_rate=("collection_rate", "mean"),
                    revenue_expected=("revenue_expected", "sum"),
                    revenue_collected=("revenue_collected", "sum"))
               .assign(revenue_at_risk=lambda d: d.revenue_expected - d.revenue_collected)
               .sort_values("revenue_at_risk", ascending=False))

    plt.figure(figsize=(9, 5))
    sns.barplot(x=summary.index, y="revenue_at_risk", data=summary, color="#9467bd")
    plt.xticks(rotation=40, ha="right")
    plt.ylabel("Revenue at Risk (currency units)")
    plt.title("Revenue at Risk from Under-Collection by Zone")
    plt.tight_layout()
    plt.savefig(FIG / "revenue_at_risk.png", dpi=150)
    plt.close()

    summary.to_csv(PROC / "revenue_risk_by_zone.csv")


def main():
    zones, consumption, weather, leaks, billing = load_data()
    citywide_trend(consumption)
    per_capita_by_zone(consumption, zones)
    seasonality_heatmap(consumption)
    weather_correlation(consumption, weather)
    leakage_summary(leaks, zones)
    revenue_risk(billing, zones)
    print(f"\nAll figures saved to: {FIG}")
    print(f"Processed summary tables saved to: {PROC}")


if __name__ == "__main__":
    main()
