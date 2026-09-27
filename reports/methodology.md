# Analytics Methodology & Technical Architecture Specification
**Project:** Energy Consumption & Business Performance Analytics  
**Role:** Senior Data Analyst / Analytics Engineer  
**Dataset Source:** Edunet Foundation (AICTE Cycle 6) — Ground Truth Energy Dataset  
**Status:** Certified Production-Grade  

---

## 1. Executive Overview & Problem Context

Enterprise facilities management requires rigorous visibility into utility consumption and financial operating expenditure (OpEx). Organizations managing distributed real estate portfolios frequently face significant challenges:
1. **Scattered or Disconnected Data:** Consumption data recorded in operational systems without relational links to utility tariff schedules or building master metadata.
2. **Aggregation Bias:** Comparing cities by total spend without normalizing for facility counts, leading to skewed capital allocation.
3. **Unexplained Cost Inflation:** Inability to isolate whether utility expenditure surges stem from operational inefficiencies (consumption volume) or external macro factors (utility rate hikes).

This project establishes a standardized, reproducible analytics pipeline transforming raw utility records into an executive business intelligence suite.

---

## 2. Data Model & Architecture

### 2.1 Conceptual & Relational Star Schema

The analytics architecture implements an enterprise **Star Schema** optimized for analytical querying, Power BI DAX performance, and dimensional filtering:

```
                  +---------------------------+
                  |       dim_calendar        |
                  +---------------------------+
                  | Date (PK)                 |
                  | Year                      |
                  | Month_Number              |
                  | Month_Name                |
                  | Quarter                   |
                  | Year_Month                |
                  +-------------+-------------+
                                |
                                | 1:N
                                v
+----------------------+  +---------------------------+  +----------------------+
|     dim_building     |  | fact_energy_consumption   |  |       dim_rate       |
+----------------------+  +---------------------------+  +----------------------+
| building_id (PK)     |<-| consumption_id (PK)       |->| rate_year (PK)       |
| city                 |  | consumption_date (FK)     |  | energy_type (PK)     |
| country              |  | building_id (FK)          |  | price_per_unit       |
+----------------------+  | water_consumption         |  +----------------------+
                          | electricity_consumption   |
                          | gas_consumption           |
                          +---------------------------+
```

### 2.2 Dataset Granularity & Verified Schemas

- **Grain:** Exactly **1 observation per Building per Month** (`consumption_date` + `building_id`).
- **Fact Table (`Energy Consumptions`):**
  - Dimensions: 528 rows × 5 columns.
  - Coverage: 11 distinct buildings (`B1000`–`B1010`) × 48 contiguous months (`2016-01-01` to `2019-12-01`).
  - Zero missing periods, zero duplicate keys.
- **Dimension Table (`Building Master`):**
  - Dimensions: 11 rows × 3 columns.
  - 5 Metropolitan Areas: New York (3 buildings), Los Angeles (3 buildings), Chicago (3 buildings), Phoenix (1 building), Houston (1 building).
  - Country: United States (`USA`).
- **Dimension Table (`Rates`):**
  - Dimensions: 15 rows × 3 columns.
  - Covers calendar years 2016 through 2020 across all 3 utility categories.
  - Constant compound annual growth rate: exactly **+10.0% p.a.** across all utility rates.

---

## 3. Financial Cost Engineering

Utility consumption metrics possess fundamentally disparate physical units (Water in gallons/units, Electricity in kilowatt-hours, Gas in therms/units). Directly summing these values constitutes a severe mathematical error. Financial cost engineering translates consumption into a unified financial currency (USD).

### 3.1 Cost Calculation Formulas

$$ \text{Water Cost}_{i,t} = \text{Water Consumption}_{i,t} \times \text{Water Rate}_t $$

$$ \text{Electricity Cost}_{i,t} = \text{Electricity Consumption}_{i,t} \times \text{Electricity Rate}_t $$

$$ \text{Gas Cost}_{i,t} = \text{Gas Consumption}_{i,t} \times \text{Gas Rate}_t $$

$$ \text{Total Utility Cost}_{i,t} = \text{Water Cost}_{i,t} + \text{Electricity Cost}_{i,t} + \text{Gas Cost}_{i,t} $$

*where $i$ denotes the individual building and $t$ denotes the calendar period.*

### 3.2 Utility Cost Share Allocation

$$ \text{Water Cost Share \%} = \left( \frac{\sum \text{Water Cost}}{\sum \text{Total Utility Cost}} \right) \times 100 $$

$$ \text{Electricity Cost Share \%} = \left( \frac{\sum \text{Electricity Cost}}{\sum \text{Total Utility Cost}} \right) \times 100 $$

$$ \text{Gas Cost Share \%} = \left( \frac{\sum \text{Gas Cost}}{\sum \text{Total Utility Cost}} \right) \times 100 $$

