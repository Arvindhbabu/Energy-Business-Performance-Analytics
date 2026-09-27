-- ==============================================================================
-- GEOGRAPHIC & REGIONAL PERFORMANCE ANALYTICS (SQL)
-- Resolves aggregation bias by comparing Total Spend against Normalized Building Averages.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 09 (Q5, Q6): City-Level Expenditure: Aggregate Total vs Normalized Per-Building
-- Demonstrates: Advanced ranking comparison showing rank reversal between total and per-building.
-- ------------------------------------------------------------------------------
WITH city_summary AS (
    SELECT
        city,
        COUNT(DISTINCT building_id) AS building_count,
        SUM(water_consumption) AS city_water_volume,
        SUM(electricity_consumption) AS city_electricity_volume,
        SUM(gas_consumption) AS city_gas_volume,
        SUM(total_utility_cost) AS total_city_cost
    FROM view_energy_master_mart
    GROUP BY city
)
SELECT
    city,
    building_count,
    ROUND(total_city_cost, 2) AS total_city_cost_usd,
    RANK() OVER (ORDER BY total_city_cost DESC) AS total_cost_rank,
    ROUND(total_city_cost / building_count, 2) AS avg_cost_per_building_usd,
    RANK() OVER (ORDER BY (total_city_cost / building_count) DESC) AS normalized_cost_rank,
    ROUND((total_city_cost / SUM(total_city_cost) OVER ()) * 100.0, 2) AS portfolio_share_pct
FROM city_summary
ORDER BY total_city_cost DESC;

-- ------------------------------------------------------------------------------
-- Query 10: Geographic Utility Mix and Consumption Profile
-- Evaluates the utility consumption intensity per building across metropolitan areas.
-- ------------------------------------------------------------------------------
SELECT
    city,
    COUNT(DISTINCT building_id) AS building_count,
    ROUND(SUM(water_consumption) * 1.0 / COUNT(DISTINCT building_id), 0) AS avg_water_per_building,
    ROUND(SUM(electricity_consumption) * 1.0 / COUNT(DISTINCT building_id), 0) AS avg_elec_per_building,
    ROUND(SUM(gas_consumption) * 1.0 / COUNT(DISTINCT building_id), 0) AS avg_gas_per_building,
    ROUND(SUM(water_cost), 2) AS total_water_cost,
    ROUND(SUM(electricity_cost), 2) AS total_electricity_cost,
    ROUND(SUM(gas_cost), 2) AS total_gas_cost,
    ROUND(SUM(total_utility_cost), 2) AS total_utility_cost
FROM view_energy_master_mart
GROUP BY city
ORDER BY total_utility_cost DESC;

-- ------------------------------------------------------------------------------
-- Query 11: City Annual Cost Progression and Growth Rates
-- Demonstrates: Multi-dimensional grouping and Window LAG partitioned by city.
-- ------------------------------------------------------------------------------
WITH city_annual AS (
    SELECT
        city,
        consumption_year,
        COUNT(DISTINCT building_id) AS building_count,
        SUM(total_utility_cost) AS annual_cost
    FROM view_energy_master_mart
    GROUP BY city, consumption_year
)
SELECT
    city,
    consumption_year,
    building_count,
    ROUND(annual_cost, 2) AS annual_cost_usd,
    ROUND(annual_cost / building_count, 2) AS annual_cost_per_building_usd,
    LAG(annual_cost, 1) OVER (PARTITION BY city ORDER BY consumption_year) AS prev_year_cost_usd,
    ROUND(
        (annual_cost - LAG(annual_cost, 1) OVER (PARTITION BY city ORDER BY consumption_year))
        / LAG(annual_cost, 1) OVER (PARTITION BY city ORDER BY consumption_year) * 100.0,
        2
    ) AS yoy_city_growth_pct
FROM city_annual
ORDER BY city, consumption_year;
