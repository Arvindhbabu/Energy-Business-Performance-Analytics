-- ==============================================================================
-- DATA QUALITY & INTEGRITY VALIDATION SUITE (SQL)
-- Automated verification queries to enforce data governance standards.
-- ==============================================================================

-- 1. Check for NULL or Invalid Fields in Fact Table
-- Expected: 0 rows returned
SELECT
    COUNT(*) AS null_record_count
FROM fact_energy_consumption
WHERE consumption_date IS NULL
   OR building_id IS NULL
   OR water_consumption IS NULL
   OR electricity_consumption IS NULL
   OR gas_consumption IS NULL;

-- 2. Check for Duplicate Composite Business Keys (Date + Building)
-- Expected: 0 rows returned
SELECT
    consumption_date,
    building_id,
    COUNT(*) AS occurrence_count
FROM fact_energy_consumption
GROUP BY consumption_date, building_id
HAVING COUNT(*) > 1;

-- 3. Check for Zero or Negative Consumption Anomalies
-- Expected: 0 rows returned
SELECT
    consumption_id,
    consumption_date,
    building_id,
    water_consumption,
    electricity_consumption,
    gas_consumption
FROM fact_energy_consumption
WHERE water_consumption <= 0
   OR electricity_consumption <= 0
   OR gas_consumption <= 0;

-- 4. Referential Integrity: Orphaned Buildings in Fact Table
-- Expected: 0 rows returned
SELECT DISTINCT
    f.building_id
FROM fact_energy_consumption f
LEFT JOIN dim_building b ON f.building_id = b.building_id
WHERE b.building_id IS NULL;

-- 5. Referential Integrity: Unmapped Consumption Years in Rates Table
-- Expected: 0 rows returned
SELECT DISTINCT
    CAST(strftime('%Y', f.consumption_date) AS INT) AS missing_year
FROM fact_energy_consumption f
LEFT JOIN dim_rate r ON CAST(strftime('%Y', f.consumption_date) AS INT) = r.rate_year
WHERE r.rate_year IS NULL;

-- 6. Completeness: Verify Monthly Continuity (Exactly 48 Months per Building)
-- Expected: 11 rows returned, all with record_count = 48
SELECT
    building_id,
    COUNT(DISTINCT consumption_date) AS record_count,
    MIN(consumption_date) AS min_date,
    MAX(consumption_date) AS max_date,
    CASE WHEN COUNT(DISTINCT consumption_date) = 48 THEN 'PASSED' ELSE 'FAILED' END AS audit_status
FROM fact_energy_consumption
GROUP BY building_id
ORDER BY building_id;
