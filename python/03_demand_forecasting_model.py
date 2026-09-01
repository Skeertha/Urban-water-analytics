"""
03_demand_forecasting_model.py
--------------------------------
Predicts daily city-wide billed water demand using a Gradient Boosting
regressor trained on calendar, weather, and lag features. This keeps
the dependency footprint light (scikit-learn only) while still capturing
seasonality, weekly patterns, and weather sensitivity.

Outputs:
    outputs/figures/forecast_vs_actual.png
    outputs/figures/feature_importance.png
    data/processed/demand_forecast_test_predictions.csv
    Console: MAE / RMSE / MAPE on a held-out test period
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
FIG = BASE / "outputs" / "figures"
PROC = BASE / "data" / "processed"


def build_features():
    consumption = pd.read_csv(RAW / "consumption_daily.csv", parse_dates=["date"])
    weather = pd.read_csv(RAW / "weather_daily.csv", parse_dates=["date"])

    city = (consumption.groupby("date")
            .agg(billed_liters=("billed_consumption_liters", "sum"))
            .reset_index())
    w_city = (weather.groupby("date")
              .agg(temp_c=("temp_c", "mean"),
                   rainfall_mm=("rainfall_mm", "sum"),
                   humidity_pct=("humidity_pct", "mean"))
              .reset_index())

    df = city.merge(w_city, on="date").sort_values("date").reset_index(drop=True)
    df["billed_ML"] = df["billed_liters"] / 1_000_000

    # calendar features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_year"] = df["date"].dt.dayofyear
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["year"] = df["date"].dt.year

    # cyclical encodings so the model understands seasonality wraps around
    df["doy_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    # lag / rolling features (yesterday, last week, trailing 7-day avg)
    df["lag_1"] = df["billed_ML"].shift(1)
    df["lag_7"] = df["billed_ML"].shift(7)
    df["roll_mean_7"] = df["billed_ML"].shift(1).rolling(7).mean()
    df["roll_mean_30"] = df["billed_ML"].shift(1).rolling(30).mean()

    df = df.dropna().reset_index(drop=True)
    return df


FEATURES = [
    "temp_c", "rainfall_mm", "humidity_pct",
    "is_weekend", "month", "year",
    "doy_sin", "doy_cos", "dow_sin", "dow_cos",
    "lag_1", "lag_7", "roll_mean_7", "roll_mean_30",
]
TARGET = "billed_ML"


def train_test_split_by_date(df, test_days=90):
    cutoff = df["date"].max() - pd.Timedelta(days=test_days)
    train = df[df["date"] <= cutoff]
    test = df[df["date"] > cutoff]
    return train, test


def evaluate(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    return mae, rmse, mape


def main():
    df = build_features()
    train, test = train_test_split_by_date(df, test_days=90)

    model = GradientBoostingRegressor(
        n_estimators=400,
        max_depth=3,
        learning_rate=0.03,
        subsample=0.8,
        random_state=42,
    )
    model.fit(train[FEATURES], train[TARGET])

    preds = model.predict(test[FEATURES])
    mae, rmse, mape = evaluate(test[TARGET].values, preds)

    print("Held-out test period:", test["date"].min().date(), "to", test["date"].max().date())
    print(f"MAE:  {mae:.2f} ML/day")
    print(f"RMSE: {rmse:.2f} ML/day")
    print(f"MAPE: {mape:.2f}%")

    # Save predictions
    out = test[["date", TARGET]].copy()
    out["predicted_ML"] = preds
    out.to_csv(PROC / "demand_forecast_test_predictions.csv", index=False)

    # Plot actual vs predicted
    plt.figure(figsize=(12, 5))
    plt.plot(train["date"].tail(60), train[TARGET].tail(60), label="Train (last 60d)", color="grey", alpha=0.6)
    plt.plot(out["date"], out[TARGET], label="Actual", color="#1f77b4")
    plt.plot(out["date"], out["predicted_ML"], label="Predicted", color="#ff7f0e", linestyle="--")
    plt.title(f"Demand Forecast vs. Actual (MAPE {mape:.1f}%)")
    plt.ylabel("Billed Megaliters / day")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG / "forecast_vs_actual.png", dpi=150)
    plt.close()

    # Feature importance
    importance = pd.Series(model.feature_importances_, index=FEATURES).sort_values()
    plt.figure(figsize=(8, 6))
    importance.plot(kind="barh", color="#2ca02c")
    plt.title("Feature Importance — Demand Forecasting Model")
    plt.tight_layout()
    plt.savefig(FIG / "feature_importance.png", dpi=150)
    plt.close()

    print(f"\nArtifacts saved to: {FIG} and {PROC}")


if __name__ == "__main__":
    main()
