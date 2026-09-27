# Energy Consumption & Business Performance Analytics

An interactive Power BI dashboard designed to analyze energy consumption, utility costs, and building-level business performance across multiple cities and buildings from 2016–2019.

## 📊 Project Overview

This project transforms energy consumption and utility cost data into an interactive business intelligence dashboard using Microsoft Power BI.

The dashboard provides insights into:

- Overall utility expenditure
- Monthly and annual cost trends
- Electricity, gas, and water costs
- Energy consumption patterns
- Building-level performance
- City-level cost comparison
- Utility cost distribution
- Consumption comparison across buildings

## 🎯 Objectives

- Analyze overall utility expenditure and consumption.
- Identify cost trends across years.
- Compare utility costs across cities.
- Evaluate building-level utility performance.
- Analyze electricity, gas, and water consumption.
- Provide interactive filtering for business analysis.
- Present complex energy data through clear visualizations.

## 🛠️ Technologies Used

- Microsoft Power BI
- DAX
- Power Query
- Data Modeling
- Data Visualization

## 🗂️ Data Model

The project uses a dimensional data model consisting of:

### Fact Table

**fact_energy_consumption**

Contains energy consumption records for buildings and dates.

Key fields:

- Building
- Date
- Electricity Consumption
- Gas Consumption
- Water Consumption

### Dimension Tables

**dim_calendar**
- Date
- Year
- Month
- Quarter
- Year-Month
- Year-Quarter

**dim_building**
- Building
- City
- Country

**dim_rate**
- Energy Type
- Price Per Unit
- Year

**dim_utility**
- Utility

This structure enables efficient filtering, aggregation, and time-based analysis.

## 📐 DAX Measures

The dashboard includes DAX measures for:

- Total Utility Cost
- Total Electricity Cost
- Total Gas Cost
- Total Water Cost
- Total Electricity Consumption
- Total Gas Consumption
- Total Water Consumption
- Average Monthly Cost
- Previous Year Cost
- YoY Cost Growth %
- Electricity Cost %
- Gas Cost %
- Water Cost %
- Average Cost per Building

## 📈 Dashboard Pages

### Page 1 — Executive Overview

Provides a high-level summary of business performance through:

- Total Utility Cost KPI
- Average Monthly Cost KPI
- Total Buildings KPI
- Total Months KPI
- Annual Utility Cost Trend
- Annual Cost Analysis
- Utility Distribution
- Cost by City
- Year slicer
- City slicer
- Building slicer

### Page 2 — Building Performance & Cost Analysis

Focuses on building-level analysis through:

- Utility Cost by Building
- Utility Cost by City
- Utility Consumption by Building
- Building-level performance table
- Total Utility Cost
- Average Monthly Cost
- Average Cost per Building

## 📌 Key Dashboard Metrics

Based on the dashboard:

- **Total Utility Cost:** approximately $15.84M
- **Total Buildings:** 11
- **Total Months:** 48
- **Cities:** 5
- **Analysis Period:** 2016–2019

## 💡 Business Insights

The dashboard enables stakeholders to:

- Identify high-cost buildings.
- Compare utility expenditure between cities.
- Track annual changes in utility costs.
- Understand the contribution of water, gas, and electricity to total expenditure.
- Identify buildings with higher utility consumption.
- Support data-driven energy management and cost optimization decisions.

## 🖼️ Dashboard Preview

### Executive Overview

![Executive Overview](screenshots/executive-overview.png)

### Building Performance & Cost Analysis

![Building Performance](screenshots/building-performance.png)

## 🚀 How to Use

1. Download the `.pbix` Power BI file.
2. Open it using Microsoft Power BI Desktop.
3. Refresh the data if the required data source is available.
4. Use the slicers to filter the dashboard by:
   - Year
   - City
   - Building
5. Interact with the visuals to explore cost and consumption patterns.

## 📁 Project Files

| File | Description |
|---|---|
| `Energy_Business_Performance_Analytics.pbix` | Power BI dashboard |
| `screenshots/` | Dashboard preview images |
| `README.md` | Project documentation |

## 👨‍💻 Author

**Arvindh Babu V**

B.Tech — Artificial Intelligence & Data Science

GitHub: https://github.com/Arvindhbabu

Portfolio: https://arvindhbabu.github.io/Portfolio/

## 📄 License

This project is intended for educational and portfolio purposes.
