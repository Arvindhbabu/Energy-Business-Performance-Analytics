-- ==============================================================================
-- ENERGY CONSUMPTION & BUSINESS PERFORMANCE ANALYTICS
-- DDL Schema Definition (Relational Star Schema & Analytics Mart)
-- Standard SQL / SQLite / PostgreSQL / DuckDB Compatible
-- ==============================================================================

-- 1. Dimension Table: Building Master
DROP TABLE IF EXISTS dim_building;
CREATE TABLE dim_building (
    building_id VARCHAR(10) PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL
);

-- 2. Dimension Table: Utility Rates
DROP TABLE IF EXISTS dim_rate;
CREATE TABLE dim_rate (
    rate_year INT NOT NULL,
    energy_type VARCHAR(20) NOT NULL,
    price_per_unit DECIMAL(10, 6) NOT NULL,
    PRIMARY KEY (rate_year, energy_type)
);

-- 3. Fact Table: Monthly Energy Consumption
DROP TABLE IF EXISTS fact_energy_consumption;
CREATE TABLE fact_energy_consumption (
    consumption_id INTEGER PRIMARY KEY AUTOINCREMENT,
    consumption_date DATE NOT NULL,
    building_id VARCHAR(10) NOT NULL,
    water_consumption BIGINT NOT NULL,
    electricity_consumption BIGINT NOT NULL,
    gas_consumption BIGINT NOT NULL,
    FOREIGN KEY (building_id) REFERENCES dim_building(building_id)
);

-- 4. Analytical Master Mart View (Enriched with Rates and Cost Calculations)
DROP VIEW IF EXISTS view_energy_master_mart;
CREATE VIEW view_energy_master_mart AS
WITH rate_pivoted AS (
    SELECT
        rate_year,
        MAX(CASE WHEN energy_type = 'Water' THEN price_per_unit END) AS water_rate,
        MAX(CASE WHEN energy_type = 'Electricity' THEN price_per_unit END) AS electricity_rate,
        MAX(CASE WHEN energy_type = 'Gas' THEN price_per_unit END) AS gas_rate
    FROM dim_rate
    GROUP BY rate_year
)
SELECT
    f.consumption_id,
    f.consumption_date,
    strftime('%Y-%m', f.consumption_date) AS year_month,
    CAST(strftime('%Y', f.consumption_date) AS INT) AS consumption_year,
    CAST(strftime('%m', f.consumption_date) AS INT) AS consumption_month,
    f.building_id,
    b.city,
    b.country,
    f.water_consumption,
    f.electricity_consumption,
    f.gas_consumption,
    r.water_rate,
    r.electricity_rate,
    r.gas_rate,
    -- Financial Cost Engineering
    ROUND(f.water_consumption * r.water_rate, 2) AS water_cost,
    ROUND(f.electricity_consumption * r.electricity_rate, 2) AS electricity_cost,
    ROUND(f.gas_consumption * r.gas_rate, 2) AS gas_cost,
    ROUND(
        (f.water_consumption * r.water_rate) +
        (f.electricity_consumption * r.electricity_rate) +
        (f.gas_consumption * r.gas_rate),
        2
    ) AS total_utility_cost
FROM fact_energy_consumption f
JOIN dim_building b ON f.building_id = b.building_id
JOIN rate_pivoted r ON CAST(strftime('%Y', f.consumption_date) AS INT) = r.rate_year;
