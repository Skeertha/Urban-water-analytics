-- =====================================================
-- Urban Water Analytics
-- SQL Business Analysis
-- Tool: MySQL
-- Purpose: Analyze NRW trends, production-billing gaps,
-- zone-level leakage and revenue risk.
-- =====================================================


-- =====================================================
-- 1. Overall KPI Analysis
-- =====================================================

SELECT
    SUM(production_amount) AS total_production,
    SUM(bill_amount) AS total_billed,
    AVG(nrw_pct) AS average_nrw
FROM citywide_daily_summary;



-- =====================================================
-- 2. Daily NRW Analysis
-- =====================================================

-- Top 10 days with highest NRW

SELECT
    date,
    production_amount,
    bill_amount,
    nrw_pct
FROM citywide_daily_summary
ORDER BY nrw_pct DESC
LIMIT 10;


-- Top 10 days with largest production-bill gap

SELECT
    date,
    production_amount,
    bill_amount,
    production_amount - bill_amount AS water_gap,
    nrw_pct
FROM citywide_daily_summary
ORDER BY water_gap DESC
LIMIT 10;



-- =====================================================
-- 3. Monthly Trend Analysis
-- =====================================================

SELECT
    YEAR(date) AS year,
    MONTH(date) AS month,
    SUM(production_amount) AS total_production,
    SUM(bill_amount) AS total_billed,
    AVG(nrw_pct) AS average_nrw
FROM citywide_daily_summary
GROUP BY YEAR(date), MONTH(date)
ORDER BY year, month;


-- Months with largest production-bill gap

SELECT
    YEAR(date) AS year,
    MONTH(date) AS month,
    SUM(production_amount - bill_amount) AS total_water_gap,
    AVG(nrw_pct) AS average_nrw
FROM citywide_daily_summary
GROUP BY YEAR(date), MONTH(date)
ORDER BY total_water_gap DESC
LIMIT 10;



-- =====================================================
-- 4. NRW Risk Classification
-- =====================================================

SELECT
    date,
    nrw_pct,
    CASE
        WHEN nrw_pct < 12 THEN 'Low NRW'
        WHEN nrw_pct < 14 THEN 'Moderate NRW'
        ELSE 'High NRW'
    END AS nrw_category
FROM citywide_daily_summary
ORDER BY nrw_pct DESC;



-- =====================================================
-- 5. Zone-Level Leakage Analysis
-- =====================================================

SELECT
    zone_name,
    incidents,
    ML_lost
FROM leakage_summary_by_zone
ORDER BY ML_lost DESC;


-- Average loss per incident

SELECT
    zone_name,
    incidents,
    ML_lost,
    ROUND(ML_lost / incidents, 2) AS avg_ML_lost_per_incident
FROM leakage_summary_by_zone
ORDER BY avg_ML_lost_per_incident DESC;



-- =====================================================
-- 6. Revenue Risk Analysis
-- =====================================================

SELECT *
FROM revenue_risk_by_zone
ORDER BY revenue_at_risk DESC;



-- =====================================================
-- 7. JOIN Analysis
-- =====================================================

SELECT
    l.zone_name,
    l.incidents,
    l.ML_lost,
    r.avg_collection_rate,
    r.revenue_expected,
    r.revenue_collected,
    r.revenue_at_risk
FROM leakage_summary_by_zone l
JOIN revenue_risk_by_zone r
    ON l.zone_name = r.zone_name
ORDER BY r.revenue_at_risk DESC;



-- =====================================================
-- 8. CTE Analysis
-- =====================================================

WITH zone_analysis AS (
    SELECT
        l.zone_name,
        l.incidents,
        l.ML_lost,
        r.revenue_at_risk,
        ROUND(l.ML_lost / l.incidents, 2) AS loss_per_incident
    FROM leakage_summary_by_zone l
    JOIN revenue_risk_by_zone r
        ON l.zone_name = r.zone_name
)

SELECT
    zone_name,
    incidents,
    ML_lost,
    loss_per_incident,
    revenue_at_risk
FROM zone_analysis
ORDER BY revenue_at_risk DESC;



-- =====================================================
-- 9. Window Function Ranking
-- =====================================================

SELECT
    zone_name,
    ML_lost,
    revenue_at_risk,
    RANK() OVER (
        ORDER BY revenue_at_risk DESC
    ) AS revenue_risk_rank,
    RANK() OVER (
        ORDER BY ML_lost DESC
    ) AS leakage_rank
FROM (
    SELECT
        l.zone_name,
        l.ML_lost,
        r.revenue_at_risk
    FROM leakage_summary_by_zone l
    JOIN revenue_risk_by_zone r
        ON l.zone_name = r.zone_name
) AS zone_data;