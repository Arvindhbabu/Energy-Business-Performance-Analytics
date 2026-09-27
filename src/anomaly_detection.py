"""
Anomaly Detection Module
Transparent statistical anomaly and operational outlier detection using
IQR (Interquartile Range) and Z-score methods, distinguishing statistical
outliers from legitimate business seasonality.
"""

import os
import pandas as pd
import numpy as np


class AnomalyDetector:
    """
    Identifies statistical outliers and operational anomalies across energy metrics.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def detect_iqr_outliers(self) -> dict:
        """
        Evaluates Tukey's Fences (IQR method) across all numeric variables.
        """
        metrics = ['Water_Consumption', 'Electricity_Consumption', 'Gas_Consumption', 'Total_Cost']
        summary = {}

        for m in metrics:
            q1 = float(self.df[m].quantile(0.25))
            q3 = float(self.df[m].quantile(0.75))
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            outliers = self.df[(self.df[m] < lower) | (self.df[m] > upper)]

            summary[m] = {
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "iqr": round(iqr, 2),
                "lower_bound": round(lower, 2),
                "upper_bound": round(upper, 2),
                "outlier_count": len(outliers),
                "min_value": float(self.df[m].min()),
                "max_value": float(self.df[m].max())
            }

        return summary

    def detect_zscore_outliers(self, threshold: float = 2.0) -> pd.DataFrame:
        """
        Detects building-normalized Z-score anomalies:
          Z = (X - Mean_bldg) / Std_bldg
        Flags any observation with |Z| > threshold.
        """
        df = self.df.copy()
        metrics = ['Water_Consumption', 'Electricity_Consumption', 'Gas_Consumption', 'Total_Cost']

        for m in metrics:
            mean_b = df.groupby('Building')[m].transform('mean')
            std_b = df.groupby('Building')[m].transform('std')
            df[f'{m}_ZScore'] = (df[m] - mean_b) / std_b
            df[f'{m}_Is_Outlier'] = df[f'{m}_ZScore'].abs() > threshold

        return df

    def classify_business_anomalies(self, z_threshold: float = 2.0) -> pd.DataFrame:
        """
        Distinguishes pure statistical distribution tails from business-actionable anomalies.
        Business Rules:
          - Gas Consumption: Expected peak in winter (heating). An off-season peak (May-Sep)
            exceeding 2 sigma represents an operational defect (e.g. heating stuck on).
          - Water Consumption: Expected peak in summer (cooling). An unseasonal spike in
            winter represents suspected leaks.
          - Electricity: Summer AC cooling peaks vs winter baselines.
        """
        df = self.detect_zscore_outliers(threshold=z_threshold)

        cols = [
            "Date", "Year_Month", "Building", "City", "Metric", "Value",
            "Building_ZScore", "Anomaly_Type", "Classification", "Is_Business_Anomaly"
        ]
        anomaly_records = []

        winter_months = [11, 12, 1, 2]
        summer_months = [6, 7, 8]

        for _, row in df.iterrows():
            month = int(row['Month_Number'])

            # 1. Gas anomaly check
            if row['Gas_Consumption_ZScore'] > z_threshold:
                if month in winter_months:
                    classif = "Seasonal Peak Heating Demand (Expected Operational Seasonality)"
                    is_biz = False
                else:
                    classif = "Off-Season Gas Spike (Suspected Boiler Fault / Space Heating Overrun)"
                    is_biz = True

                anomaly_records.append({
                    "Date": str(row['Date'])[:10],
                    "Year_Month": row['Year_Month'],
                    "Building": row['Building'],
                    "City": row['City'],
                    "Metric": "Gas Consumption",
                    "Value": float(row['Gas_Consumption']),
                    "Building_ZScore": round(float(row['Gas_Consumption_ZScore']), 2),
                    "Anomaly_Type": "High Spike",
                    "Classification": classif,
                    "Is_Business_Anomaly": is_biz
                })

            # 2. Water anomaly check
            if row['Water_Consumption_ZScore'] > z_threshold:
                if month in summer_months:
                    classif = "Summer Cooling Tower Water Evaporation (Normal Seasonal Peak)"
                    is_biz = False
                else:
                    classif = "Unseasonal Water Spike (Suspected Plumbing Leak / Facility Surge)"
                    is_biz = True

                anomaly_records.append({
                    "Date": str(row['Date'])[:10],
                    "Year_Month": row['Year_Month'],
                    "Building": row['Building'],
                    "City": row['City'],
                    "Metric": "Water Consumption",
                    "Value": float(row['Water_Consumption']),
                    "Building_ZScore": round(float(row['Water_Consumption_ZScore']), 2),
                    "Anomaly_Type": "High Spike",
                    "Classification": classif,
                    "Is_Business_Anomaly": is_biz
                })

            # 3. Electricity anomaly check
            if row['Electricity_Consumption_ZScore'] > z_threshold:
                if month in summer_months:
                    classif = "Peak Summer Air Conditioning Load (Normal Chiller Seasonality)"
                    is_biz = False
                else:
                    classif = "Unseasonal Electricity Spike (Unscheduled IT/Lighting Load)"
                    is_biz = True

                anomaly_records.append({
                    "Date": str(row['Date'])[:10],
                    "Year_Month": row['Year_Month'],
                    "Building": row['Building'],
                    "City": row['City'],
                    "Metric": "Electricity Consumption",
                    "Value": float(row['Electricity_Consumption']),
                    "Building_ZScore": round(float(row['Electricity_Consumption_ZScore']), 2),
                    "Anomaly_Type": "High Spike",
                    "Classification": classif,
                    "Is_Business_Anomaly": is_biz
                })

            # 4. Total Cost anomaly check
            if row['Total_Cost_ZScore'] > z_threshold:
                anomaly_records.append({
                    "Date": str(row['Date'])[:10],
                    "Year_Month": row['Year_Month'],
                    "Building": row['Building'],
                    "City": row['City'],
                    "Metric": "Total Utility Cost",
                    "Value": round(float(row['Total_Cost']), 2),
                    "Building_ZScore": round(float(row['Total_Cost_ZScore']), 2),
                    "Anomaly_Type": "High Expenditure Spike",
                    "Classification": "Combined Rate & Consumption Cost Outlier",
                    "Is_Business_Anomaly": True
                })

        res_df = pd.DataFrame(anomaly_records)
        if res_df.empty:
            res_df = pd.DataFrame(columns=cols)
        return res_df


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    enriched_csv = os.path.join(project_root, "data", "processed", "energy_consumption_enriched.csv")
    out_dir = os.path.join(project_root, "outputs", "summary_tables")

    df_enrich = pd.read_csv(enriched_csv)
    detector = AnomalyDetector(df_enrich)

    # 1. IQR Summary
    iqr_res = detector.detect_iqr_outliers()
    import json
    with open(os.path.join(out_dir, "iqr_outlier_summary.json"), "w") as f:
        json.dump(iqr_res, f, indent=2)

    # 2. Classified Business Anomalies
    anomalies_df = detector.classify_business_anomalies(z_threshold=2.0)
    anomalies_path = os.path.join(out_dir, "anomaly_detection_report.csv")
    anomalies_df.to_csv(anomalies_path, index=False)

    print(f"[AnomalyDetector] Anomaly detection complete. Total records flagged (Z > 2.0): {len(anomalies_df)}")
    if not anomalies_df.empty:
        biz_count = anomalies_df['Is_Business_Anomaly'].sum()
        print(f"[AnomalyDetector] Actionable Business Anomalies: {biz_count}")
        print(anomalies_df.head(10)[['Date', 'Building', 'Metric', 'Building_ZScore', 'Classification']])