---

## 4. Price vs. Volume Variance Decomposition

A core analytical contribution of this portfolio project is the mathematical isolation of operational usage changes from external price escalation.

### 4.1 Mathematical Formulation

Let:
- $Q_0, Q_1$ be consumption quantities in periods $t-1$ and $t$.
- $P_0, P_1$ be tariff rates in periods $t-1$ and $t$.
- $C_0 = Q_0 \times P_0$ and $C_1 = Q_1 \times P_1$ be total expenditure.

The total cost change ($\Delta C$) is decomposed using Laspeyres-type variance analysis:

$$ \Delta C = C_1 - C_0 = (Q_1 \times P_1) - (Q_0 \times P_0) $$

We factor this identity into:

$$ \text{Volume Effect} = (Q_1 - Q_0) \times P_0 $$
*(The change in expenditure attributable strictly to consumption change, evaluated at baseline price)*

$$ \text{Price Effect} = Q_1 \times (P_1 - P_0) $$
*(The change in expenditure attributable strictly to tariff inflation, evaluated on current volume)*

### 4.2 Exact Identity Proof (Zero Residual)

$$ \text{Volume Effect} + \text{Price Effect} = (Q_1 P_0 - Q_0 P_0) + (Q_1 P_1 - Q_1 P_0) = Q_1 P_1 - Q_0 P_0 = \Delta C $$

This identity is 100% mathematically exact with zero residual or unexplained variance.

---

## 5. Anomaly Detection Framework

To prevent alert fatigue and provide actionable intelligence to operations, the framework separates **Statistical Outliers** from **Business Anomalies**.

### 5.1 Statistical Outlier Methods
1. **Tukey’s Fences (IQR Method):**
   - Interquartile Range $\text{IQR} = Q_3 - Q_1$
   - $\text{Lower Bound} = Q_1 - 1.5 \times \text{IQR}$
   - $\text{Upper Bound} = Q_3 + 1.5 \times \text{IQR}$
2. **Building-Normalized Z-Score:**
   - $Z_{i,t} = \frac{X_{i,t} - \mu_i}{\sigma_i}$
   - Threshold: $|Z_{i,t}| \ge 2.0$ (warning threshold isolating 95th percentile variations).

### 5.2 Business Domain Classification Rules
- **Winter Gas Demand:** High gas usage during December–February aligns with space heating physics. These are classified as **Expected Seasonal Peak Demand**. High gas usage in July indicates a boiler control failure or continuous space heating overrun and is flagged as an **Actionable Business Anomaly**.
- **Summer Water Demand:** High water usage during June–August correlates with cooling tower evaporative heat rejection. Off-season water surges in winter indicate underground pipe leaks or facility fixture failures.
- **Summer Electrical Load:** Peak July chiller demand represents normal peak-load operations, whereas off-peak electrical surges warrant facility audits.

---

## 6. Business KPI Architecture

| KPI Name | Analytical Grain | Business Definition | Formula |
| :--- | :--- | :--- | :--- |
| **Total Portfolio Cost** | Enterprise / Portfolio | Cumulative expenditure across all utilities | $\sum \text{Total Cost}$ |
| **Avg Monthly Cost** | Portfolio / Month | Average monthly operational expenditure | $\frac{\text{Total Cost}}{\text{Active Months}}$ |
| **YoY Cost Growth %** | Period / Annual | Rate of annual expenditure expansion | $\frac{\text{Cost}_t - \text{Cost}_{t-1}}{\text{Cost}_{t-1}} \times 100$ |
| **MoM Cost Growth %** | Period / Monthly | Sequential monthly volatility rate | $\frac{\text{Cost}_m - \text{Cost}_{m-1}}{\text{Cost}_{m-1}} \times 100$ |
| **Rolling 12M Avg Cost** | Time-Series | Deseasonalized baseline expenditure trend | 12-month trailing moving average |
| **Cost Per Building** | City / Geography | Like-for-like regional efficiency metric | $\frac{\text{Total City Cost}}{\text{Building Count}}$ |
| **Utility Mix %** | Facility / Building | Energy source cost concentration | $\frac{\text{Utility Cost}}{\text{Facility Total Cost}} \times 100$ |

---

## 7. Implementation & Reproducibility Stack

- **Data Processing:** Python 3.12, Pandas 2.2.3, NumPy 1.26.4
- **Relational SQL Engine:** SQLite 3 (In-Memory Test Harness) / Standard ANSI SQL compatible
- **Visualization:** Matplotlib 3.8+, Seaborn 0.13+
- **Business Intelligence:** Microsoft Power BI Desktop, DAX
- **Orchestration:** `src/run_pipeline.py` (single-command execution)
