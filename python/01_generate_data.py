"""
01_generate_data.py
--------------------
Generates a realistic synthetic dataset for the Urban Water Supply
Intelligence & Demand Analytics project and writes CSVs to data/raw/.

Tables produced:
    zones.csv               - service zones (static attributes)
    reservoirs.csv          - reservoirs feeding each zone
    pipe_network.csv        - pipe segments per zone
    weather_daily.csv       - daily weather per zone
    consumption_daily.csv   - daily metered water consumption per zone
    leakage_incidents.csv   - recorded leak/burst events
    billing_monthly.csv     - monthly billing & revenue collection

Design notes (why the numbers look the way they do):
    - Consumption has yearly seasonality (higher in hot/dry months),
      a weekly pattern (lower on weekends for commercial zones),
      a slow upward population-driven trend, and random noise.
    - A handful of "leak events" are injected as sustained upward
      spikes in raw production vs. billed consumption, feeding the
      Non-Revenue Water (NRW) calculations downstream.
    - Everything is seeded for reproducibility.
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = pd.Timestamp("2023-01-01")
END_DATE = pd.Timestamp("2025-12-31")
DATES = pd.date_range(START_DATE, END_DATE, freq="D")

ZONE_DEFS = [
    # zone_id, name, type, population, households, area_km2
    ("Z01", "Riverside North", "Residential", 48000, 14200, 6.1),
    ("Z02", "Old Town Central", "Mixed",        62000, 17800, 4.3),
    ("Z03", "Greenfield Suburbs", "Residential", 35500, 10600, 9.8),
    ("Z04", "Industrial Belt East", "Industrial", 12800, 2100, 7.4),
    ("Z05", "Lakeside Heights", "Residential",  27600, 8300, 5.5),
    ("Z06", "Downtown Business", "Commercial",  18900, 4100, 2.9),
    ("Z07", "Harborview", "Mixed",               31200, 9700, 5.0),
    ("Z08", "Hillcrest", "Residential",          22400, 6900, 6.7),
]

MATERIALS = ["Ductile Iron", "PVC", "Cast Iron", "HDPE", "Asbestos Cement"]


def build_zones():
    df = pd.DataFrame(
        ZONE_DEFS,
        columns=["zone_id", "zone_name", "zone_type", "population",
                 "num_households", "area_sq_km"],
    )
    return df


def build_reservoirs(zones):
    rows = []
    for i, z in zones.iterrows():
        capacity = round(z.population * rng.uniform(0.08, 0.15), 1)  # ML
        rows.append({
            "reservoir_id": f"R{z.zone_id[1:]}",
            "zone_id": z.zone_id,
            "reservoir_name": f"{z.zone_name} Reservoir",
            "capacity_ml": capacity,
            "commissioned_year": int(rng.integers(1970, 2015)),
        })
    return pd.DataFrame(rows)


def build_pipe_network(zones):
    rows = []
    pipe_counter = 1
    for _, z in zones.iterrows():
        n_segments = int(rng.integers(6, 12))
        for _ in range(n_segments):
            rows.append({
                "pipe_id": f"P{pipe_counter:04d}",
                "zone_id": z.zone_id,
                "length_km": round(rng.uniform(0.5, 4.5), 2),
                "diameter_mm": int(rng.choice([100, 150, 200, 300, 400])),
                "material": rng.choice(MATERIALS),
                "install_year": int(rng.integers(1965, 2022)),
                "avg_pressure_bar": round(rng.uniform(2.0, 5.5), 2),
            })
            pipe_counter += 1
    return pd.DataFrame(rows)


def seasonal_factor(day_of_year):
    # Peak demand in summer (~day 200), trough in winter
    return 1 + 0.22 * np.sin(2 * np.pi * (day_of_year - 110) / 365)


def build_weather(zones):
    frames = []
    base_temp = {z.zone_id: rng.uniform(14, 19) for _, z in zones.iterrows()}
    for _, z in zones.iterrows():
        doy = DATES.dayofyear.values
        seasonal_temp = base_temp[z.zone_id] + 11 * np.sin(2 * np.pi * (doy - 100) / 365)
        temp = seasonal_temp + rng.normal(0, 1.8, len(DATES))
        rainfall = np.clip(
            rng.gamma(shape=0.5, scale=6.0, size=len(DATES))
            * (1 + 0.6 * np.sin(2 * np.pi * (doy - 300) / 365)),
            0, None,
        )
        humidity = np.clip(55 + 15 * np.sin(2 * np.pi * (doy - 300) / 365)
                            + rng.normal(0, 5, len(DATES)), 20, 100)
        frames.append(pd.DataFrame({
            "date": DATES,
            "zone_id": z.zone_id,
            "temp_c": temp.round(1),
            "rainfall_mm": rainfall.round(1),
            "humidity_pct": humidity.round(1),
        }))
    return pd.concat(frames, ignore_index=True)


def build_consumption_and_leaks(zones, weather):
    weather_idx = weather.set_index(["zone_id", "date"])
    cons_rows = []
    leak_rows = []
    leak_id = 1

    for _, z in zones.iterrows():
        # base per-capita daily consumption (liters/person/day)
        if z.zone_type == "Industrial":
            base_per_capita = rng.uniform(180, 230)
        elif z.zone_type == "Commercial":
            base_per_capita = rng.uniform(140, 180)
        else:
            base_per_capita = rng.uniform(110, 150)

        # slow population growth trend over 3 years
        growth = np.linspace(1.0, rng.uniform(1.04, 1.09), len(DATES))

        # pick 2-4 random leak episodes for this zone
        n_leaks = int(rng.integers(2, 5))
        leak_starts = rng.choice(np.arange(15, len(DATES) - 30), size=n_leaks, replace=False)
        leak_windows = []
        for ls in leak_starts:
            dur = int(rng.integers(5, 21))
            severity = rng.choice(["Low", "Medium", "High"], p=[0.5, 0.35, 0.15])
            magnitude = {"Low": rng.uniform(0.03, 0.07),
                         "Medium": rng.uniform(0.07, 0.14),
                         "High": rng.uniform(0.14, 0.25)}[severity]
            leak_windows.append((ls, ls + dur, magnitude, severity))
            resolved_date = DATES[min(ls + dur, len(DATES) - 1)]
            leak_rows.append({
                "incident_id": f"L{leak_id:04d}",
                "zone_id": z.zone_id,
                "pipe_id": None,  # linked later
                "reported_date": DATES[ls].date().isoformat(),
                "resolved_date": resolved_date.date().isoformat(),
                "severity": severity,
                "estimated_volume_lost_liters": None,  # filled after loop
            })
            leak_id += 1

        temp_series = weather_idx.loc[z.zone_id]["temp_c"].values
        rain_series = weather_idx.loc[z.zone_id]["rainfall_mm"].values
        doy = DATES.dayofyear.values
        dow = DATES.dayofweek.values

        seasonal = seasonal_factor(doy)
        weekday_factor = np.where(
            z.zone_type == "Commercial",
            np.where(dow >= 5, 0.55, 1.05),   # commercial: quiet weekends
            np.where(dow >= 5, 1.08, 0.98),   # residential: busier weekends
        )
        temp_effect = 1 + 0.012 * (temp_series - temp_series.mean())
        rain_effect = 1 - 0.01 * np.clip(rain_series, 0, 20) / 20

        noise = rng.normal(1.0, 0.035, len(DATES))

        billed_liters_per_capita = (
            base_per_capita * seasonal * weekday_factor * temp_effect
            * rain_effect * growth * noise
        )
        billed_total = billed_liters_per_capita * z.population  # liters/day

        # production = billed + non-revenue water (base losses + leak spikes)
        base_nrw_pct = rng.uniform(0.10, 0.16)  # 10-16% baseline system losses
        leak_extra = np.zeros(len(DATES))
        for (ls, le, magnitude, severity) in leak_windows:
            leak_extra[ls:le] += magnitude

        production_total = billed_total * (1 + base_nrw_pct + leak_extra)

        cons_rows.append(pd.DataFrame({
            "date": DATES,
            "zone_id": z.zone_id,
            "population_est": int(z.population),
            "billed_consumption_liters": billed_total.round(0).astype(int),
            "production_volume_liters": production_total.round(0).astype(int),
            "avg_pressure_bar": np.clip(rng.normal(3.6, 0.5, len(DATES)), 1.5, 6.0).round(2),
        }))

        # fill in estimated volume lost (liters) for each leak window of this zone
        zone_leak_rows = [r for r in leak_rows if r["zone_id"] == z.zone_id
                           and r["estimated_volume_lost_liters"] is None]
        for row, (ls, le, magnitude, severity) in zip(zone_leak_rows, leak_windows):
            vol = float((production_total[ls:le] - billed_total[ls:le] * (1 + base_nrw_pct)).sum())
            row["estimated_volume_lost_liters"] = max(round(vol), 0)

    consumption = pd.concat(cons_rows, ignore_index=True)
    leaks = pd.DataFrame(leak_rows)
    return consumption, leaks


def build_billing(zones, consumption):
    consumption["date"] = pd.to_datetime(consumption["date"])
    consumption["month"] = consumption["date"].values.astype("datetime64[M]")
    monthly = (consumption.groupby(["zone_id", "month"])["billed_consumption_liters"]
               .sum().reset_index())
    monthly["billed_kilo_liters"] = (monthly["billed_consumption_liters"] / 1000).round(1)

    rows = []
    rate_per_kl = 1.85  # currency units per 1000 liters
    for _, r in monthly.iterrows():
        revenue_expected = round(r["billed_kilo_liters"] * rate_per_kl, 2)
        collection_rate = round(float(np.clip(rng.normal(0.91, 0.05), 0.55, 1.0)), 3)
        revenue_collected = round(revenue_expected * collection_rate, 2)
        rows.append({
            "zone_id": r["zone_id"],
            "billing_month": r["month"].date().isoformat(),
            "billed_kilo_liters": r["billed_kilo_liters"],
            "revenue_expected": revenue_expected,
            "collection_rate": collection_rate,
            "revenue_collected": revenue_collected,
        })
    return pd.DataFrame(rows)


def main():
    zones = build_zones()
    reservoirs = build_reservoirs(zones)
    pipes = build_pipe_network(zones)
    weather = build_weather(zones)
    consumption, leaks = build_consumption_and_leaks(zones, weather)

    # link each leak incident to a random pipe in its zone (for realism)
    pipes_by_zone = pipes.groupby("zone_id")["pipe_id"].apply(list).to_dict()
    leaks["pipe_id"] = leaks["zone_id"].apply(lambda z: rng.choice(pipes_by_zone[z]))

    billing = build_billing(zones, consumption.copy())

    zones.to_csv(OUT_DIR / "zones.csv", index=False)
    reservoirs.to_csv(OUT_DIR / "reservoirs.csv", index=False)
    pipes.to_csv(OUT_DIR / "pipe_network.csv", index=False)
    weather.to_csv(OUT_DIR / "weather_daily.csv", index=False)
    consumption.to_csv(OUT_DIR / "consumption_daily.csv", index=False)
    leaks.to_csv(OUT_DIR / "leakage_incidents.csv", index=False)
    billing.to_csv(OUT_DIR / "billing_monthly.csv", index=False)

    print("Data generation complete. Files written to:", OUT_DIR)
    for f in sorted(OUT_DIR.glob("*.csv")):
        print(f" - {f.name}: {sum(1 for _ in open(f)) - 1} rows")


if __name__ == "__main__":
    main()
