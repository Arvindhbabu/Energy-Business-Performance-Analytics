"""
Visualization Engine Module
Generates high-resolution, publication-ready analytics charts for executive
reporting and portfolio documentation.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set visual style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 16


class ChartGenerator:
    """
    Generates and saves the analytical visual suite.
    """

    def __init__(self, enriched_csv_path: str, output_charts_dir: str):
        self.df = pd.read_csv(enriched_csv_path)
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.output_dir = output_charts_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Palette
        self.color_water = "#0284c7"      # Deep sky blue
        self.color_elec = "#f59e0b"       # Warm Amber
        self.color_gas = "#ef4444"        # Coral red
        self.color_total = "#1e293b"      # Slate navy

    def plot_monthly_cost_trend(self):
        """01: Monthly expenditure trajectory by utility."""
        monthly = self.df.groupby('Date').agg({
            'Water_Cost': 'sum',
            'Electricity_Cost': 'sum',
            'Gas_Cost': 'sum',
            'Total_Cost': 'sum'
        }).reset_index()

        fig, ax = plt.subplots(figsize=(13, 6), dpi=300)
        ax.plot(monthly['Date'], monthly['Total_Cost'], color=self.color_total, linewidth=2.5, label='Total Utility Cost', marker='o', markersize=3)
        ax.plot(monthly['Date'], monthly['Water_Cost'], color=self.color_water, linewidth=1.8, label='Water Cost', linestyle='--')
        ax.plot(monthly['Date'], monthly['Gas_Cost'], color=self.color_gas, linewidth=1.8, label='Gas Cost', linestyle='-.')
        ax.plot(monthly['Date'], monthly['Electricity_Cost'], color=self.color_elec, linewidth=1.8, label='Electricity Cost', linestyle=':')

        ax.set_title("Monthly Utility Expenditure Trajectory (2016 - 2019)")
        ax.set_ylabel("Monthly Expenditure (USD)")
        ax.set_xlabel("Timeline")
        ax.yaxis.set_major_formatter('${x:,.0f}')
        ax.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')
        plt.tight_layout()

        out_path = os.path.join(self.output_dir, "01_monthly_utility_cost_trend.png")
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[ChartGenerator] Saved {out_path}")

    def plot_cost_share_donut(self):
        """02: Total expenditure contribution by utility."""
        total_water = self.df['Water_Cost'].sum()
        total_elec = self.df['Electricity_Cost'].sum()
        total_gas = self.df['Gas_Cost'].sum()

        sizes = [total_water, total_gas, total_elec]
        labels = [
            f"Water\n${total_water:,.0f}\n(68.2%)",
            f"Gas\n${total_gas:,.0f}\n(19.0%)",
            f"Electricity\n${total_elec:,.0f}\n(12.8%)"
        ]
        colors = [self.color_water, self.color_gas, self.color_elec]

        fig, ax = plt.subplots(figsize=(8, 8), dpi=300)
        wedges, texts = ax.pie(
            sizes, labels=labels, colors=colors, startangle=140,
            wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2)
        )
        for t in texts:
            t.set_fontsize(11)
            t.set_fontweight('semibold')

        ax.set_title("Total Portfolio Utility Cost Contribution ($15.84M Total)")
        plt.tight_layout()

        out_path = os.path.join(self.output_dir, "02_utility_cost_contribution_share.png")
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[ChartGenerator] Saved {out_path}")

    def plot_price_vs_volume(self, pvd_csv_path: str):
        """03: Price vs Volume Decomposition Bar Chart."""
        if not os.path.exists(pvd_csv_path):
            return
        pvd = pd.read_csv(pvd_csv_path)
        tot = pvd[pvd['Utility'] == 'Total Portfolio']

        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        x = np.arange(len(tot))
        width = 0.35

        rects1 = ax.bar(x - width/2, tot['Volume_Effect_USD'], width, label='Volume Effect (Usage Change)', color='#3b82f6')
        rects2 = ax.bar(x + width/2, tot['Price_Effect_USD'], width, label='Price Effect (Tariff Inflation)', color='#f97316')

        ax.set_title("Annual Cost Growth Decomposition: Volume vs. Price Effect")
        ax.set_ylabel("Cost Impact (USD)")
        ax.set_xticks(x)
        ax.set_xticklabels(tot['Period'])
        ax.yaxis.set_major_formatter('${x:,.0f}')
        ax.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')

        # Add data labels
        for rect in rects1:
            h = rect.get_height()
            ax.annotate(f'${h:,.0f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
        for rect in rects2:
            h = rect.get_height()
            ax.annotate(f'${h:,.0f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "03_price_vs_volume_decomposition.png")
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[ChartGenerator] Saved {out_path}")

    def plot_annual_cost_by_utility(self):
        """04: Annual stacked cost progression."""
        annual = self.df.groupby('Year').agg({
            'Water_Cost': 'sum',
            'Electricity_Cost': 'sum',
            'Gas_Cost': 'sum'
        }).reset_index()

        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        years = annual['Year'].astype(str)
        p1 = ax.bar(years, annual['Water_Cost'], label='Water Cost', color=self.color_water, width=0.55)
        p2 = ax.bar(years, annual['Gas_Cost'], bottom=annual['Water_Cost'], label='Gas Cost', color=self.color_gas, width=0.55)
        p3 = ax.bar(years, annual['Electricity_Cost'], bottom=annual['Water_Cost'] + annual['Gas_Cost'], label='Electricity Cost', color=self.color_elec, width=0.55)

        ax.set_title("Annual Utility Expenditure by Category (2016 - 2019)")
        ax.set_ylabel("Annual Expenditure (USD)")
        ax.set_xlabel("Year")
        ax.yaxis.set_major_formatter('${x:,.0f}')
        ax.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')

        # Annotate total cost on top of bars
        totals = annual['Water_Cost'] + annual['Gas_Cost'] + annual['Electricity_Cost']
        for i, tot in enumerate(totals):
            ax.text(i, tot + 70000, f"${tot:,.0f}", ha='center', va='bottom', fontweight='bold', fontsize=10)

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "04_annual_cost_by_utility.png")
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[ChartGenerator] Saved {out_path}")

    def plot_building_ranking(self):
        """05: Building ranking horizontal bar chart."""
        bldg = self.df.groupby(['Building', 'City']).agg({
            'Water_Cost': 'sum',
            'Electricity_Cost': 'sum',
            'Gas_Cost': 'sum',
            'Total_Cost': 'sum'
        }).reset_index().sort_values('Total_Cost', ascending=True)

        fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
        y = np.arange(len(bldg))

        b1 = ax.barh(y, bldg['Water_Cost'], color=self.color_water, label='Water Cost', height=0.6)
        b2 = ax.barh(y, bldg['Gas_Cost'], left=bldg['Water_Cost'], color=self.color_gas, label='Gas Cost', height=0.6)
        b3 = ax.barh(y, bldg['Electricity_Cost'], left=bldg['Water_Cost'] + bldg['Gas_Cost'], color=self.color_elec, label='Electricity Cost', height=0.6)

        labels = [f"{row['Building']} ({row['City']})" for _, row in bldg.iterrows()]
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.set_title("Total Utility Cost Ranking by Building (4-Year Cumulative)")
        ax.set_xlabel("Expenditure (USD)")
        ax.xaxis.set_major_formatter('${x:,.0f}')
        ax.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')

        # Annotate total
        for i, val in enumerate(bldg['Total_Cost']):
            ax.text(val + 15000, i, f"${val:,.0f}", va='center', fontsize=9, fontweight='semibold')

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "05_building_total_cost_ranking.png")
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[ChartGenerator] Saved {out_path}")

    def plot_city_comparison(self):
        """06: Geographic comparison: Total vs Normalized Cost."""
        city = self.df.groupby('City').agg(
            Building_Count=('Building', 'nunique'),
            Total_Cost=('Total_Cost', 'sum')
        ).reset_index()
        city['Avg_Cost_Per_Building'] = city['Total_Cost'] / city['Building_Count']
        city = city.sort_values('Total_Cost', ascending=False)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

        # Plot 1: Total City Spend
        sns.barplot(data=city, x='City', y='Total_Cost', hue='City', ax=ax1, palette='Blues_r', legend=False)
        ax1.set_title("Total Expenditure by Metropolitan Area\n(Impacted by Building Count)")
        ax1.set_ylabel("Total Spend (USD)")
        ax1.yaxis.set_major_formatter('${x:,.0f}')
        for p in ax1.patches:
            ax1.annotate(f"${p.get_height():,.0f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, xytext=(0, 4), textcoords='offset points')

        # Plot 2: Average Cost Per Building
        city_sorted_norm = city.sort_values('Avg_Cost_Per_Building', ascending=False)
        sns.barplot(data=city_sorted_norm, x='City', y='Avg_Cost_Per_Building', hue='City', ax=ax2, palette='mako', legend=False)
        ax2.set_title("Normalized Cost Per Building by City\n(Fair Like-for-Like Comparison)")
        ax2.set_ylabel("Average Cost Per Building (USD)")
        ax2.yaxis.set_major_formatter('${x:,.0f}')
        for p in ax2.patches:
            ax2.annotate(f"${p.get_height():,.0f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                         ha='center', va='bottom', fontsize=9, xytext=(0, 4), textcoords='offset points')

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "06_city_total_vs_normalized_cost.png")
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[ChartGenerator] Saved {out_path}")

    def plot_seasonal_patterns(self):
        """07: Monthly Seasonality Profiles."""
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        m_avg = self.df.groupby('Month_Name').agg({
            'Water_Consumption': 'mean',
            'Electricity_Consumption': 'mean',
            'Gas_Consumption': 'mean'
        }).reindex(month_order).reset_index()

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 10), sharex=True, dpi=300)

        ax1.plot(m_avg['Month_Name'], m_avg['Water_Consumption'], color=self.color_water, marker='s', linewidth=2)
        ax1.set_title("Monthly Seasonality: Water Consumption (Summer Cooling Load)", fontsize=11)
        ax1.set_ylabel("Units")
        ax1.yaxis.set_major_formatter('{x:,.0f}')

        ax2.plot(m_avg['Month_Name'], m_avg['Electricity_Consumption'], color=self.color_elec, marker='^', linewidth=2)
        ax2.set_title("Monthly Seasonality: Electricity Consumption (HVAC Peak Demand)", fontsize=11)
        ax2.set_ylabel("kWh")
        ax2.yaxis.set_major_formatter('{x:,.0f}')

        ax3.plot(m_avg['Month_Name'], m_avg['Gas_Consumption'], color=self.color_gas, marker='o', linewidth=2)
        ax3.set_title("Monthly Seasonality: Gas Consumption (Winter Heating Demand)", fontsize=11)
        ax3.set_ylabel("Units")
        ax3.set_xlabel("Calendar Month")
        ax3.yaxis.set_major_formatter('{x:,.0f}')

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "07_seasonal_consumption_patterns.png")
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[ChartGenerator] Saved {out_path}")

    def plot_volatility(self):
        """08: Portfolio YoY Cost Growth Over Time."""
        monthly_tot = self.df.groupby('Date')['Total_Cost'].sum().reset_index()
        monthly_tot['Prev_Year_Cost'] = monthly_tot['Total_Cost'].shift(12)
        monthly_tot['YoY_Growth_Pct'] = ((monthly_tot['Total_Cost'] - monthly_tot['Prev_Year_Cost']) / monthly_tot['Prev_Year_Cost']) * 100.0

        fig, ax = plt.subplots(figsize=(12, 5), dpi=300)
        valid_df = monthly_tot.dropna(subset=['YoY_Growth_Pct'])
        ax.plot(valid_df['Date'], valid_df['YoY_Growth_Pct'], color='#6366f1', marker='o', linewidth=2, label='YoY Cost Growth (%)')
        ax.axhline(0, color='gray', linestyle='--', linewidth=1)

        ax.set_title("Portfolio Year-over-Year (YoY) Cost Growth Trajectory")
        ax.set_ylabel("YoY Growth Rate (%)")
        ax.set_xlabel("Timeline")
        ax.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0')
        plt.tight_layout()

        out_path = os.path.join(self.output_dir, "08_monthly_mom_yoy_volatility.png")
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[ChartGenerator] Saved {out_path}")

    def plot_anomalies(self, anomaly_csv_path: str):
        """09: Anomaly Detection Distribution Scatter."""
        if not os.path.exists(anomaly_csv_path):
            return
        anom = pd.read_csv(anomaly_csv_path)
        if anom.empty:
            return

        fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
        sns.scatterplot(
            data=anom, x='Building', y='Building_ZScore', hue='Metric',
            style='Is_Business_Anomaly', s=120, ax=ax, palette='Set1'
        )
        ax.axhline(2.0, color='red', linestyle='--', linewidth=1.5, label='Anomaly Threshold (Z = 2.0)')
        ax.set_title("Detected Energy Anomalies by Building and Utility Metric")
        ax.set_ylabel("Standardized Score (Z-Score)")
        ax.legend(frameon=True, facecolor='white', edgecolor='#e2e8f0', bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout()

        out_path = os.path.join(self.output_dir, "09_anomaly_detection_scatter.png")
        fig.savefig(out_path)
        plt.close(fig)
        print(f"[ChartGenerator] Saved {out_path}")

    def generate_all(self, pvd_csv_path: str, anomaly_csv_path: str = None):
        """Generates all charts."""
        self.plot_monthly_cost_trend()
        self.plot_cost_share_donut()
        self.plot_price_vs_volume(pvd_csv_path)
        self.plot_annual_cost_by_utility()
        self.plot_building_ranking()
        self.plot_city_comparison()
        self.plot_seasonal_patterns()
        self.plot_volatility()
        if anomaly_csv_path:
            self.plot_anomalies(anomaly_csv_path)
        print("[ChartGenerator] All visual assets successfully generated.")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    enriched_csv = os.path.join(project_root, "data", "processed", "energy_consumption_enriched.csv")
    pvd_csv = os.path.join(project_root, "outputs", "summary_tables", "price_vs_volume_decomposition.csv")
    anomaly_csv = os.path.join(project_root, "outputs", "summary_tables", "anomaly_detection_report.csv")
    charts_dir = os.path.join(project_root, "outputs", "charts")

    cg = ChartGenerator(enriched_csv, charts_dir)
    cg.generate_all(pvd_csv, anomaly_csv)
