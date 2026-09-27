"""
Business KPI Framework Module
Calculates enterprise-wide, utility-level, building-level, and geographic KPIs
for executive performance monitoring.
"""

import os
import json
import pandas as pd
import numpy as np


class KPIAnalyzer:
    """
    Computes standard business performance indicators across multiple analytical grains.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def compute_portfolio_kpis(self) -> dict:
        """Computes top-level portfolio KPIs."""
        df = self.df
        total_cost = float(df['Total_Cost'].sum())
        water_cost = float(df['Water_Cost'].sum())
        elec_cost = float(df['Electricity_Cost'].sum())
        gas_cost = float(df['Gas_Cost'].sum())

        water_vol = int(df['Water_Consumption'].sum())
        elec_vol = int(df['Electricity_Consumption'].sum())
        gas_vol = int(df['Gas_Consumption'].sum())

        months_count = df['Year_Month'].nunique() # 48
        bldg_count = df['Building'].nunique() # 11

        monthly_costs = df.groupby('Year_Month')['Total_Cost'].sum()
        peak_month = monthly_costs.idxmax()
        peak_monthly_cost = float(monthly_costs.max())
        min_month = monthly_costs.idxmin()
        min_monthly_cost = float(monthly_costs.min())

        kpis = {
            "total_portfolio_cost_usd": round(total_cost, 2),
            "average_monthly_portfolio_cost_usd": round(total_cost / months_count, 2),
            "average_monthly_building_cost_usd": round(total_cost / (months_count * bldg_count), 2),
            "peak_month": {
                "year_month": peak_month,
                "cost_usd": round(peak_monthly_cost, 2)
            },
            "min_month": {
                "year_month": min_month,
                "cost_usd": round(min_monthly_cost, 2)
            },
            "utility_cost_breakdown": {
                "water_cost_usd": round(water_cost, 2),
                "water_cost_pct": round((water_cost / total_cost) * 100, 2),
                "electricity_cost_usd": round(elec_cost, 2),
                "electricity_cost_pct": round((elec_cost / total_cost) * 100, 2),
                "gas_cost_usd": round(gas_cost, 2),
                "gas_cost_pct": round((gas_cost / total_cost) * 100, 2)
            },
            "total_volume_breakdown": {
                "total_water_consumption_units": water_vol,
                "total_electricity_consumption_kwh": elec_vol,
                "total_gas_consumption_units": gas_vol,
                "average_monthly_water_per_building": round(water_vol / (months_count * bldg_count), 1),
                "average_monthly_electricity_per_building": round(elec_vol / (months_count * bldg_count), 1),
                "average_monthly_gas_per_building": round(gas_vol / (months_count * bldg_count), 1)
            }
        }
        return kpis

    def compute_annual_growth_kpis(self) -> pd.DataFrame:
        """Computes Year-over-Year (YoY) annual portfolio growth."""
        annual = self.df.groupby('Year').agg({
            'Total_Cost': 'sum',
            'Water_Cost': 'sum',
            'Electricity_Cost': 'sum',
            'Gas_Cost': 'sum',
            'Water_Consumption': 'sum',
            'Electricity_Consumption': 'sum',
            'Gas_Consumption': 'sum'
        }).reset_index()

        annual['Total_Cost_YoY_Growth_Pct'] = annual['Total_Cost'].pct_change() * 100.0
        annual['Water_Cost_YoY_Growth_Pct'] = annual['Water_Cost'].pct_change() * 100.0
        annual['Electricity_Cost_YoY_Growth_Pct'] = annual['Electricity_Cost'].pct_change() * 100.0
        annual['Gas_Cost_YoY_Growth_Pct'] = annual['Gas_Cost'].pct_change() * 100.0

        annual['Water_Vol_YoY_Growth_Pct'] = annual['Water_Consumption'].pct_change() * 100.0
        annual['Electricity_Vol_YoY_Growth_Pct'] = annual['Electricity_Consumption'].pct_change() * 100.0
        annual['Gas_Vol_YoY_Growth_Pct'] = annual['Gas_Consumption'].pct_change() * 100.0

        return annual.round(2)

    def compute_building_kpis(self) -> pd.DataFrame:
        """Computes building-level KPIs, ranking, and utility cost mix."""
        bldg = self.df.groupby(['Building', 'City']).agg({
            'Total_Cost': 'sum',
            'Water_Cost': 'sum',
            'Electricity_Cost': 'sum',
            'Gas_Cost': 'sum',
            'Water_Consumption': 'sum',
            'Electricity_Consumption': 'sum',
            'Gas_Consumption': 'sum'
        }).reset_index()

        months_per_bldg = 48
        bldg['Avg_Monthly_Cost'] = bldg['Total_Cost'] / months_per_bldg
        bldg['Water_Cost_Share_Pct'] = (bldg['Water_Cost'] / bldg['Total_Cost']) * 100.0
        bldg['Electricity_Cost_Share_Pct'] = (bldg['Electricity_Cost'] / bldg['Total_Cost']) * 100.0
        bldg['Gas_Cost_Share_Pct'] = (bldg['Gas_Cost'] / bldg['Total_Cost']) * 100.0

        # Ranks
        bldg['Cost_Rank'] = bldg['Total_Cost'].rank(ascending=False, method='min').astype(int)

        # Calculate 2016 to 2019 CAGR / Total Growth per building
        piv = self.df.pivot_table(index='Building', columns='Year', values='Total_Cost', aggfunc='sum')
        bldg['Cost_2016'] = bldg['Building'].map(piv[2016])
        bldg['Cost_2019'] = bldg['Building'].map(piv[2019])
        bldg['4Y_Cost_Growth_Pct'] = ((bldg['Cost_2019'] - bldg['Cost_2016']) / bldg['Cost_2016']) * 100.0

        return bldg.sort_values(by='Cost_Rank').round(2)

    def compute_geographic_kpis(self) -> pd.DataFrame:
        """
        Computes city-level KPIs distinguishing Total Spend from Normalized Cost Per Building.
        """
        city = self.df.groupby('City').agg({
            'Building': 'nunique',
            'Total_Cost': 'sum',
            'Water_Cost': 'sum',
            'Electricity_Cost': 'sum',
            'Gas_Cost': 'sum',
            'Water_Consumption': 'sum',
            'Electricity_Consumption': 'sum',
            'Gas_Consumption': 'sum'
        }).rename(columns={'Building': 'Building_Count'}).reset_index()

        city['Avg_Cost_Per_Building'] = city['Total_Cost'] / city['Building_Count']
        city['Avg_Monthly_Cost_Per_Building'] = city['Avg_Cost_Per_Building'] / 48.0

        city['Avg_Water_Consumption_Per_Building'] = city['Water_Consumption'] / city['Building_Count']
        city['Avg_Electricity_Consumption_Per_Building'] = city['Electricity_Consumption'] / city['Building_Count']
        city['Avg_Gas_Consumption_Per_Building'] = city['Gas_Consumption'] / city['Building_Count']

        city['Total_Cost_Rank'] = city['Total_Cost'].rank(ascending=False, method='min').astype(int)
        city['Normalized_Cost_Per_Building_Rank'] = city['Avg_Cost_Per_Building'].rank(ascending=False, method='min').astype(int)

        return city.sort_values(by='Total_Cost_Rank').round(2)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    enriched_csv = os.path.join(project_root, "data", "processed", "energy_consumption_enriched.csv")
    out_dir = os.path.join(project_root, "outputs", "summary_tables")
    os.makedirs(out_dir, exist_ok=True)

    df_enrich = pd.read_csv(enriched_csv)
    analyzer = KPIAnalyzer(df_enrich)

    # 1. Overall Portfolio KPIs
    port_kpis = analyzer.compute_portfolio_kpis()
    with open(os.path.join(out_dir, "portfolio_kpis.json"), "w") as f:
        json.dump(port_kpis, f, indent=2)

    # 2. Annual Growth KPIs
    annual_df = analyzer.compute_annual_growth_kpis()
    annual_df.to_csv(os.path.join(out_dir, "annual_growth_kpis.csv"), index=False)

    # 3. Building KPIs
    bldg_df = analyzer.compute_building_kpis()
    bldg_df.to_csv(os.path.join(out_dir, "building_kpis.csv"), index=False)

    # 4. Geographic KPIs
    geo_df = analyzer.compute_geographic_kpis()
    geo_df.to_csv(os.path.join(out_dir, "geographic_kpis.csv"), index=False)

    print("[KPIAnalyzer] All KPI summary tables generated and saved.")
