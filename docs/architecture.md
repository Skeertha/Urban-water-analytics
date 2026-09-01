# Architecture & Data Flow

```mermaid
flowchart LR
    A[Synthetic / Source Data<br/>SCADA, meters, weather, billing] --> B[python/01_generate_data.py]
    B --> C[(data/raw/*.csv)]
    C --> D[SQL Database<br/>sql/01_schema.sql]
    D --> E[sql/02_analysis_queries.sql<br/>KPI views & queries]
    C --> F[python/02_eda_and_visualization.py<br/>EDA & charts]
    C --> G[python/03_demand_forecasting_model.py<br/>Gradient Boosting forecast]
    C --> H[python/04_leak_anomaly_detection.py<br/>Isolation Forest NRW anomalies]
    F --> I[(data/processed/*.csv)]
    G --> I
    H --> I
    E --> J[Power BI Dashboard]
    I --> J
    C --> J
```

## Layer responsibilities

| Layer | Tool | Responsibility |
|---|---|---|
| Data generation | Python | Produces a realistic multi-year dataset across 8 zones: consumption, weather, pipe network, leaks, billing |
| Storage / modeling | SQL | Relational schema, indexes, and reusable analytical queries (NRW %, per-capita demand, YoY growth, revenue risk) |
| Analysis | Python (pandas, seaborn) | Exploratory data analysis, seasonality and correlation charts |
| Predictive analytics | Python (scikit-learn) | Gradient Boosting demand forecast (~1.5% MAPE on held-out 90 days) and Isolation Forest leak/NRW anomaly detection |
| Visualization | Power BI | Executive dashboard: city overview, forecasting, leakage/infrastructure risk, billing & revenue |

## Why this design

- **Zone-level granularity** mirrors how real utilities segment a city (District Metered Areas), which is what makes NRW% and leak detection meaningful.
- **Production vs. billed** split is the backbone of the Non-Revenue Water (NRW) KPI, the single most-watched metric in water utility operations.
- **Per-zone anomaly detection** (rather than one citywide model) avoids masking a small zone's leak inside citywide averages.
- **Calendar + weather + lag features** in the forecasting model reflect the real drivers of urban water demand: seasonality, weekday/weekend behavior, temperature, and recent trend.
