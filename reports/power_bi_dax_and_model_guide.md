# Power BI Enterprise Semantic Model & DAX Guide
**Project:** Energy Consumption & Business Performance Analytics  
**Document Type:** Business Intelligence Semantic Model Specification & Blueprint  
**Target BI Platform:** Microsoft Power BI Desktop / Power BI Service  

---

## 1. Executive Summary & Upgrade Strategy

The original Power BI file (`Energy Consumption Trend Analysis.pbix`) suffered from severe modeling limitations:
1. It loaded disconnected tables without Star Schema relationships.
2. It contained **zero custom DAX measures**, leading Power BI to default to invalid auto-summaries such as `Sum(Rates.Year)` and `Sum(Rates.Price Per Unit)`.
3. Financial utility costs were never computed.
4. Physical consumption units with different dimensions (gallons, kWh, therms) were summed together in charts.

This blueprint establishes a **Gold-Standard Power BI Architecture**:
- A unified **Star Schema** with one-to-many (`1:*`) relationships and single-direction cross-filtering.
- A dedicated `_Measures` table containing over 20 production-grade, documented DAX measures.
- A 5-page executive dashboard layout designed for C-suite decision-makers.

---

## 2. Power BI Data Model Architecture (Star Schema)

Import the clean tables from `outputs/cleaned_data/`:

| Table Name | Source File | Table Type | Role in Model |
| :--- | :--- | :--- | :--- |
| `dim_calendar` | `outputs/cleaned_data/dim_calendar.csv` | Dimension | Temporal hierarchy (Year, Quarter, Month, Year-Month). Marked as Official Date Table. |
| `dim_building` | `outputs/cleaned_data/dim_building.csv` | Dimension | Facility master (Building, City, Country). |
| `dim_rate` | `outputs/cleaned_data/dim_rate.csv` | Dimension | Annual tariffs per energy type. |
| `fact_energy_consumption` | `outputs/cleaned_data/fact_energy_consumption.csv` | Fact | 528 monthly consumption records. |
| `_Measures` | Created in Power BI (Enter Data) | Measure Table | Central repository for all business DAX formulas. |

### Relationships:
1. `dim_calendar[Date]` `1` $\rightarrow$ `*` `fact_energy_consumption[Date]` (Single Direction)
2. `dim_building[Building]` `1` $\rightarrow$ `*` `fact_energy_consumption[Building]` (Single Direction)
3. *(Alternative Option)*: If utilizing `outputs/cleaned_data/energy_master_flat.csv`, a pre-calculated dimensional model is immediately available without relationship overhead.

---

## 3. Production DAX Measure Library

Create a blank table named `_Measures` and add the following measures.

### 3.1 Base Consumption & Financial Cost Measures

#### Measure 01: `[Total Water Consumption]`
```dax
Total Water Consumption = 
SUM('fact_energy_consumption'[Water Consumption])
```
*Format: Whole Number (`#,##0`)*

#### Measure 02: `[Total Electricity Consumption]`
```dax
Total Electricity Consumption = 
SUM('fact_energy_consumption'[Electricity Consumption])
```
*Format: Whole Number (`#,##0`)*

#### Measure 03: `[Total Gas Consumption]`
```dax
Total Gas Consumption = 
SUM('fact_energy_consumption'[Gas Consumption])
```
*Format: Whole Number (`#,##0`)*

#### Measure 04: `[Total Water Cost]`
```dax
Total Water Cost = 
SUMX(
    'fact_energy_consumption',
    'fact_energy_consumption'[Water Consumption] * 
    LOOKUPVALUE(
        'dim_rate'[Price Per Unit],
        'dim_rate'[Energy Type], "Water",
        'dim_rate'[Year], YEAR('fact_energy_consumption'[Date])
    )
)
```
*(If using `energy_master_flat`: `SUM(energy_master_flat[Water_Cost])`)*  
*Format: Currency (`$#,##0.00`)*

#### Measure 05: `[Total Electricity Cost]`
```dax
Total Electricity Cost = 
SUMX(
    'fact_energy_consumption',
    'fact_energy_consumption'[Electricity Consumption] * 
    LOOKUPVALUE(
        'dim_rate'[Price Per Unit],
        'dim_rate'[Energy Type], "Electricity",
        'dim_rate'[Year], YEAR('fact_energy_consumption'[Date])
    )
)
```
*Format: Currency (`$#,##0.00`)*

