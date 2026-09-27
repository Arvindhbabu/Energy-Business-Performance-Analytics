-- ==============================================================================
-- PORTFOLIO KPI & UTILITY COST ANALYTICS (SQL)
-- Answers executive questions on annual spend, growth trajectories, and utility contribution.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 01 (Q1, Q7): Total Utility Cost and Year-over-Year Cost Growth by Year
-- ------------------------------------------------------------------------------
WITH annual_spend AS (
    SELECT
        consumption_year,
        SUM(water_cost) AS total_water_cost,
        SUM(electricity_cost) AS total_electricity_cost,
        SUM(gas_cost) AS total_gas_cost,
        SUM(total_utility_cost) AS total_portfolio_cost
    FROM view_energy_master_mart
    GROUP BY consumption_year
)
SELECT
    consumption_year,
    ROUND(total_water_cost, 2) AS total_water_cost,
    ROUND(total_electricity_cost, 2) AS total_electricity_cost,
    ROUND(total_gas_cost, 2) AS total_gas_cost,
    ROUND(total_portfolio_cost, 2) AS total_portfolio_cost,
    LAG(total_portfolio_cost, 1) OVER (ORDER BY consumption_year) AS prev_year_portfolio_cost,
    ROUND(
        (total_portfolio_cost - LAG(total_portfolio_cost, 1) OVER (ORDER BY consumption_year))
        / LAG(total_portfolio_cost, 1) OVER (ORDER BY consumption_year) * 100.0,
        2
    ) AS yoy_cost_growth_pct
FROM annual_spend
ORDER BY consumption_year;

-- ------------------------------------------------------------------------------
-- Query 02 (Q2, Q3, Q18): Portfolio Utility Consumption Totals and Cost Contribution %
-- ------------------------------------------------------------------------------
WITH utility_totals AS (
    SELECT
        SUM(water_consumption) AS total_water_volume,
        SUM(electricity_consumption) AS total_electricity_volume,
        SUM(gas_consumption) AS total_gas_volume,
        SUM(water_cost) AS total_water_cost,
        SUM(electricity_cost) AS total_electricity_cost,
        SUM(gas_cost) AS total_gas_cost,
        SUM(total_utility_cost) AS total_portfolio_cost
    FROM view_energy_master_mart
)
SELECT
    'Water' AS utility_name,
    total_water_volume AS total_consumption_volume,
    'Gallons/Units' AS unit_of_measure,
    ROUND(total_water_cost, 2) AS total_cost_usd,
    ROUND((total_water_cost / total_portfolio_cost) * 100.0, 2) AS cost_share_pct
FROM utility_totals
UNION ALL
SELECT
    'Electricity' AS utility_name,
    total_electricity_volume AS total_consumption_volume,
    'kWh' AS unit_of_measure,
    ROUND(total_electricity_cost, 2) AS total_cost_usd,
    ROUND((total_electricity_cost / total_portfolio_cost) * 100.0, 2) AS cost_share_pct
FROM utility_totals
UNION ALL
SELECT
    'Gas' AS utility_name,
    total_gas_volume AS total_consumption_volume,
    'Units/Therms' AS unit_of_measure,
    ROUND(total_gas_cost, 2) AS total_cost_usd,
    ROUND((total_gas_cost / total_portfolio_cost) * 100.0, 2) AS cost_share_pct
FROM utility_totals
ORDER BY total_cost_usd DESC;

-- ------------------------------------------------------------------------------
-- Query 03 (Q8, Q9): Monthly Portfolio Consumption and Cost Trajectory
-- ------------------------------------------------------------------------------
SELECT
    year_month,
    SUM(water_consumption) AS monthly_water_consumption,
    SUM(electricity_consumption) AS monthly_electricity_consumption,
    SUM(gas_consumption) AS monthly_gas_consumption,
    ROUND(SUM(water_cost), 2) AS monthly_water_cost,
    ROUND(SUM(electricity_cost), 2) AS monthly_electricity_cost,
    ROUND(SUM(gas_cost), 2) AS monthly_gas_cost,
    ROUND(SUM(total_utility_cost), 2) AS monthly_total_cost
FROM view_energy_master_mart
GROUP BY year_month
ORDER BY year_month;

-- ------------------------------------------------------------------------------
-- Query 04 (Q16): Utility-Level Annual Growth Comparison (Which utility grew fastest?)
-- ------------------------------------------------------------------------------
WITH yearly_util AS (
    SELECT
        consumption_year,
        SUM(water_cost) AS water_cost,
        SUM(electricity_cost) AS elec_cost,
        SUM(gas_cost) AS gas_cost
    FROM view_energy_master_mart
    GROUP BY consumption_year
)
SELECT
    consumption_year,
    ROUND(water_cost, 2) AS water_cost,
    ROUND((water_cost - LAG(water_cost) OVER (ORDER BY consumption_year)) / LAG(water_cost) OVER (ORDER BY consumption_year) * 100, 2) AS water_cost_growth_pct,
    ROUND(elec_cost, 2) AS electricity_cost,
    ROUND((elec_cost - LAG(elec_cost) OVER (ORDER BY consumption_year)) / LAG(elec_cost) OVER (ORDER BY consumption_year) * 100, 2) AS electricity_cost_growth_pct,
    ROUND(gas_cost, 2) AS gas_cost,
    ROUND((gas_cost - LAG(gas_cost) OVER (ORDER BY consumption_year)) / LAG(gas_cost) OVER (ORDER BY consumption_year) * 100, 2) AS gas_cost_growth_pct
FROM yearly_util
ORDER BY consumption_year;
