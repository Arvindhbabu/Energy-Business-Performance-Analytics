# SQL Analytics Execution Report

### Query: `q01_annual_cost_and_growth`

```sql
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
                ROUND(total_water_cost, 2) AS water_cost_usd,
                ROUND(total_electricity_cost, 2) AS electricity_cost_usd,
                ROUND(total_gas_cost, 2) AS gas_cost_usd,
                ROUND(total_portfolio_cost, 2) AS total_portfolio_cost_usd,
                LAG(total_portfolio_cost, 1) OVER (ORDER BY consumption_year) AS prev_year_cost_usd,
                ROUND(
                    (total_portfolio_cost - LAG(total_portfolio_cost, 1) OVER (ORDER BY consumption_year))
                    / LAG(total_portfolio_cost, 1) OVER (ORDER BY consumption_year) * 100.0,
                    2
                ) AS yoy_cost_growth_pct
            FROM annual_spend
            ORDER BY consumption_year;
```

**Results:**

| consumption_year | water_cost_usd | electricity_cost_usd | gas_cost_usd | total_portfolio_cost_usd | prev_year_cost_usd | yoy_cost_growth_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 2016.0 | 2259326.3 | 394720.0 | 504523.0 | 3158569.3 | nan | nan |
| 2017.0 | 2638119.48 | 461453.54 | 655055.5 | 3754628.19 | 3158569.3 | 18.87 |
| 2018.0 | 2865924.28 | 542462.39 | 825904.86 | 4234291.52 | 3754628.19 | 12.78 |
| 2019.0 | 3042822.37 | 626660.12 | 1025527.58 | 4695010.05 | 4234291.52 | 10.88 |

---

### Query: `q02_utility_cost_and_volume_totals`

```sql
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
```

**Results:**

| utility_name | total_consumption_volume | unit_of_measure | total_cost_usd | cost_share_pct |
| --- | --- | --- | --- | --- |
| Water | 186245327 | Gallons/Units | 10806192.43 | 68.21 |
| Gas | 2553088 | Units/Therms | 3011010.94 | 19.01 |
| Electricity | 21666978 | kWh | 2025296.05 | 12.78 |

---

### Query: `q05_building_rankings`

```sql
WITH building_aggregates AS (
                SELECT
                    building_id,
                    city,
                    COUNT(DISTINCT consumption_date) AS active_months,
                    SUM(total_utility_cost) AS total_building_cost
                FROM view_energy_master_mart
                GROUP BY building_id, city
            )
            SELECT
                RANK() OVER (ORDER BY total_building_cost DESC) AS cost_rank,
                building_id,
                city,
                ROUND(total_building_cost, 2) AS total_building_cost_usd,
                ROUND(total_building_cost / active_months, 2) AS avg_monthly_cost_usd,
                ROUND((total_building_cost / SUM(total_building_cost) OVER ()) * 100.0, 2) AS portfolio_share_pct,
                CASE
                    WHEN RANK() OVER (ORDER BY total_building_cost DESC) <= 5 THEN 'Top 5 Highest Cost'
                    WHEN RANK() OVER (ORDER BY total_building_cost DESC) >= 7 THEN 'Bottom 5 Lowest Cost'
                    ELSE 'Mid Tier'
                END AS cost_tier
            FROM building_aggregates
            ORDER BY cost_rank;
```

**Results:**

| cost_rank | building_id | city | total_building_cost_usd | avg_monthly_cost_usd | portfolio_share_pct | cost_tier |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | B1008 | Chicago | 1496830.1 | 31183.96 | 9.45 | Top 5 Highest Cost |
| 2 | B1006 | Phoenix | 1479068.13 | 30813.92 | 9.34 | Top 5 Highest Cost |
| 3 | B1001 | New York | 1477667.48 | 30784.74 | 9.33 | Top 5 Highest Cost |
| 4 | B1000 | New York | 1468356.73 | 30590.77 | 9.27 | Top 5 Highest Cost |
| 5 | B1003 | Los Angeles | 1461989.81 | 30458.12 | 9.23 | Top 5 Highest Cost |
| 6 | B1010 | Los Angeles | 1459011.21 | 30396.07 | 9.21 | Mid Tier |
| 7 | B1004 | Chicago | 1453834.05 | 30288.21 | 9.18 | Bottom 5 Lowest Cost |
| 8 | B1005 | Houston | 1440927.75 | 30019.33 | 9.1 | Bottom 5 Lowest Cost |
| 9 | B1002 | New York | 1389020.22 | 28937.92 | 8.77 | Bottom 5 Lowest Cost |
| 10 | B1009 | Los Angeles | 1359142.12 | 28315.46 | 8.58 | Bottom 5 Lowest Cost |
| 11 | B1007 | Chicago | 1356651.46 | 28263.57 | 8.56 | Bottom 5 Lowest Cost |

