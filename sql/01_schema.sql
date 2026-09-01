-- ============================================================
-- Urban Water Supply Intelligence & Demand Analytics
-- 01_schema.sql
-- Target: PostgreSQL (works with minor tweaks on MySQL/SQL Server)
-- ============================================================

DROP TABLE IF EXISTS billing_monthly CASCADE;
DROP TABLE IF EXISTS leakage_incidents CASCADE;
DROP TABLE IF EXISTS consumption_daily CASCADE;
DROP TABLE IF EXISTS weather_daily CASCADE;
DROP TABLE IF EXISTS pipe_network CASCADE;
DROP TABLE IF EXISTS reservoirs CASCADE;
DROP TABLE IF EXISTS zones CASCADE;

CREATE TABLE zones (
    zone_id         VARCHAR(10) PRIMARY KEY,
    zone_name       VARCHAR(100) NOT NULL,
    zone_type       VARCHAR(20)  NOT NULL,   -- Residential / Commercial / Industrial / Mixed
    population      INT NOT NULL,
    num_households  INT NOT NULL,
    area_sq_km      NUMERIC(6,2) NOT NULL
);

CREATE TABLE reservoirs (
    reservoir_id       VARCHAR(10) PRIMARY KEY,
    zone_id            VARCHAR(10) REFERENCES zones(zone_id),
    reservoir_name     VARCHAR(120),
    capacity_ml        NUMERIC(10,2),      -- megaliters
    commissioned_year  INT
);

CREATE TABLE pipe_network (
    pipe_id         VARCHAR(10) PRIMARY KEY,
    zone_id         VARCHAR(10) REFERENCES zones(zone_id),
    length_km       NUMERIC(6,2),
    diameter_mm     INT,
    material        VARCHAR(30),
    install_year    INT,
    avg_pressure_bar NUMERIC(4,2)
);

CREATE TABLE weather_daily (
    date            DATE NOT NULL,
    zone_id         VARCHAR(10) REFERENCES zones(zone_id),
    temp_c          NUMERIC(4,1),
    rainfall_mm     NUMERIC(6,1),
    humidity_pct    NUMERIC(4,1),
    PRIMARY KEY (date, zone_id)
);

CREATE TABLE consumption_daily (
    date                        DATE NOT NULL,
    zone_id                     VARCHAR(10) REFERENCES zones(zone_id),
    population_est              INT,
    billed_consumption_liters   BIGINT,
    production_volume_liters    BIGINT,
    avg_pressure_bar            NUMERIC(4,2),
    PRIMARY KEY (date, zone_id)
);

CREATE TABLE leakage_incidents (
    incident_id                    VARCHAR(10) PRIMARY KEY,
    zone_id                        VARCHAR(10) REFERENCES zones(zone_id),
    pipe_id                        VARCHAR(10) REFERENCES pipe_network(pipe_id),
    reported_date                  DATE,
    resolved_date                  DATE,
    severity                       VARCHAR(10),   -- Low / Medium / High
    estimated_volume_lost_liters   BIGINT
);

CREATE TABLE billing_monthly (
    zone_id             VARCHAR(10) REFERENCES zones(zone_id),
    billing_month       DATE,
    billed_kilo_liters  NUMERIC(12,1),
    revenue_expected    NUMERIC(12,2),
    collection_rate     NUMERIC(5,3),
    revenue_collected   NUMERIC(12,2),
    PRIMARY KEY (zone_id, billing_month)
);

-- Helpful indexes for time-series and zone lookups
CREATE INDEX idx_consumption_zone_date ON consumption_daily(zone_id, date);
CREATE INDEX idx_weather_zone_date ON weather_daily(zone_id, date);
CREATE INDEX idx_leaks_zone ON leakage_incidents(zone_id);
CREATE INDEX idx_billing_zone_month ON billing_monthly(zone_id, billing_month);

-- ============================================================
-- Loading data (psql example — adjust paths/COPY for your engine)
-- ============================================================
-- \copy zones FROM 'data/raw/zones.csv' DELIMITER ',' CSV HEADER;
-- \copy reservoirs FROM 'data/raw/reservoirs.csv' DELIMITER ',' CSV HEADER;
-- \copy pipe_network FROM 'data/raw/pipe_network.csv' DELIMITER ',' CSV HEADER;
-- \copy weather_daily FROM 'data/raw/weather_daily.csv' DELIMITER ',' CSV HEADER;
-- \copy consumption_daily FROM 'data/raw/consumption_daily.csv' DELIMITER ',' CSV HEADER;
-- \copy leakage_incidents FROM 'data/raw/leakage_incidents.csv' DELIMITER ',' CSV HEADER;
-- \copy billing_monthly FROM 'data/raw/billing_monthly.csv' DELIMITER ',' CSV HEADER;
