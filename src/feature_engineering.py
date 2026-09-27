"""
Feature Engineering & Utility Cost Analytics Module
Calculates utility-level financial costs, cost shares, growth indicators,
and mathematical Price vs. Volume decomposition.
"""

import os
import pandas as pd
import numpy as np


class FeatureEngineer:
    """
    Enriches processed energy data with cost metrics, growth dynamics,
    and variance decomposition.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def engineer_costs(self) -> pd.DataFrame:
        """
        Calculates individual utility costs and total expenditure.
        Formulas:
          - Water Cost = Water Consumption × Water Rate
          - Electricity Cost = Electricity Consumption × Electricity Rate
          - Gas Cost = Gas Consumption × Gas Rate
          - Total Utility Cost = Water Cost + Electricity Cost + Gas Cost
        """
        df = self.df

        # 1. Cost calculations
        df['Water_Cost'] = df['Water_Consumption'] * df['Water_Rate']
        df['Electricity_Cost'] = df['Electricity_Consumption'] * df['Electricity_Rate']
        df['Gas_Cost'] = df['Gas_Consumption'] * df['Gas_Rate']
        df['Total_Cost'] = df['Water_Cost'] + df['Electricity_Cost'] + df['Gas_Cost']

        # 2. Utility cost shares (%)
        df['Water_Cost_Pct'] = (df['Water_Cost'] / df['Total_Cost']) * 100.0
        df['Electricity_Cost_Pct'] = (df['Electricity_Cost'] / df['Total_Cost']) * 100.0
        df['Gas_Cost_Pct'] = (df['Gas_Cost'] / df['Total_Cost']) * 100.0

        self.df = df
        return df

    def engineer_growth_metrics(self) -> pd.DataFrame:
        """
        Calculates MoM and YoY growth rates per building across all dimensions.
        """
        df = self.df.sort_values(by=['Building', 'Date']).reset_index(drop=True)

        # Building-level lags
        metrics = ['Water_Consumption', 'Electricity_Consumption', 'Gas_Consumption',
                   'Water_Cost', 'Electricity_Cost', 'Gas_Cost', 'Total_Cost']

        for m in metrics:
            # 1-month lag (MoM)
            df[f'{m}_MoM_Prev'] = df.groupby('Building')[m].shift(1)
            df[f'{m}_MoM_Growth_Pct'] = ((df[m] - df[f'{m}_MoM_Prev']) / df[f'{m}_MoM_Prev']) * 100.0

            # 12-month lag (YoY)
            df[f'{m}_YoY_Prev'] = df.groupby('Building')[m].shift(12)
            df[f'{m}_YoY_Growth_Pct'] = ((df[m] - df[f'{m}_YoY_Prev']) / df[f'{m}_YoY_Prev']) * 100.0

            # Rolling 3-month and 12-month moving averages
            df[f'{m}_Rolling3M_Avg'] = df.groupby('Building')[m].transform(lambda s: s.rolling(3, min_periods=1).mean())
            df[f'{m}_Rolling12M_Avg'] = df.groupby('Building')[m].transform(lambda s: s.rolling(12, min_periods=1).mean())

        self.df = df
        return df

    @staticmethod
    def calculate_price_volume_decomposition(df: pd.DataFrame) -> pd.DataFrame:
        """
        Decomposes year-over-year cost changes into Volume Effect vs Price Effect.
        Mathematical Formulation:
          Total Cost Change = Delta Cost = Cost_t - Cost_{t-1}
          Volume Effect = (Q_t - Q_{t-1}) * P_{t-1}
          Price Effect = Q_t * (P_t - P_{t-1})
          Identity: Volume Effect + Price Effect = Delta Cost (100% exact, 0 residual)
        """
        # Aggregate by Year and Utility
        annual_summary = df.groupby('Year').agg({
            'Water_Consumption': 'sum',
            'Electricity_Consumption': 'sum',
            'Gas_Consumption': 'sum',
            'Water_Rate': 'first',
            'Electricity_Rate': 'first',
            'Gas_Rate': 'first',
            'Water_Cost': 'sum',
            'Electricity_Cost': 'sum',
            'Gas_Cost': 'sum',
            'Total_Cost': 'sum'
        }).reset_index()

        years = annual_summary['Year'].tolist()
        records = []

        for i in range(1, len(years)):
            y_curr = years[i]
            y_prev = years[i-1]

            row_curr = annual_summary[annual_summary['Year'] == y_curr].iloc[0]
            row_prev = annual_summary[annual_summary['Year'] == y_prev].iloc[0]

            utilities = [
                ('Water', 'Water_Consumption', 'Water_Rate', 'Water_Cost'),
                ('Electricity', 'Electricity_Consumption', 'Electricity_Rate', 'Electricity_Cost'),
                ('Gas', 'Gas_Consumption', 'Gas_Rate', 'Gas_Cost')
            ]

            tot_vol_eff = 0.0
            tot_price_eff = 0.0
            tot_cost_change = 0.0

            for util_name, q_col, p_col, c_col in utilities:
                q0 = row_prev[q_col]
                q1 = row_curr[q_col]
                p0 = row_prev[p_col]
                p1 = row_curr[p_col]
                c0 = row_prev[c_col]
                c1 = row_curr[c_col]

                delta_cost = c1 - c0
                volume_effect = (q1 - q0) * p0
                price_effect = q1 * (p1 - p0)

                # Verification
                assert np.isclose(volume_effect + price_effect, delta_cost, atol=1e-2), "Decomposition mismatch"

                vol_share = (volume_effect / delta_cost * 100.0) if delta_cost != 0 else 0
                price_share = (price_effect / delta_cost * 100.0) if delta_cost != 0 else 0

                records.append({
                    "Period": f"{y_prev} -> {y_curr}",
                    "Utility": util_name,
                    "Prev_Quantity": q0,
                    "Curr_Quantity": q1,
                    "Delta_Quantity": q1 - q0,
                    "Quantity_Growth_Pct": round(((q1 - q0) / q0) * 100, 2),
                    "Prev_Price": round(p0, 6),
                    "Curr_Price": round(p1, 6),
                    "Price_Growth_Pct": round(((p1 - p0) / p0) * 100, 2),
                    "Prev_Cost": round(c0, 2),
                    "Curr_Cost": round(c1, 2),
                    "Delta_Cost": round(delta_cost, 2),
                    "Cost_Growth_Pct": round((delta_cost / c0) * 100, 2),
                    "Volume_Effect_USD": round(volume_effect, 2),
                    "Price_Effect_USD": round(price_effect, 2),
                    "Volume_Contribution_Pct": round(vol_share, 2),
                    "Price_Contribution_Pct": round(price_share, 2)
                })

                tot_vol_eff += volume_effect
                tot_price_eff += price_effect
                tot_cost_change += delta_cost

            # Portfolio total record
            records.append({
                "Period": f"{y_prev} -> {y_curr}",
                "Utility": "Total Portfolio",
                "Prev_Quantity": None,
                "Curr_Quantity": None,
                "Delta_Quantity": None,
                "Quantity_Growth_Pct": None,
                "Prev_Price": None,
                "Curr_Price": None,
                "Price_Growth_Pct": None,
                "Prev_Cost": round(row_prev['Total_Cost'], 2),
                "Curr_Cost": round(row_curr['Total_Cost'], 2),
                "Delta_Cost": round(tot_cost_change, 2),
                "Cost_Growth_Pct": round((tot_cost_change / row_prev['Total_Cost']) * 100, 2),
                "Volume_Effect_USD": round(tot_vol_eff, 2),
                "Price_Effect_USD": round(tot_price_eff, 2),
                "Volume_Contribution_Pct": round((tot_vol_eff / tot_cost_change) * 100, 2),
                "Price_Contribution_Pct": round((tot_price_eff / tot_cost_change) * 100, 2)
            })

        return pd.DataFrame(records)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    proc_csv = os.path.join(project_root, "data", "processed", "energy_consumption_processed.csv")

    df_proc = pd.read_csv(proc_csv)
    fe = FeatureEngineer(df_proc)
    df_costs = fe.engineer_costs()
    df_growth = fe.engineer_growth_metrics()

    # Save enriched master dataset
    enriched_csv = os.path.join(project_root, "data", "processed", "energy_consumption_enriched.csv")
    df_growth.to_csv(enriched_csv, index=False)
    print(f"[FeatureEngineer] Enriched master dataset saved to: {enriched_csv}")

    # Generate Price vs Volume table
    pvd = FeatureEngineer.calculate_price_volume_decomposition(df_costs)
    pvd_csv = os.path.join(project_root, "outputs", "summary_tables", "price_vs_volume_decomposition.csv")
    pvd.to_csv(pvd_csv, index=False)
    print(f"[FeatureEngineer] Price vs Volume decomposition saved to: {pvd_csv}")
    print("\nPrice vs Volume Decomposition Summary:")
    print(pvd[pvd['Utility'] == 'Total Portfolio'][['Period', 'Delta_Cost', 'Cost_Growth_Pct', 'Volume_Effect_USD', 'Price_Effect_USD', 'Volume_Contribution_Pct', 'Price_Contribution_Pct']])