---

### Query: `q09_city_total_vs_normalized`

```sql
WITH city_summary AS (
                SELECT
                    city,
                    COUNT(DISTINCT building_id) AS building_count,
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
```

**Results:**

| city | building_count | total_city_cost_usd | total_cost_rank | avg_cost_per_building_usd | normalized_cost_rank | portfolio_share_pct |
| --- | --- | --- | --- | --- | --- | --- |
| New York | 3 | 4335044.43 | 1 | 1445014.81 | 2 | 27.36 |
| Chicago | 3 | 4307315.61 | 2 | 1435771.87 | 4 | 27.19 |
| Los Angeles | 3 | 4280143.14 | 3 | 1426714.38 | 5 | 27.02 |
| Phoenix | 1 | 1479068.13 | 4 | 1479068.13 | 1 | 9.34 |
| Houston | 1 | 1440927.75 | 5 | 1440927.75 | 3 | 9.1 |

---

### Query: `q12_mom_yoy_dynamics`

```sql
WITH monthly_metrics AS (
                SELECT
                    year_month,
                    SUM(total_utility_cost) AS total_monthly_cost
                FROM view_energy_master_mart
                GROUP BY year_month
            )
            SELECT
                year_month,
                ROUND(total_monthly_cost, 2) AS monthly_cost_usd,
                LAG(total_monthly_cost, 1) OVER (ORDER BY year_month) AS prev_month_cost_usd,
                ROUND(
                    (total_monthly_cost - LAG(total_monthly_cost, 1) OVER (ORDER BY year_month))
                    / LAG(total_monthly_cost, 1) OVER (ORDER BY year_month) * 100.0,
                    2
                ) AS mom_cost_growth_pct,
                LAG(total_monthly_cost, 12) OVER (ORDER BY year_month) AS prev_year_month_cost_usd,
                ROUND(
                    (total_monthly_cost - LAG(total_monthly_cost, 12) OVER (ORDER BY year_month))
                    / LAG(total_monthly_cost, 12) OVER (ORDER BY year_month) * 100.0,
                    2
                ) AS yoy_cost_growth_pct
            FROM monthly_metrics
            ORDER BY year_month;
```

**Results:**

