import os
import pandas as pd

base_dir = r"c:\Users\varav\Documents\Projects\Data Analytics Intern Edunet\energy-business-analytics"
raw_excel = os.path.join(base_dir, "data", "raw", "Energy Consumption Data.xlsx")
clean_dir = os.path.join(base_dir, "outputs", "cleaned_data")
os.makedirs(clean_dir, exist_ok=True)

# 1. Dim Building
df_bm = pd.read_excel(raw_excel, sheet_name="Building Master")
df_bm.to_csv(os.path.join(clean_dir, "dim_building.csv"), index=False)

# 2. Dim Rate
df_rates = pd.read_excel(raw_excel, sheet_name="Rates")
df_rates.to_csv(os.path.join(clean_dir, "dim_rate.csv"), index=False)

# 3. Dim Calendar
dates = pd.date_range(start="2016-01-01", end="2020-12-01", freq="MS")
df_cal = pd.DataFrame({
    "Date": dates,
    "Year": dates.year,
    "Month_Number": dates.month,
    "Month_Name": dates.strftime("%b"),
    "Month_Full_Name": dates.strftime("%B"),
    "Quarter": "Q" + dates.quarter.astype(str),
    "Year_Quarter": dates.year.astype(str) + "-Q" + dates.quarter.astype(str),
    "Year_Month": dates.strftime("%Y-%m")
})
df_cal.to_csv(os.path.join(clean_dir, "dim_calendar.csv"), index=False)

# 4. Fact Table
df_ec = pd.read_excel(raw_excel, sheet_name="Energy Consumptions")
df_ec.to_csv(os.path.join(clean_dir, "fact_energy_consumption.csv"), index=False)

# 5. Flat Enriched Master (for simple 1-table Power BI import if preferred)
df_enrich = pd.read_csv(os.path.join(base_dir, "data", "processed", "energy_consumption_enriched.csv"))
df_enrich.to_csv(os.path.join(clean_dir, "energy_master_flat.csv"), index=False)

print(f"[PowerBI Export] Dimensional and flat datasets exported to: {clean_dir}")
