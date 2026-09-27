-- ==============================================================================
-- TIME-SERIES & TREND ANALYTICS (SQL)
-- Implements MoM, YoY, Rolling Moving Averages, and Identifies Volatility Extremes.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 12 (Q12, Q13): Portfolio Month-over-Month and Year-over-Year Dynamics
-- Demonstrates: LAG(1) for MoM and LAG(12) for YoY across consecutive calendar months.
-- ------------------------------------------------------------------------------
WITH monthly_metrics AS (
    SELECT
        year_month,
        MIN(consumption_date) AS month_start_date,
        SUM(total_utility_cost) AS total_monthly_cost,
        SUM(water_consumption) AS water_vol,
        SUM(electricity_consumption) AS elec_vol,
        SUM(gas_consumption) AS gas_vol
    FROM view_energy_master_mart
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(total_monthly_cost, 2) AS monthly_cost_usd,
    -- 1-Month Lag (MoM)
    LAG(total_monthly_cost, 1) OVER (ORDER BY year_month) AS prev_month_cost_usd,
    ROUND(
        (total_monthly_cost - LAG(total_monthly_cost, 1) OVER (ORDER BY year_month))
        / LAG(total_monthly_cost, 1) OVER (ORDER BY year_month) * 100.0,
        2
    ) AS mom_cost_growth_pct,
    -- 12-Month Lag (YoY)
    LAG(total_monthly_cost, 12) OVER (ORDER BY year_month) AS prev_year_same_month_cost_usd,
    ROUND(
        (total_monthly_cost - LAG(total_monthly_cost, 12) OVER (ORDER BY year_month))
        / LAG(total_monthly_cost, 12) OVER (ORDER BY year_month) * 100.0,
        2
    ) AS yoy_monthly_growth_pct
FROM monthly_metrics
ORDER BY year_month;

-- ------------------------------------------------------------------------------
-- Query 13 (Q19): Rolling 3-Month and 12-Month Moving Averages
-- Demonstrates: Window Frame specifications (ROWS BETWEEN N PRECEDING AND CURRENT ROW).
-- ------------------------------------------------------------------------------
WITH monthly_cost AS (
    SELECT
        year_month,
        SUM(total_utility_cost) AS monthly_cost
    FROM view_energy_master_mart
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(monthly_cost, 2) AS monthly_cost_usd,
    -- 3-Month Rolling Average
    ROUND(
        AVG(monthly_cost) OVER (
            ORDER BY year_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS rolling_3m_avg_cost_usd,
    -- 12-Month Rolling Average (Seasonality Smoothed Trend)
    ROUND(
        AVG(monthly_cost) OVER (
            ORDER BY year_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS rolling_12m_avg_cost_usd
FROM monthly_cost
ORDER BY year_month;

-- ------------------------------------------------------------------------------
-- Query 14 (Q20): Top 5 Largest Monthly Cost Surges (Largest Positive Changes)
-- Demonstrates: CTE with Window LAG and ORDER BY absolute/pct difference DESC.
-- ------------------------------------------------------------------------------
WITH monthly_diff AS (
    SELECT
        year_month,
        SUM(total_utility_cost) AS current_cost,
        LAG(SUM(total_utility_cost), 1) OVER (ORDER BY year_month) AS prev_cost
    FROM view_energy_master_mart
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(prev_cost, 2) AS previous_month_cost_usd,
    ROUND(current_cost, 2) AS current_month_cost_usd,
    ROUND(current_cost - prev_cost, 2) AS absolute_cost_increase_usd,
    ROUND(((current_cost - prev_cost) / prev_cost) * 100.0, 2) AS mom_growth_pct
FROM monthly_diff
WHERE prev_cost IS NOT NULL
ORDER BY (current_cost - prev_cost) DESC
LIMIT 5;

-- ------------------------------------------------------------------------------
-- Query 15 (Q20): Top 5 Largest Monthly Cost Drops (Largest Negative Changes)
-- Demonstrates: Identifying post-peak demand contractions and seasonal relief.
-- ------------------------------------------------------------------------------
WITH monthly_diff AS (
    SELECT
        year_month,
        SUM(total_utility_cost) AS current_cost,
        LAG(SUM(total_utility_cost), 1) OVER (ORDER BY year_month) AS prev_cost
    FROM view_energy_master_mart
    GROUP BY year_month
)
SELECT
    year_month,
    ROUND(prev_cost, 2) AS previous_month_cost_usd,
    ROUND(current_cost, 2) AS current_month_cost_usd,
    ROUND(current_cost - prev_cost, 2) AS absolute_cost_decrease_usd,
    ROUND(((current_cost - prev_cost) / prev_cost) * 100.0, 2) AS mom_drop_pct
FROM monthly_diff
WHERE prev_cost IS NOT NULL
ORDER BY (current_cost - prev_cost) ASC
LIMIT 5;