| year_month | monthly_cost_usd | prev_month_cost_usd | mom_cost_growth_pct | prev_year_month_cost_usd | yoy_cost_growth_pct |
| --- | --- | --- | --- | --- | --- |
| 2016-01 | 251871.95 | nan | nan | nan | nan |
| 2016-02 | 256441.92 | 251871.94999999998 | 1.81 | nan | nan |
| 2016-03 | 262776.82 | 256441.91999999998 | 2.47 | nan | nan |
| 2016-04 | 257683.12 | 262776.82 | -1.94 | nan | nan |
| 2016-05 | 293016.65 | 257683.12 | 13.71 | nan | nan |
| 2016-06 | 276389.26 | 293016.65 | -5.67 | nan | nan |
| 2016-07 | 259446.37 | 276389.26 | -6.13 | nan | nan |
| 2016-08 | 250558.67 | 259446.37 | -3.43 | nan | nan |
| 2016-09 | 254419.8 | 250558.67 | 1.54 | nan | nan |
| 2016-10 | 278509.19 | 254419.8 | 9.47 | nan | nan |
| 2016-11 | 243543.52 | 278509.19 | -12.55 | nan | nan |
| 2016-12 | 273912.03 | 243543.52 | 12.47 | nan | nan |
| 2017-01 | 327543.39 | 273912.02999999997 | 19.58 | 251871.94999999998 | 30.04 |
| 2017-02 | 308289.34 | 327543.39 | -5.88 | 256441.91999999998 | 20.22 |
| 2017-03 | 279050.37 | 308289.34 | -9.48 | 262776.82 | 6.19 |
| 2017-04 | 334567.59 | 279050.37 | 19.9 | 257683.12 | 29.84 |
| 2017-05 | 311501.99 | 334567.58999999997 | -6.89 | 293016.65 | 6.31 |
| 2017-06 | 292960.25 | 311501.99 | -5.95 | 276389.26 | 6.0 |
| 2017-07 | 312327.07 | 292960.25 | 6.61 | 259446.37 | 20.38 |
| 2017-08 | 299995.6 | 312327.07 | -3.95 | 250558.67 | 19.73 |
| 2017-09 | 321001.19 | 299995.6 | 7.0 | 254419.8 | 26.17 |
| 2017-10 | 318478.87 | 321001.19 | -0.79 | 278509.19 | 14.35 |
| 2017-11 | 334171.61 | 318478.87 | 4.93 | 243543.52 | 37.21 |
| 2017-12 | 314740.92 | 334171.61 | -5.81 | 273912.02999999997 | 14.91 |
| 2018-01 | 339433.99 | 314740.92 | 7.85 | 327543.39 | 3.63 |
| 2018-02 | 381102.42 | 339433.99 | 12.28 | 308289.34 | 23.62 |
| 2018-03 | 342151.99 | 381102.42 | -10.22 | 279050.37 | 22.61 |
| 2018-04 | 390827.72 | 342151.99 | 14.23 | 334567.58999999997 | 16.82 |
| 2018-05 | 341481.71 | 390827.72 | -12.63 | 311501.99 | 9.62 |
| 2018-06 | 354312.32 | 341481.71 | 3.76 | 292960.25 | 20.94 |
| 2018-07 | 362708.11 | 354312.32 | 2.37 | 312327.07 | 16.13 |
| 2018-08 | 352113.39 | 362708.11 | -2.92 | 299995.6 | 17.37 |
| 2018-09 | 322478.56 | 352113.39 | -8.42 | 321001.19 | 0.46 |
| 2018-10 | 349355.88 | 322478.56 | 8.33 | 318478.87 | 9.7 |
| 2018-11 | 350436.26 | 349355.88 | 0.31 | 334171.61 | 4.87 |
| 2018-12 | 347889.17 | 350436.26 | -0.73 | 314740.92 | 10.53 |
| 2019-01 | 399581.57 | 347889.17 | 14.86 | 339433.99 | 17.72 |
| 2019-02 | 396950.4 | 399581.57 | -0.66 | 381102.42 | 4.16 |
| 2019-03 | 407781.22 | 396950.4 | 2.73 | 342151.99 | 19.18 |
| 2019-04 | 383142.96 | 407781.22 | -6.04 | 390827.72 | -1.97 |
| 2019-05 | 378609.19 | 383142.95999999996 | -1.18 | 341481.71 | 10.87 |
| 2019-06 | 400549.97 | 378609.19 | 5.8 | 354312.32 | 13.05 |
| 2019-07 | 401039.34 | 400549.97 | 0.12 | 362708.11 | 10.57 |
| 2019-08 | 372569.18 | 401039.33999999997 | -7.1 | 352113.39 | 5.81 |
| 2019-09 | 410503.77 | 372569.18 | 10.18 | 322478.56 | 27.3 |
| 2019-10 | 385442.35 | 410503.77 | -6.11 | 349355.88 | 10.33 |
| 2019-11 | 383786.06 | 385442.35 | -0.43 | 350436.26 | 9.52 |
| 2019-12 | 375054.04 | 383786.06 | -2.28 | 347889.17 | 7.81 |

---

### Query: `q13_rolling_averages`

```sql
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
                ROUND(
                    AVG(monthly_cost) OVER (
                        ORDER BY year_month
                        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                    ),
                    2
                ) AS rolling_3m_avg_cost_usd,
                ROUND(
                    AVG(monthly_cost) OVER (
                        ORDER BY year_month
                        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                    ),
                    2
                ) AS rolling_12m_avg_cost_usd
            FROM monthly_cost
            ORDER BY year_month;
```

**Results:**

