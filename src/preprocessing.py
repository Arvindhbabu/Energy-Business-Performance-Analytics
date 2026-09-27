"""
Data Preprocessing Pipeline Module
Loads raw sheets, standardizes column formats, parses dates, joins dimension
tables (Building Master, Rates), derives calendar features, and prepares
the unified master analytics dataset.
"""

import os
import pandas as pd
import numpy as np


class DataPreprocessor:
    """
    Standardizes and enriches the raw energy dataset with building and rate dimensions.
    """

    def __init__(self, raw_excel_path: str):
        self.raw_excel_path = raw_excel_path
        self.df_raw_ec = None
        self.df_raw_rates = None
        self.df_raw_bm = None
        self.df_processed = None

    def load_raw_data(self):
        """Loads raw sheets from Excel without mutating files."""
        self.df_raw_ec = pd.read_excel(self.raw_excel_path, sheet_name="Energy Consumptions")
        self.df_raw_rates = pd.read_excel(self.raw_excel_path, sheet_name="Rates")
        self.df_raw_bm = pd.read_excel(self.raw_excel_path, sheet_name="Building Master")

    def clean_and_standardize(self) -> pd.DataFrame:
        """Cleans and merges consumption records with dimensions."""
        self.load_raw_data()

        # 1. Standardize column names and types in consumption fact table
        df = self.df_raw_ec.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df['Building'] = df['Building'].astype(str).str.strip()
        df['Water_Consumption'] = df['Water Consumption'].astype(np.int64)
        df['Electricity_Consumption'] = df['Electricity Consumption'].astype(np.int64)
        df['Gas_Consumption'] = df['Gas Consumption'].astype(np.int64)

        # Drop original spaced column names to avoid ambiguity
        df = df.drop(columns=['Water Consumption', 'Electricity Consumption', 'Gas Consumption'])

        # 2. Derive calendar and time dimensions
        df['Year'] = df['Date'].dt.year.astype(int)
        df['Month_Number'] = df['Date'].dt.month.astype(int)
        df['Month_Name'] = df['Date'].dt.strftime('%b') # Jan, Feb...
        df['Month_Full_Name'] = df['Date'].dt.strftime('%B') # January...
        df['Quarter'] = 'Q' + df['Date'].dt.quarter.astype(str)
        df['Year_Month'] = df['Date'].dt.strftime('%Y-%m')

        # 3. Join Building Master metadata
        bm = self.df_raw_bm.copy()
        bm['Building'] = bm['Building'].astype(str).str.strip()
        bm['City'] = bm['City'].astype(str).str.strip()
        bm['Country'] = bm['Country'].astype(str).str.strip()

        df = df.merge(bm, on='Building', how='left')

        # 4. Pivot Rates table to join rates cleanly by Year
        rates = self.df_raw_rates.copy()
        rates['Energy Type'] = rates['Energy Type'].astype(str).str.strip()
        rates_pivot = rates.pivot(index='Year', columns='Energy Type', values='Price Per Unit').reset_index()
        rates_pivot = rates_pivot.rename(columns={
            'Water': 'Water_Rate',
            'Electricity': 'Electricity_Rate',
            'Gas': 'Gas_Rate'
        })

        df = df.merge(rates_pivot, on='Year', how='left')

        # Sort cleanly by Date and Building
        df = df.sort_values(by=['Date', 'Building']).reset_index(drop=True)

        self.df_processed = df
        return df

    def save_processed_data(self, output_dir: str) -> dict:
        """Saves processed data to CSV and Parquet formats."""
        if self.df_processed is None:
            self.clean_and_standardize()

        os.makedirs(output_dir, exist_ok=True)
        csv_path = os.path.join(output_dir, "energy_consumption_processed.csv")
        parquet_path = os.path.join(output_dir, "energy_consumption_processed.parquet")

        self.df_processed.to_csv(csv_path, index=False)
        self.df_processed.to_parquet(parquet_path, index=False)

        print(f"[DataPreprocessor] Processed CSV saved to: {csv_path}")
        print(f"[DataPreprocessor] Processed Parquet saved to: {parquet_path}")

        return {
            "csv_path": csv_path,
            "parquet_path": parquet_path,
            "row_count": len(self.df_processed),
            "column_count": len(self.df_processed.columns),
            "columns": list(self.df_processed.columns)
        }


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    raw_path = os.path.join(project_root, "data", "raw", "Energy Consumption Data.xlsx")
    proc_dir = os.path.join(project_root, "data", "processed")

    preprocessor = DataPreprocessor(raw_path)
    info = preprocessor.save_processed_data(proc_dir)
    print("Preprocessing Complete:", info)
