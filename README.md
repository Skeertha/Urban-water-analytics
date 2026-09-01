# 🚰 Urban Water Supply Intelligence & Demand Analytics

An end-to-end data project that combines **SQL + Python + Power BI + predictive
analytics** to solve a real-world municipal utility problem: how much water a
city will need, where it's being lost, and which zones are most at financial
and infrastructure risk.

Built around a synthetic but realistic dataset spanning **8 service zones,
3 years of daily data, weather, billing, pipe network, and leak incidents.**

## Business problem

Urban water utilities lose 10–35% of the water they produce before it's ever
billed — this is called **Non-Revenue Water (NRW)**. On top of that, planners
need to forecast demand for reservoir and pumping capacity, and finance teams
need visibility into revenue collection gaps. This project builds the
analytics stack a water utility's data team would actually build to tackle
all three problems together.

## What's inside

| Question | How it's answered |
|---|---|
| How much water are we losing, and where? | SQL NRW% queries + Isolation Forest anomaly detection on production-vs-billed gaps |
| What will demand look like next quarter? | Gradient Boosting time-series forecast (~1.5% MAPE) using weather + calendar + lag features |
| Which pipes/zones are highest risk? | SQL queries joining pipe age/material with leak history |
| Are we collecting the revenue we're owed? | Billing/collection-rate analysis by zone |
| How do I see all this at a glance? | Power BI dashboard spec with ready-to-paste DAX measures |

## Project structure

```
urban-water-analytics/
├── data/
│   ├── raw/                     # generated CSV source data (8 zones × 3 years)
│   └── processed/               # model outputs, KPI summaries
├── sql/
│   ├── 01_schema.sql            # relational schema (PostgreSQL)
│   └── 02_analysis_queries.sql  # NRW%, per-capita demand, YoY growth, revenue risk, etc.
├── python/
│   ├── 01_generate_data.py            # synthetic data generator
│   ├── 02_eda_and_visualization.py    # EDA, seasonality, weather correlation
│   ├── 03_demand_forecasting_model.py # Gradient Boosting demand forecast
│   └── 04_leak_anomaly_detection.py   # Isolation Forest NRW anomaly detection
├── powerbi/
│   └── PowerBI_Guide.md         # data model, DAX measures, page-by-page dashboard spec
├── outputs/figures/             # generated charts (PNG)
├── docs/
│   └── architecture.md          # data flow diagram & design rationale
├── requirements.txt
└── README.md
```

## Quickstart

```bash
git clone https://github.com/<your-username>/urban-water-analytics.git
cd urban-water-analytics
pip install -r requirements.txt

# 1. Generate the dataset
python python/01_generate_data.py

# 2. Run exploratory analysis (saves charts to outputs/figures)
python python/02_eda_and_visualization.py

# 3. Train & evaluate the demand forecasting model
python python/03_demand_forecasting_model.py

# 4. Run leak / NRW anomaly detection
python python/04_leak_anomaly_detection.py
```

To use the SQL layer, load `data/raw/*.csv` into a PostgreSQL database using
`sql/01_schema.sql`, then run the queries in `sql/02_analysis_queries.sql`.

To build the Power BI dashboard, follow `powerbi/PowerBI_Guide.md` — it lists
exactly which CSVs to import and the DAX measures to paste in.

## Key results (on the generated sample data)

- **Demand forecast accuracy:** ~1.5% MAPE on a 90-day held-out test period, using a Gradient Boosting model with weather, calendar, and lag features.
- **Leak detection:** Isolation Forest flags NRW anomalies with ~95% precision and ~76% recall against injected leak events, run independently per zone so small zones aren't masked by citywide averages.
- **NRW baseline:** ~10–16% system-wide losses plus zone-specific leak spikes, matching typical real-world utility ranges.

## Dataset

Since real SCADA/meter/billing data from a utility isn't publicly available,
`python/01_generate_data.py` generates a realistic synthetic dataset with:

- Seasonal + weekly demand patterns (higher in summer, weekday/weekend splits by zone type)
- Weather-driven variation (temperature, rainfall, humidity)
- Randomly injected leak events with realistic duration/severity
- Population-driven demand growth trend over 3 years
- Billing collection rates with realistic variance

This makes the project fully reproducible and safe to publish on GitHub —
no confidential utility data required — while still exercising every skill
(SQL modeling, EDA, forecasting, anomaly detection, dashboarding) that a real
deployment would need.

## Tech stack

`Python (pandas, numpy, scikit-learn, matplotlib, seaborn)` · `SQL (PostgreSQL)` · `Power BI (DAX)`

## License

MIT — free to use, adapt, and extend for your own portfolio or coursework.