| year_month | monthly_cost_usd | rolling_3m_avg_cost_usd | rolling_12m_avg_cost_usd |
| --- | --- | --- | --- |
| 2016-01 | 251871.95 | 251871.95 | 251871.95 |
| 2016-02 | 256441.92 | 254156.93 | 254156.93 |
| 2016-03 | 262776.82 | 257030.23 | 257030.23 |
| 2016-04 | 257683.12 | 258967.29 | 257193.45 |
| 2016-05 | 293016.65 | 271158.86 | 264358.09 |
| 2016-06 | 276389.26 | 275696.34 | 266363.29 |
| 2016-07 | 259446.37 | 276284.09 | 265375.16 |
| 2016-08 | 250558.67 | 262131.43 | 263523.09 |
| 2016-09 | 254419.8 | 254808.28 | 262511.62 |
| 2016-10 | 278509.19 | 261162.55 | 264111.38 |
| 2016-11 | 243543.52 | 258824.17 | 262241.57 |
| 2016-12 | 273912.03 | 265321.58 | 263214.11 |
| 2017-01 | 327543.39 | 281666.31 | 269520.06 |
| 2017-02 | 308289.34 | 303248.25 | 273840.68 |
| 2017-03 | 279050.37 | 304961.03 | 275196.81 |
| 2017-04 | 334567.59 | 307302.43 | 281603.85 |
| 2017-05 | 311501.99 | 308373.32 | 283144.29 |
| 2017-06 | 292960.25 | 313009.94 | 284525.21 |
| 2017-07 | 312327.07 | 305596.44 | 288931.93 |
| 2017-08 | 299995.6 | 301760.97 | 293051.68 |
| 2017-09 | 321001.19 | 311107.95 | 298600.13 |
| 2017-10 | 318478.87 | 313158.55 | 301930.93 |
| 2017-11 | 334171.61 | 324550.56 | 309483.27 |
| 2017-12 | 314740.92 | 322463.8 | 312885.68 |
| 2018-01 | 339433.99 | 329448.84 | 313876.57 |
| 2018-02 | 381102.42 | 345092.44 | 319944.32 |
| 2018-03 | 342151.99 | 354229.47 | 325202.79 |
| 2018-04 | 390827.72 | 371360.71 | 329891.14 |
| 2018-05 | 341481.71 | 358153.81 | 332389.45 |
| 2018-06 | 354312.32 | 362207.25 | 337502.12 |
| 2018-07 | 362708.11 | 352834.05 | 341700.54 |
| 2018-08 | 352113.39 | 356377.94 | 346043.69 |
| 2018-09 | 322478.56 | 345766.69 | 346166.8 |
| 2018-10 | 349355.88 | 341315.94 | 348739.89 |
| 2018-11 | 350436.26 | 340756.9 | 350095.27 |
| 2018-12 | 347889.17 | 349227.1 | 352857.63 |
| 2019-01 | 399581.57 | 365969.0 | 357869.92 |
| 2019-02 | 396950.4 | 381473.71 | 359190.59 |
| 2019-03 | 407781.22 | 401437.73 | 364659.69 |
| 2019-04 | 383142.96 | 395958.19 | 364019.3 |
| 2019-05 | 378609.19 | 389844.46 | 367113.25 |
| 2019-06 | 400549.97 | 387434.04 | 370966.39 |
| 2019-07 | 401039.34 | 393399.5 | 374160.66 |
| 2019-08 | 372569.18 | 391386.16 | 375865.31 |
| 2019-09 | 410503.77 | 394704.1 | 383200.74 |
| 2019-10 | 385442.35 | 389505.1 | 386207.95 |
| 2019-11 | 383786.06 | 393244.06 | 388987.1 |
| 2019-12 | 375054.04 | 381427.48 | 391250.84 |

---

### Query: `q14_top_monthly_surges`

```sql
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
```

**Results:**

| year_month | previous_month_cost_usd | current_month_cost_usd | absolute_cost_increase_usd | mom_growth_pct |
| --- | --- | --- | --- | --- |
| 2017-04 | 279050.37 | 334567.59 | 55517.22 | 19.9 |
| 2017-01 | 273912.03 | 327543.39 | 53631.36 | 19.58 |
| 2019-01 | 347889.17 | 399581.57 | 51692.4 | 14.86 |
| 2018-04 | 342151.99 | 390827.72 | 48675.73 | 14.23 |
| 2018-02 | 339433.99 | 381102.42 | 41668.43 | 12.28 |

---

### Query: `q15_top_monthly_drops`

```sql
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
```

**Results:**

| year_month | previous_month_cost_usd | current_month_cost_usd | absolute_cost_decrease_usd | mom_drop_pct |
| --- | --- | --- | --- | --- |
| 2018-05 | 390827.72 | 341481.71 | -49346.01 | -12.63 |
| 2018-03 | 381102.42 | 342151.99 | -38950.43 | -10.22 |
| 2016-11 | 278509.19 | 243543.52 | -34965.67 | -12.55 |
| 2018-09 | 352113.39 | 322478.56 | -29634.83 | -8.42 |
| 2017-03 | 308289.34 | 279050.37 | -29238.97 | -9.48 |

---

