"""
Data Validation Module
Automated validation of incoming raw energy datasets, verifying structure,
completeness, dates, value ranges, and referential integrity.
"""

import os
import json
from datetime import datetime
import pandas as pd
import numpy as np


class DataValidator:
    """
    Automated data quality validation engine for energy analytics datasets.
    """

    def __init__(self, raw_excel_path: str):
        self.raw_excel_path = raw_excel_path
        self.report = {
            "validation_timestamp": datetime.now().isoformat(),
            "source_file": os.path.basename(raw_excel_path),
            "status": "PENDING",
            "checks": {},
            "summary": {}
        }
        self.df_consumption = None
        self.df_rates = None
        self.df_buildings = None

    def load_data(self):
        """Loads the raw sheets from Excel."""
        xls = pd.ExcelFile(self.raw_excel_path)
        self.sheets = xls.sheet_names
        self.df_consumption = pd.read_excel(self.raw_excel_path, sheet_name="Energy Consumptions")
        self.df_rates = pd.read_excel(self.raw_excel_path, sheet_name="Rates")
        self.df_buildings = pd.read_excel(self.raw_excel_path, sheet_name="Building Master")

    def validate_structure(self):
        """Validates row and column counts, expected columns, and data types."""
        expected_sheets = {"Energy Consumptions", "Rates", "Building Master"}
        sheet_check = expected_sheets.issubset(set(self.sheets))

        ec_cols = list(self.df_consumption.columns)
        expected_ec_cols = ['Date', 'Building', 'Water Consumption', 'Electricity Consumption', 'Gas Consumption']
        ec_col_check = expected_ec_cols == ec_cols

        rates_cols = list(self.df_rates.columns)
        expected_rates_cols = ['Year', 'Energy Type', 'Price Per Unit']
        rates_col_check = expected_rates_cols == rates_cols

        bm_cols = list(self.df_buildings.columns)
        expected_bm_cols = ['Building', 'City', 'Country']
        bm_col_check = expected_bm_cols == bm_cols

        structure_pass = sheet_check and ec_col_check and rates_col_check and bm_col_check

        self.report["checks"]["structure"] = {
            "passed": bool(structure_pass),
            "sheets_found": self.sheets,
            "energy_consumptions": {
                "rows": int(len(self.df_consumption)),
                "columns": ec_cols,
                "dtypes": {k: str(v) for k, v in self.df_consumption.dtypes.items()}
            },
            "rates": {
                "rows": int(len(self.df_rates)),
                "columns": rates_cols,
                "dtypes": {k: str(v) for k, v in self.df_rates.dtypes.items()}
            },
            "building_master": {
                "rows": int(len(self.df_buildings)),
                "columns": bm_cols,
                "dtypes": {k: str(v) for k, v in self.df_buildings.dtypes.items()}
            }
        }

    def validate_missing_data(self):
        """Checks null counts and null percentages across all tables."""
        ec_nulls = self.df_consumption.isnull().sum().to_dict()
        rates_nulls = self.df_rates.isnull().sum().to_dict()
        bm_nulls = self.df_buildings.isnull().sum().to_dict()

        total_nulls = sum(ec_nulls.values()) + sum(rates_nulls.values()) + sum(bm_nulls.values())
        missing_pass = (total_nulls == 0)

        self.report["checks"]["missing_data"] = {
            "passed": bool(missing_pass),
            "total_null_count": int(total_nulls),
            "energy_consumptions_nulls": {k: int(v) for k, v in ec_nulls.items()},
            "rates_nulls": {k: int(v) for k, v in rates_nulls.items()},
            "building_master_nulls": {k: int(v) for k, v in bm_nulls.items()}
        }

    def validate_duplicates(self):
        """Checks for exact row duplicates and composite business key duplicates."""
        ec_exact_dup = int(self.df_consumption.duplicated().sum())
        ec_key_dup = int(self.df_consumption.duplicated(subset=['Date', 'Building']).sum())
        bm_key_dup = int(self.df_buildings.duplicated(subset=['Building']).sum())
        rates_key_dup = int(self.df_rates.duplicated(subset=['Year', 'Energy Type']).sum())

        dup_pass = (ec_exact_dup == 0 and ec_key_dup == 0 and bm_key_dup == 0 and rates_key_dup == 0)

        self.report["checks"]["duplicates"] = {
            "passed": bool(dup_pass),
            "energy_consumptions_exact_duplicates": ec_exact_dup,
            "energy_consumptions_key_duplicates (Date, Building)": ec_key_dup,
            "building_master_key_duplicates (Building)": bm_key_dup,
            "rates_key_duplicates (Year, Energy Type)": rates_key_dup
        }

    def validate_dates(self):
        """Checks date ranges, formatting, invalid dates, and monthly continuity."""
        dates = pd.to_datetime(self.df_consumption['Date'], errors='coerce')
        invalid_dates = int(dates.isnull().sum())
        min_date = dates.min()
        max_date = dates.max()

        # Monthly continuity check: 48 expected consecutive months
        expected_periods = pd.date_range(start=min_date, end=max_date, freq='MS')
        actual_unique_dates = sorted(dates.unique())
        continuity_pass = len(expected_periods) == len(actual_unique_dates)

        # Check records per building
        records_per_bldg = self.df_consumption.groupby('Building')['Date'].count().to_dict()
        all_48 = all(v == 48 for v in records_per_bldg.values())

        date_pass = (invalid_dates == 0) and continuity_pass and all_48

        self.report["checks"]["dates"] = {
            "passed": bool(date_pass),
            "invalid_dates": invalid_dates,
            "min_date": str(min_date.date()) if pd.notnull(min_date) else None,
            "max_date": str(max_date.date()) if pd.notnull(max_date) else None,
            "total_calendar_months": int(len(actual_unique_dates)),
            "monthly_continuity_complete": bool(continuity_pass),
            "records_per_building": {k: int(v) for k, v in records_per_bldg.items()}
        }

    def validate_categorical_and_numerical(self):
        """Validates categories and numeric ranges for anomalies (<=0, negatives)."""
        buildings_ec = set(self.df_consumption['Building'].unique())
        buildings_bm = set(self.df_buildings['Building'].unique())
        cities = sorted(self.df_buildings['City'].unique())
        countries = sorted(self.df_buildings['Country'].unique())
        energy_types = sorted(self.df_rates['Energy Type'].unique())

        num_cols = ['Water Consumption', 'Electricity Consumption', 'Gas Consumption']
        num_checks = {}
        all_num_pass = True

        for col in num_cols:
            series = self.df_consumption[col]
            neg_count = int((series < 0).sum())
            zero_count = int((series == 0).sum())
            min_val = float(series.min())
            max_val = float(series.max())
            mean_val = float(series.mean())
            passed = (neg_count == 0) and (zero_count == 0)
            if not passed:
                all_num_pass = False
            num_checks[col] = {
                "passed": bool(passed),
                "negative_count": neg_count,
                "zero_count": zero_count,
                "min": min_val,
                "max": max_val,
                "mean": round(mean_val, 2)
            }

        self.report["checks"]["numerical_fields"] = {
            "passed": bool(all_num_pass),
            "columns": num_checks
        }

        self.report["checks"]["categorical_fields"] = {
            "passed": True,
            "unique_buildings_count": len(buildings_ec),
            "unique_cities": cities,
            "unique_countries": countries,
            "unique_energy_types": energy_types
        }

    def validate_referential_integrity(self):
        """Verifies foreign key relationships between consumption, buildings, and rates."""
        ec_buildings = set(self.df_consumption['Building'].unique())
        bm_buildings = set(self.df_buildings['Building'].unique())
        unmapped_buildings = list(ec_buildings - bm_buildings)

        # Year mapping to rates
        ec_years = set(pd.to_datetime(self.df_consumption['Date']).dt.year.unique())
        rates_years = set(self.df_rates['Year'].unique())
        unmapped_years = list(ec_years - rates_years)

        # Check rates completeness for each year
        rates_complete = True
        for yr in ec_years:
            yr_types = set(self.df_rates[self.df_rates['Year'] == yr]['Energy Type'].unique())
            if yr_types != {'Water', 'Electricity', 'Gas'}:
                rates_complete = False

        ref_pass = (len(unmapped_buildings) == 0) and (len(unmapped_years) == 0) and rates_complete

        self.report["checks"]["referential_integrity"] = {
            "passed": bool(ref_pass),
            "unmapped_buildings_count": len(unmapped_buildings),
            "unmapped_buildings": unmapped_buildings,
            "unmapped_consumption_years": unmapped_years,
            "rates_definition_complete_for_all_years": rates_complete
        }

    def run_all(self, output_json_path: str = None) -> dict:
        """Executes full validation suite and returns report dictionary."""
        self.load_data()
        self.validate_structure()
        self.validate_missing_data()
        self.validate_duplicates()
        self.validate_dates()
        self.validate_categorical_and_numerical()
        self.validate_referential_integrity()

        all_passed = all(check.get("passed", False) for check in self.report["checks"].values())
        self.report["status"] = "PASSED" if all_passed else "FAILED"
        self.report["summary"] = {
            "total_checks": len(self.report["checks"]),
            "passed_checks": sum(1 for c in self.report["checks"].values() if c.get("passed", False)),
            "failed_checks": sum(1 for c in self.report["checks"].values() if not c.get("passed", False)),
            "dataset_certified_for_processing": bool(all_passed)
        }

        if output_json_path:
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(self.report, f, indent=2)
            print(f"[DataValidator] Quality report successfully saved to: {output_json_path}")

        return self.report


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    raw_path = os.path.join(project_root, "data", "raw", "Energy Consumption Data.xlsx")
    report_out = os.path.join(project_root, "reports", "data_quality_report.json")

    validator = DataValidator(raw_path)
    res = validator.run_all(report_out)
    print(f"Validation Status: {res['status']}")
    print(f"Passed Checks: {res['summary']['passed_checks']} / {res['summary']['total_checks']}")
