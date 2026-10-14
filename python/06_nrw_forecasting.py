
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 1. Load and prepare the daily NRW data
ROOT = Path(__file__).resolve().parent.parent
input_file = ROOT / "data" / "processed" / "citywide_etl_summary.csv"
output_dir = ROOT / "results"
output_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(input_file, parse_dates=["date"])
df = df.sort_values("date").drop_duplicates(subset="date").reset_index(drop=True)

# 2. Create features using historical data only
df["lag_1"] = df["nrw_pct"].shift(1)
df["lag_2"] = df["nrw_pct"].shift(2)
df["lag_3"] = df["nrw_pct"].shift(3)
df["lag_7"] = df["nrw_pct"].shift(7)

df["rolling_mean_7"] = df["nrw_pct"].shift(1).rolling(7).mean()
df["rolling_mean_30"] = df["nrw_pct"].shift(1).rolling(30).mean()

df["day_of_week"] = df["date"].dt.dayofweek
day_of_year = df["date"].dt.dayofyear
df["year_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
df["year_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)

feature_columns = [
    "lag_1", "lag_2", "lag_3", "lag_7",
    "rolling_mean_7", "rolling_mean_30",
    "day_of_week", "year_sin", "year_cos"
]

data = df.dropna(subset=feature_columns + ["nrw_pct"]).copy()

X = data[feature_columns]
y = data["nrw_pct"]

# 3. Split chronologically: earlier dates train, later dates test
split_point = int(len(data) * 0.80)

X_train = X.iloc[:split_point]
X_test = X.iloc[split_point:]
y_train = y.iloc[:split_point]
y_test = y.iloc[split_point:]

test_dates = data["date"].iloc[split_point:]

# 4. Train and compare the models
models = {
    "Previous-day baseline": None,
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
}

predictions = {}
metrics = []

for name, model in models.items():
    if model is None:
        # Predict tomorrow using the previous day's actual NRW
        predicted = X_test["lag_1"].to_numpy()
    else:
        model.fit(X_train, y_train)
        predicted = model.predict(X_test)

    predictions[name] = predicted

    mae = mean_absolute_error(y_test, predicted)
    rmse = np.sqrt(mean_squared_error(y_test, predicted))

    metrics.append({
        "model": name,
        "test_days": len(y_test),
        "MAE_percentage_points": mae,
        "RMSE_percentage_points": rmse
    })

# 5. Save evaluation results and daily predictions
metrics_df = pd.DataFrame(metrics).sort_values(
    "MAE_percentage_points"
)
metrics_df.to_csv(output_dir / "nrw_forecast_metrics.csv", index=False)

prediction_df = pd.DataFrame({
    "date": test_dates.to_numpy(),
    "actual_nrw_pct": y_test.to_numpy()
})

for name, predicted in predictions.items():
    safe_name = name.lower().replace(" ", "_").replace("-", "_")
    prediction_df[safe_name + "_prediction"] = predicted

prediction_df.to_csv(
    output_dir / "nrw_forecast_predictions.csv",
    index=False
)

# 6. Display the results
print("DAILY NRW FORECAST MODEL COMPARISON")
print("-----------------------------------")
print("Total daily records:", len(df))
print("Training days:", len(X_train))
print("Testing days:", len(X_test))
print("Test period:", test_dates.min().date(), "to", test_dates.max().date())
print("\nMetrics (lower is better):")
print(metrics_df.round(4).to_string(index=False))

baseline_mae = metrics_df.loc[
    metrics_df["model"] == "Previous-day baseline",
    "MAE_percentage_points"
].iloc[0]

best_model = metrics_df.iloc[0]
print("\nLowest-MAE model:", best_model["model"])

if best_model["model"] != "Previous-day baseline":
    improvement = (
        (baseline_mae - best_model["MAE_percentage_points"])
        / baseline_mae
    ) * 100
    print(f"MAE improvement over baseline: {improvement:.2f}%")
else:
    print("Machine learning did not beat the baseline on MAE.")

print("\nFiles saved:")
print(output_dir / "nrw_forecast_metrics.csv")
print(output_dir / "nrw_forecast_predictions.csv")