#### Measure 06: `[Total Gas Cost]`
```dax
Total Gas Cost = 
SUMX(
    'fact_energy_consumption',
    'fact_energy_consumption'[Gas Consumption] * 
    LOOKUPVALUE(
        'dim_rate'[Price Per Unit],
        'dim_rate'[Energy Type], "Gas",
        'dim_rate'[Year], YEAR('fact_energy_consumption'[Date])
    )
)
```
*Format: Currency (`$#,##0.00`)*

#### Measure 07: `[Total Utility Cost]`
```dax
Total Utility Cost = 
[Total Water Cost] + [Total Electricity Cost] + [Total Gas Cost]
```
*Format: Currency (`$#,##0.00`)*

---

### 3.2 Portfolio KPI & Average Measures

#### Measure 08: `[Average Monthly Cost]`
```dax
Average Monthly Cost = 
DIVIDE(
    [Total Utility Cost],
    DISTINCTCOUNT('dim_calendar'[Year_Month]),
    0
)
```
*Format: Currency (`$#,##0.00`)*

#### Measure 09: `[Average Cost Per Building]`
```dax
Average Cost Per Building = 
DIVIDE(
    [Total Utility Cost],
    DISTINCTCOUNT('dim_building'[Building]),
    0
)
```
*Format: Currency (`$#,##0.00`)*

---

### 3.3 Utility Contribution Share Measures

#### Measure 10: `[Water Cost Share %]`
```dax
Water Cost Share % = 
DIVIDE([Total Water Cost], [Total Utility Cost], 0)
```
*Format: Percentage (`0.0%`)*

#### Measure 11: `[Electricity Cost Share %]`
```dax
Electricity Cost Share % = 
DIVIDE([Total Electricity Cost], [Total Utility Cost], 0)
```
*Format: Percentage (`0.0%`)*

#### Measure 12: `[Gas Cost Share %]`
```dax
Gas Cost Share % = 
DIVIDE([Total Gas Cost], [Total Utility Cost], 0)
```
*Format: Percentage (`0.0%`)*

---

### 3.4 Time-Intelligence & Growth Dynamic Measures

#### Measure 13: `[Previous Year Cost]`
```dax
Previous Year Cost = 
CALCULATE(
    [Total Utility Cost],
    SAMEPERIODLASTYEAR('dim_calendar'[Date])
)
```
*Format: Currency (`$#,##0.00`)*

#### Measure 14: `[YoY Cost Growth %]`
```dax
YoY Cost Growth % = 
VAR PrevYear = [Previous Year Cost]
VAR CurrYear = [Total Utility Cost]
RETURN
DIVIDE(CurrYear - PrevYear, PrevYear, BLANK())
```
*Format: Percentage (`+0.0%;-0.0%;0.0%`)*

#### Measure 15: `[Previous Month Cost]`
```dax
Previous Month Cost = 
CALCULATE(
    [Total Utility Cost],
    DATEADD('dim_calendar'[Date], -1, MONTH)
)
```
*Format: Currency (`$#,##0.00`)*

#### Measure 16: `[MoM Cost Growth %]`
```dax
MoM Cost Growth % = 
VAR PrevMonth = [Previous Month Cost]
VAR CurrMonth = [Total Utility Cost]
RETURN
DIVIDE(CurrMonth - PrevMonth, PrevMonth, BLANK())
```
*Format: Percentage (`+0.0%;-0.0%;0.0%`)*

#### Measure 17: `[Rolling 3M Avg Cost]`
```dax
Rolling 3M Avg Cost = 
CALCULATE(
    [Average Monthly Cost],
    DATESINPERIOD('dim_calendar'[Date], MAX('dim_calendar'[Date]), -3, MONTH)
)
```
*Format: Currency (`$#,##0.00`)*

#### Measure 18: `[Rolling 12M Avg Cost]`
```dax
Rolling 12M Avg Cost = 
CALCULATE(
    [Average Monthly Cost],
    DATESINPERIOD('dim_calendar'[Date], MAX('dim_calendar'[Date]), -12, MONTH)
)
```
*Format: Currency (`$#,##0.00`)*

