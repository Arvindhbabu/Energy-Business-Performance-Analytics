-- ==============================================================================
-- BUILDING PERFORMANCE & COMPARATIVE ANALYTICS (SQL)
-- Identifies top and bottom cost drivers, rankings, utility mix, and facility growth.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 05 (Q4, Q14, Q15): Full Building Cost Ranking with Top 5 / Bottom 5 Classification
-- Demonstrates: Window Functions RANK(), DENSE_RANK(), and CASE expressions.
-- ------------------------------------------------------------------------------
WITH building_aggregates AS (
    SELECT
        building_id,
        city,
        COUNT(DISTINCT consumption_date) AS active_months,
        SUM(water_cost) AS total_water_cost,
        SUM(electricity_cost) AS total_electricity_cost,
        SUM(gas_cost) AS total_gas_cost,
        SUM(total_utility_cost) AS total_building_cost
    FROM view_energy_master_mart
    GROUP BY building_id, city
),
ranked_buildings AS (
    SELECT
        building_id,
        city,
        active_months,
        ROUND(total_building_cost, 2) AS total_building_cost,
        ROUND(total_building_cost / active_months, 2) AS avg_monthly_cost,
        RANK() OVER (ORDER BY total_building_cost DESC) AS cost_rank,
        DENSE_RANK() OVER (ORDER BY total_building_cost DESC) AS cost_dense_rank,
        ROUND(SUM(total_building_cost) OVER (), 2) AS portfolio_total_cost,
        ROUND((total_building_cost / SUM(total_building_cost) OVER ()) * 100.0, 2) AS portfolio_share_pct
    FROM building_aggregates
)
SELECT
    cost_rank,
    building_id,
    city,
    total_building_cost,
    avg_monthly_cost,
    portfolio_share_pct,
    CASE
        WHEN cost_rank <= 5 THEN 'Top 5 Highest Cost'
        WHEN cost_rank >= 7 THEN 'Bottom 5 Lowest Cost'
        ELSE 'Mid Tier'
    END AS cost_tier
FROM ranked_buildings
ORDER BY cost_rank;

-- ------------------------------------------------------------------------------
-- Query 06 (Q11): Utility Mix Breakdown by Building
-- Analyzes the percentage contribution of Water, Electricity, and Gas for each facility.
-- ------------------------------------------------------------------------------
SELECT
    building_id,
    city,
    ROUND(SUM(total_utility_cost), 2) AS total_building_cost,
    ROUND(SUM(water_cost), 2) AS water_cost,
    ROUND((SUM(water_cost) / SUM(total_utility_cost)) * 100.0, 2) AS water_share_pct,
    ROUND(SUM(electricity_cost), 2) AS electricity_cost,
    ROUND((SUM(electricity_cost) / SUM(total_utility_cost)) * 100.0, 2) AS electricity_share_pct,
    ROUND(SUM(gas_cost), 2) AS gas_cost,
    ROUND((SUM(gas_cost) / SUM(total_utility_cost)) * 100.0, 2) AS gas_share_pct
FROM view_energy_master_mart
GROUP BY building_id, city
ORDER BY total_building_cost DESC;

-- ------------------------------------------------------------------------------
-- Query 07 (Q10): Building-Level 4-Year Cost Growth (2016 vs 2019)
-- Evaluates which facility experienced the fastest cost expansion.
-- ------------------------------------------------------------------------------
WITH bldg_annual AS (
    SELECT
        building_id,
        city,
        consumption_year,
        SUM(total_utility_cost) AS annual_cost
    FROM view_energy_master_mart
    WHERE consumption_year IN (2016, 2019)
    GROUP BY building_id, city, consumption_year
),
pivoted AS (
    SELECT
        building_id,
        city,
        MAX(CASE WHEN consumption_year = 2016 THEN annual_cost END) AS cost_2016,
        MAX(CASE WHEN consumption_year = 2019 THEN annual_cost END) AS cost_2019
    FROM bldg_annual
    GROUP BY building_id, city
)
SELECT
    building_id,
    city,
    ROUND(cost_2016, 2) AS cost_2016_usd,
    ROUND(cost_2019, 2) AS cost_2019_usd,
    ROUND(cost_2019 - cost_2016, 2) AS absolute_cost_increase_usd,
    ROUND(((cost_2019 - cost_2016) / cost_2016) * 100.0, 2) AS four_year_growth_pct,
    RANK() OVER (ORDER BY ((cost_2019 - cost_2016) / cost_2016) DESC) AS growth_rank
FROM pivoted
ORDER BY four_year_growth_pct DESC;

-- ------------------------------------------------------------------------------
-- Query 08 (Q17): Building Peak-to-Average Consumption Volatility (Unusual Usage)
-- Calculates the peak-to-mean ratio for each utility by building.
-- ------------------------------------------------------------------------------
SELECT
    building_id,
    city,
    ROUND(MAX(water_consumption) * 1.0 / AVG(water_consumption), 2) AS water_peak_to_avg_ratio,
    ROUND(MAX(electricity_consumption) * 1.0 / AVG(electricity_consumption), 2) AS elec_peak_to_avg_ratio,
    ROUND(MAX(gas_consumption) * 1.0 / AVG(gas_consumption), 2) AS gas_peak_to_avg_ratio,
    ROUND(MAX(total_utility_cost) * 1.0 / AVG(total_utility_cost), 2) AS cost_peak_to_avg_ratio
FROM view_energy_master_mart
GROUP BY building_id, city
ORDER BY cost_peak_to_avg_ratio DESC;
