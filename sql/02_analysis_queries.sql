-- ============================================================
-- Urban Water Supply Intelligence & Demand Analytics
-- 02_analysis_queries.sql
-- A library of analytical queries that power the KPIs used in
-- the Python notebooks and the Power BI dashboard.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Non-Revenue Water (NRW) % by zone, monthly
--    NRW% = (Production - Billed) / Production * 100
-- ------------------------------------------------------------
SELECT
    zone_id,
    DATE_TRUNC('month', date)::date AS month,
    SUM(production_volume_liters)                                   AS production_liters,
    SUM(billed_consumption_liters)                                  AS billed_liters,
    ROUND(
        100.0 * (SUM(production_volume_liters) - SUM(billed_consumption_liters))
        / NULLIF(SUM(production_volume_liters), 0), 2
    ) AS nrw_pct
FROM consumption_daily
GROUP BY zone_id, DATE_TRUNC('month', date)
ORDER BY zone_id, month;

-- ------------------------------------------------------------
-- 2. Per-capita daily consumption (liters/person/day) by zone
-- ------------------------------------------------------------
SELECT
    c.zone_id,
    z.zone_name,
    DATE_TRUNC('month', c.date)::date AS month,
    ROUND(AVG(c.billed_consumption_liters * 1.0 / NULLIF(c.population_est, 0)), 1)
        AS avg_liters_per_capita_per_day
FROM consumption_daily c
JOIN zones z ON z.zone_id = c.zone_id
GROUP BY c.zone_id, z.zone_name, DATE_TRUNC('month', c.date)
ORDER BY c.zone_id, month;

-- ------------------------------------------------------------
-- 3. Year-over-year demand growth by zone
-- ------------------------------------------------------------
WITH yearly AS (
    SELECT zone_id, EXTRACT(YEAR FROM date)::int AS yr,
           SUM(billed_consumption_liters) AS total_billed
    FROM consumption_daily
    GROUP BY zone_id, EXTRACT(YEAR FROM date)
)
SELECT
    a.zone_id,
    a.yr AS year,
    a.total_billed,
    LAG(a.total_billed) OVER (PARTITION BY a.zone_id ORDER BY a.yr) AS prior_year_billed,
    ROUND(
        100.0 * (a.total_billed - LAG(a.total_billed) OVER (PARTITION BY a.zone_id ORDER BY a.yr))
        / NULLIF(LAG(a.total_billed) OVER (PARTITION BY a.zone_id ORDER BY a.yr), 0), 2
    ) AS yoy_growth_pct
FROM yearly a
ORDER BY a.zone_id, a.yr;

-- ------------------------------------------------------------
-- 4. Top zones by leakage volume and incident severity mix
-- ------------------------------------------------------------
SELECT
    z.zone_id,
    z.zone_name,
    COUNT(*)                                    AS incident_count,
    SUM(li.estimated_volume_lost_liters)        AS total_liters_lost,
    ROUND(AVG(li.resolved_date - li.reported_date), 1) AS avg_days_to_resolve,
    SUM(CASE WHEN li.severity = 'High' THEN 1 ELSE 0 END)   AS high_severity_count
FROM leakage_incidents li
JOIN zones z ON z.zone_id = li.zone_id
GROUP BY z.zone_id, z.zone_name
ORDER BY total_liters_lost DESC;

-- ------------------------------------------------------------
-- 5. Aging / high-risk pipe segments (older infrastructure,
--    material prone to failure, in zones with recent leaks)
-- ------------------------------------------------------------
SELECT
    p.pipe_id,
    p.zone_id,
    p.material,
    p.install_year,
    (EXTRACT(YEAR FROM CURRENT_DATE) - p.install_year)::int AS age_years,
    p.avg_pressure_bar,
    COUNT(li.incident_id) AS leak_history_count
FROM pipe_network p
LEFT JOIN leakage_incidents li ON li.pipe_id = p.pipe_id
WHERE p.material IN ('Asbestos Cement', 'Cast Iron')
   OR (EXTRACT(YEAR FROM CURRENT_DATE) - p.install_year) > 40
GROUP BY p.pipe_id, p.zone_id, p.material, p.install_year, p.avg_pressure_bar
ORDER BY leak_history_count DESC, age_years DESC;

-- ------------------------------------------------------------
-- 6. Weather vs. demand correlation input (daily grain, ready
--    for Python / Power BI to compute correlation or feed a model)
-- ------------------------------------------------------------
SELECT
    c.date,
    c.zone_id,
    c.billed_consumption_liters,
    w.temp_c,
    w.rainfall_mm,
    w.humidity_pct
FROM consumption_daily c
JOIN weather_daily w ON w.zone_id = c.zone_id AND w.date = c.date
ORDER BY c.zone_id, c.date;

-- ------------------------------------------------------------
-- 7. Billing collection efficiency by zone (revenue at risk)
-- ------------------------------------------------------------
SELECT
    b.zone_id,
    z.zone_name,
    ROUND(AVG(b.collection_rate) * 100, 1)               AS avg_collection_rate_pct,
    SUM(b.revenue_expected)                               AS total_revenue_expected,
    SUM(b.revenue_expected - b.revenue_collected)          AS total_revenue_at_risk
FROM billing_monthly b
JOIN zones z ON z.zone_id = b.zone_id
GROUP BY b.zone_id, z.zone_name
ORDER BY total_revenue_at_risk DESC;

-- ------------------------------------------------------------
-- 8. Reservoir stress proxy: zone production vs. reservoir capacity
-- ------------------------------------------------------------
SELECT
    r.reservoir_id,
    r.zone_id,
    r.capacity_ml,
    ROUND(SUM(c.production_volume_liters) / 1000000.0, 2) AS total_production_ml,
    ROUND(
        (SUM(c.production_volume_liters) / 1000000.0) / NULLIF(r.capacity_ml, 0), 2
    ) AS approx_annual_capacity_turnover
FROM reservoirs r
JOIN consumption_daily c ON c.zone_id = r.zone_id
WHERE c.date >= DATE_TRUNC('year', CURRENT_DATE) - INTERVAL '1 year'
GROUP BY r.reservoir_id, r.zone_id, r.capacity_ml
ORDER BY approx_annual_capacity_turnover DESC;

-- ------------------------------------------------------------
-- 9. City-wide daily summary view (used as the Power BI fact table)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vw_daily_city_summary AS
SELECT
    c.date,
    SUM(c.billed_consumption_liters) AS total_billed_liters,
    SUM(c.production_volume_liters)  AS total_production_liters,
    ROUND(
        100.0 * (SUM(c.production_volume_liters) - SUM(c.billed_consumption_liters))
        / NULLIF(SUM(c.production_volume_liters), 0), 2
    ) AS citywide_nrw_pct,
    ROUND(AVG(w.temp_c), 1)      AS avg_temp_c,
    ROUND(SUM(w.rainfall_mm), 1) AS total_rainfall_mm
FROM consumption_daily c
JOIN weather_daily w ON w.zone_id = c.zone_id AND w.date = c.date
GROUP BY c.date
ORDER BY c.date;