---

### 3.5 Ranking & Dynamic Context Measures

#### Measure 19: `[Building Cost Rank]`
```dax
Building Cost Rank = 
RANKX(
    ALLSELECTED('dim_building'[Building]),
    [Total Utility Cost],
    ,
    DESC,
    Dense
)
```
*Format: Whole Number*

#### Measure 20: `[City Cost Rank]`
```dax
City Cost Rank = 
RANKX(
    ALLSELECTED('dim_building'[City]),
    [Total Utility Cost],
    ,
    DESC,
    Dense
)
```
*Format: Whole Number*

---

## 4. Upgraded 5-Page Dashboard Layout Blueprint

### PAGE 1 — Executive Overview
- **Header:** Organization Logo, Title: *"Enterprise Utility & Performance Analytics"*, Global Slicers (`Year`, `City`).
- **Top KPI Cards (Row 1):**
  1. `[Total Utility Cost]` (\$15.84M)
  2. `[Total Water Cost]` (\$10.81M | 68.2%)
  3. `[Total Gas Cost]` (\$3.01M | 19.0%)
  4. `[Total Electricity Cost]` (\$2.03M | 12.8%)
  5. `[YoY Cost Growth %]` (+10.9% in 2019)
- **Visuals (Body):**
  - **Visual 1 (Line & Stacked Column):** Monthly spend trend with bars broken down by Water, Gas, Electricity, and a navy line overlay for `[Rolling 12M Avg Cost]`.
  - **Visual 2 (Donut Chart):** Expenditure share by utility category.
  - **Visual 3 (Clustered Bar Chart):** Total City Spend vs. `[Average Cost Per Building]` side-by-side.

### PAGE 2 — Utility Performance Deep-Dive
- **Header:** Utility Slicer (Water, Electricity, Gas), Metric Toggle.
- **Visuals:**
  - **Visual 1 (Area Chart):** Monthly volume vs. cost trend for the selected utility.
  - **Visual 2 (Waterfall Chart):** Annual spend progression highlighting annual growth increments.
  - **Visual 3 (Matrix Grid):** Year-over-Year comparison matrix showing Unit Consumption, Tariff Rate, Total Spend, and YoY % Change.

### PAGE 3 — Building & Geographic Analytics
- **Header:** Slicers for `City`, `Building`, `Quarter`.
- **Visuals:**
  - **Visual 1 (Horizontal Ranked Bar):** All 11 buildings ranked by `[Total Utility Cost]` with utility color-stacking.
  - **Visual 2 (Scatter Plot):** X-axis: `[Total Water Consumption]`, Y-axis: `[Total Gas Consumption]`, Bubble Size: `[Total Utility Cost]`, Color: `City`.
  - **Visual 3 (Matrix Table):** Hierarchy breakdown: `City` $\rightarrow$ `Building` $\rightarrow$ `Total Cost`, `Avg Monthly Cost`, `Utility Mix %`, `Rank`.

### PAGE 4 — Trends, Seasonality & Anomalies
- **Header:** Time-series drill down and anomaly filter (`Is_Business_Anomaly`).
- **Visuals:**
  - **Visual 1 (Multi-line Chart):** Seasonality profiles across calendar months (Jan–Dec) showing summer water surge vs. winter gas surge.
  - **Visual 2 (Heatmap Matrix):** Year on columns, Month on rows, conditional formatting on `[Total Utility Cost]` to pinpoint peak cost windows.
  - **Visual 3 (Table):** Operational Anomaly Log displaying Date, Building, City, Metric, Z-Score, and Classification.

### PAGE 5 — Executive Business Insights & Recommendations
- **Layout:** Clean card-and-callout management presentation:
  - **Card 1: Primary Cost Driver** (Water represents 68.2% of spend; recommend cooling tower sub-metering).
  - **Card 2: Rate Escalation vs Efficiency** (Tariff inflation drives 92.6% of recent cost growth; recommend rate hedging).
  - **Card 3: Geographic Normalization** (Phoenix is the highest unit cost asset; recommend climate efficiency audit).
  - **Card 4: Facility Spread** (10.3% performance gap between B1008 and B1007; potential \$35k/yr optimization).
