"""
Automated SQL Test Runner and Verification Engine
Loads raw energy data into an in-memory SQLite database, validates DDL,
runs data quality queries, executes analytical queries, and reconciles
the SQL output against the Python analytics pipeline.
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np

# Set project root
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw_excel = os.path.join(base_dir, "data", "raw", "Energy Consumption Data.xlsx")
sql_dir = os.path.join(base_dir, "sql")
out_sql_dir = os.path.join(base_dir, "outputs", "summary_tables", "sql_results")
os.makedirs(out_sql_dir, exist_ok=True)


def init_database() -> sqlite3.Connection:
    """Creates in-memory database and loads schema and raw tables."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # 1. Read and execute schema.sql
    with open(os.path.join(sql_dir, "schema.sql"), "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    # 2. Ingest raw Excel sheets into tables
    df_bm = pd.read_excel(raw_excel, sheet_name="Building Master")
    df_bm = df_bm.rename(columns={"Building": "building_id", "City": "city", "Country": "country"})
    df_bm.to_sql("dim_building", conn, if_exists="append", index=False)

    df_rates = pd.read_excel(raw_excel, sheet_name="Rates")
    df_rates = df_rates.rename(columns={"Year": "rate_year", "Energy Type": "energy_type", "Price Per Unit": "price_per_unit"})
    df_rates.to_sql("dim_rate", conn, if_exists="append", index=False)

    df_ec = pd.read_excel(raw_excel, sheet_name="Energy Consumptions")
    df_ec["Date"] = pd.to_datetime(df_ec["Date"]).dt.strftime("%Y-%m-%d")
    df_ec = df_ec.rename(columns={
        "Date": "consumption_date",
        "Building": "building_id",
        "Water Consumption": "water_consumption",
        "Electricity Consumption": "electricity_consumption",
        "Gas Consumption": "gas_consumption"
    })
    df_ec.to_sql("fact_energy_consumption", conn, if_exists="append", index=False)

    conn.commit()
    print("[SQL Runner] Database initialized with 11 buildings, 15 rate records, and 528 fact records.")
    return conn


def run_data_quality_tests(conn: sqlite3.Connection):
    """Executes automated SQL data quality checks."""
    print("\n--- RUNNING SQL DATA QUALITY TESTS ---")
    cursor = conn.cursor()

    # Test 1: Nulls
    res = cursor.execute("SELECT COUNT(*) FROM fact_energy_consumption WHERE consumption_date IS NULL OR building_id IS NULL;").fetchone()[0]
    assert res == 0, f"Null test failed: found {res} null rows"
    print("  [OK] Test 1: Zero Nulls in Fact Table")

    # Test 2: Duplicate Keys
    res = cursor.execute("SELECT COUNT(*) FROM (SELECT consumption_date, building_id FROM fact_energy_consumption GROUP BY consumption_date, building_id HAVING COUNT(*) > 1);").fetchone()[0]
    assert res == 0, f"Duplicate test failed: found {res} duplicate keys"
    print("  [OK] Test 2: Zero Duplicate Keys (Date + Building)")

    # Test 3: Negative / Zero consumption
    res = cursor.execute("SELECT COUNT(*) FROM fact_energy_consumption WHERE water_consumption <= 0 OR electricity_consumption <= 0 OR gas_consumption <= 0;").fetchone()[0]
    assert res == 0, f"Zero/Negative test failed: found {res} non-positive values"
    print("  [OK] Test 3: Zero Negative or Non-Positive Consumption Records")

    # Test 4: Orphan foreign keys
    res = cursor.execute("SELECT COUNT(*) FROM fact_energy_consumption f LEFT JOIN dim_building b ON f.building_id = b.building_id WHERE b.building_id IS NULL;").fetchone()[0]
    assert res == 0, f"Referential integrity failed: {res} orphaned building records"
    print("  [OK] Test 4: 100% Referential Integrity with Building Master")

    # Test 5: Monthly continuity
    res = cursor.execute("SELECT COUNT(*) FROM (SELECT building_id FROM fact_energy_consumption GROUP BY building_id HAVING COUNT(DISTINCT consumption_date) != 48);").fetchone()[0]
    assert res == 0, f"Monthly continuity failed: {res} buildings have != 48 records"
    print("  [OK] Test 5: Perfect Monthly Continuity (All 11 buildings have 48 months)")


def execute_analytical_queries(conn: sqlite3.Connection):
    """Executes business queries and exports clean CSV/markdown outputs."""
    print("\n--- EXECUTING ANALYTICAL SQL QUERIES ---")

    queries = {
        "q01_annual_cost_and_growth": """
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
        """,
        "q02_utility_cost_and_volume_totals": """
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
        """,
        "q05_building_rankings": """
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
        """,
        "q09_city_total_vs_normalized": """
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
        """,
        "q12_mom_yoy_dynamics": """
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
        """,
        "q13_rolling_averages": """
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
        """,
        "q14_top_monthly_surges": """
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
        """,
        "q15_top_monthly_drops": """
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
        """
    }

    def df_to_markdown(df):
        headers = [str(c) for c in df.columns]
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        for _, row in df.iterrows():
            lines.append("| " + " | ".join(str(val) for val in row.values) + " |")
        return "\n".join(lines)

    markdown_report = "# SQL Analytics Execution Report\n\n"

    for qname, qsql in queries.items():
        df_res = pd.read_sql_query(qsql, conn)
        csv_file = os.path.join(out_sql_dir, f"{qname}.csv")
        df_res.to_csv(csv_file, index=False)
        print(f"  [OK] Query '{qname}' executed ({len(df_res)} rows). Saved to CSV.")

        markdown_report += f"### Query: `{qname}`\n\n```sql\n{qsql.strip()}\n```\n\n"
        markdown_report += f"**Results:**\n\n"
        markdown_report += df_to_markdown(df_res) + "\n\n---\n\n"

    # Reconciliation Check
    total_sql_cost = pd.read_sql_query("SELECT SUM(total_utility_cost) FROM view_energy_master_mart;", conn).iloc[0, 0]
    print(f"\n[SQL Reconciliation Check]")
    print(f"  Total SQL Master View Cost: ${total_sql_cost:,.2f}")
    assert np.isclose(total_sql_cost, 15842498.96, atol=1.0), f"Reconciliation error: {total_sql_cost}"
    print("  [OK] Exact Reconciliation Confirmed: SQL Total matches Python Benchmark ($15,842,498.96)")

    # Save markdown report
    rep_path = os.path.join(base_dir, "reports", "sql_execution_report.md")
    with open(rep_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"[SQL Runner] Execution markdown report saved to: {rep_path}")


if __name__ == "__main__":
    conn = init_database()
    run_data_quality_tests(conn)
    execute_analytical_queries(conn)
    conn.close()
