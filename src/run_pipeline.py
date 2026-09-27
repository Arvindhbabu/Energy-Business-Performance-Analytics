"""
End-to-End Analytics Pipeline Orchestrator
Executes data validation, preprocessing, feature engineering, KPI calculations,
anomaly detection, and chart rendering in a single reproducible workflow.
"""

import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from src.data_validation import DataValidator
from src.preprocessing import DataPreprocessor
from src.feature_engineering import FeatureEngineer
from src.kpi_analysis import KPIAnalyzer
from src.anomaly_detection import AnomalyDetector
from src.generate_charts import ChartGenerator


def run_pipeline():
    start_time = time.time()
    print("=" * 70)
    print("ENERGY CONSUMPTION & BUSINESS PERFORMANCE ANALYTICS PIPELINE")
    print("=" * 70)

    # 0. Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_excel = os.path.join(base_dir, "data", "raw", "Energy Consumption Data.xlsx")
    proc_dir = os.path.join(base_dir, "data", "processed")
    reports_dir = os.path.join(base_dir, "reports")
    summary_dir = os.path.join(base_dir, "outputs", "summary_tables")
    charts_dir = os.path.join(base_dir, "outputs", "charts")

    # Step 1: Data Validation
    print("\n[STEP 1/6] Running Automated Data Validation...")
    validator = DataValidator(raw_excel)
    val_report_path = os.path.join(reports_dir, "data_quality_report.json")
    val_res = validator.run_all(val_report_path)
    if val_res["status"] != "PASSED":
        print(f"[FAIL] Data Validation Failed: {val_res['summary']}")
        sys.exit(1)
    print(f"[OK] Data Validation Passed ({val_res['summary']['passed_checks']}/{val_res['summary']['total_checks']} checks)")

    # Step 2: Data Preprocessing
    print("\n[STEP 2/6] Preprocessing and Standardizing Master Dataset...")
    preprocessor = DataPreprocessor(raw_excel)
    proc_info = preprocessor.save_processed_data(proc_dir)
    print(f"[OK] Master Processed Data Created ({proc_info['row_count']} rows, {proc_info['column_count']} columns)")

    # Step 3: Feature Engineering & Cost Analytics
    print("\n[STEP 3/6] Engineering Utility Costs and Price vs. Volume Decomposition...")
    df_proc = pd.read_csv(proc_info["csv_path"])
    fe = FeatureEngineer(df_proc)
    df_costs = fe.engineer_costs()
    df_growth = fe.engineer_growth_metrics()

    enriched_csv = os.path.join(proc_dir, "energy_consumption_enriched.csv")
    df_growth.to_csv(enriched_csv, index=False)

    pvd_df = FeatureEngineer.calculate_price_volume_decomposition(df_costs)
    pvd_csv = os.path.join(summary_dir, "price_vs_volume_decomposition.csv")
    pvd_df.to_csv(pvd_csv, index=False)
    print(f"[OK] Enriched Data and Price vs. Volume Decomposition Generated")

    # Step 4: Business KPI Framework
    print("\n[STEP 4/6] Computing Portfolio, Building, and Geographic KPIs...")
    kpi = KPIAnalyzer(df_growth)
    port_kpis = kpi.compute_portfolio_kpis()
    import json
    with open(os.path.join(summary_dir, "portfolio_kpis.json"), "w") as f:
        json.dump(port_kpis, f, indent=2)

    kpi.compute_annual_growth_kpis().to_csv(os.path.join(summary_dir, "annual_growth_kpis.csv"), index=False)
    kpi.compute_building_kpis().to_csv(os.path.join(summary_dir, "building_kpis.csv"), index=False)
    kpi.compute_geographic_kpis().to_csv(os.path.join(summary_dir, "geographic_kpis.csv"), index=False)
    print(f"[OK] Business KPI Summary Tables Generated")

    # Step 5: Anomaly Detection
    print("\n[STEP 5/6] Executing Statistical & Operational Anomaly Detection...")
    detector = AnomalyDetector(df_growth)
    iqr_res = detector.detect_iqr_outliers()
    with open(os.path.join(summary_dir, "iqr_outlier_summary.json"), "w") as f:
        json.dump(iqr_res, f, indent=2)

    anomalies_df = detector.classify_business_anomalies(z_threshold=2.0)
    anom_csv = os.path.join(summary_dir, "anomaly_detection_report.csv")
    anomalies_df.to_csv(anom_csv, index=False)
    print(f"[OK] Anomaly Detection Complete ({len(anomalies_df)} anomalies categorized)")

    # Step 6: Publication Chart Rendering
    print("\n[STEP 6/6] Rendering High-Resolution Analytics Visuals...")
    cg = ChartGenerator(enriched_csv, charts_dir)
    cg.generate_all(pvd_csv, anom_csv)
    print(f"[OK] Publication Visuals Rendered in: {charts_dir}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    print(f"Total Portfolio Spend: ${port_kpis['total_portfolio_cost_usd']:,.2f}")
    print(f"Water Cost Share: {port_kpis['utility_cost_breakdown']['water_cost_pct']}%")
    print(f"Electricity Cost Share: {port_kpis['utility_cost_breakdown']['electricity_cost_pct']}%")
    print(f"Gas Cost Share: {port_kpis['utility_cost_breakdown']['gas_cost_pct']}%")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()
