# Analytical Limitations & Research Constraints
**Project:** Energy Consumption & Business Performance Analytics  
**Context:** Professional Analytics Governance & Interview Defensibility  

---

## 1. Overview & Methodological Candor

In professional analytics and enterprise data science, acknowledging dataset boundaries and model assumptions is critical for executive credibility. While the analytics pipeline and SQL queries in this project adhere to rigorous engineering standards, several fundamental limitations arise from the observational and synthetic characteristics of the underlying data.

This document explicitly delineates these constraints to prevent over-interpretation and ensure that recommendations are presented within their valid empirical scope.

---

## 2. Key Data Limitations

### 2.1 Absence of Physical Facility Normalization Variables (Scale Bias)
- **Missing Parameters:** The dataset contains no metadata regarding:
  - Gross Floor Area / Square Footage ($\text{sq ft}$ or $\text{m}^2$)
  - Building Volume or Ceiling Heights
  - Facility Type (e.g., Commercial Office, Data Center, Warehouse, Retail)
  - Year of Construction / Architectural Vintage
- **Analytical Impact:** Building `B1008` is the highest-cost facility in the portfolio (\$1.50M vs \$1.36M for `B1007`). However, if `B1008` spans $250,000\text{ sq ft}$ while `B1007` spans only $180,000\text{ sq ft}$, `B1008` is actually significantly *more energy-efficient* on an Energy Use Intensity (EUI = $\text{kBtu} / \text{sq ft}$) basis. Without square footage, an analyst cannot definitively label any building as operational "wasteful" or "efficient".

### 2.2 Absence of Operational & Occupancy Context
- **Missing Parameters:**
  - Daily/Weekly Operating Hours (e.g., 24/7 continuous operations vs standard 8-to-5 office schedule)
  - Headcount and Full-Time Equivalent (FTE) Occupancy
  - Tenant Industry Density (e.g., computer labs vs standard administrative space)
- **Analytical Impact:** Water and electrical surges may simply reflect higher tenant density or expanded shift operations rather than plumbing leaks or equipment inefficiencies.

### 2.3 Exogenous Weather & Climatic Normalization (CDD / HDD)
- **Missing Parameters:**
  - Outside Ambient Air Temperature
  - Cooling Degree Days (CDD) and Heating Degree Days (HDD)
  - Humidity / Wet-Bulb Temperatures
- **Analytical Impact:** Geographic differences between Phoenix (`B1006`) and Chicago (`B1004`, `B1007`, `B1008`) reflect severe climatic divergence (extreme desert summer heat vs severe midwestern sub-zero winters). Energy analytics best practice requires weather-normalization using ASHRAE degree-day regressions. The absence of local weather feeds prevents separating weather volatility from equipment performance.

### 2.4 Simplified Utility Tariff Assumptions
- **Rate Uniformity Across Geographies:** The supplied `Rates` table specifies a single price per unit for each utility per year regardless of geographic location. In real-world utility markets, water, electricity, and gas tariffs vary dramatically across municipalities (e.g., ConEdison in New York vs LADWP in Los Angeles vs ComEd in Chicago).
- **Absence of Time-of-Use (TOU) and Peak Demand Charges:** Commercial electricity tariffs typically feature complex billing structures:
  - On-peak vs Off-peak volumetric rates (\$/kWh)
  - Peak Electrical Demand Charges based on 15-minute kW peak intervals (\$/kW)
  - Fixed customer meter charges and municipal franchise fees
  The model assumes a flat volumetric rate ($P \times Q$), omitting demand ratchets.
- **Fixed Compounding Rate Escalation:** All three utility rates escalate by exactly **+10.0% p.a.** compound annual growth rate. This mathematical regularity reflects synthetic educational modeling rather than deregulated market fluctuations.

### 2.5 Inability to Establish Causal Mechanisms
- As an observational study, statistical correlation and regression cannot prove causality.
- Observed statistical anomalies ($Z \ge 2.0$) represent candidate signals for engineering investigation rather than definitive equipment failures.

---

## 3. Interview-Ready Defense Summary

| Question from Hiring Manager | Executive-Grade Analyst Response |
| :--- | :--- |
| *"Why didn't you declare Building 1008 as the most inefficient building?"* | *"Because efficiency is a ratio of input to useful output. While B1008 has the highest absolute expenditure (\$1.50M), our dataset lacks square footage, occupancy, and operating hours. High cost may simply reflect a larger physical scale. I recommended an engineering audit rather than asserting operational waste."* |
| *"Is the 48% cost growth caused by poor management?"* | *"No. Our Price vs. Volume variance decomposition proves that by 2019, 92.6% of cost growth was driven by external tariff inflation (+10% annual rate escalation), while water consumption actually fell by -3.5%. The organization is maintaining usage discipline, but macro rate hikes are driving expenditure."* |
| *"Why is New York the highest-cost city in totals, but Phoenix is highest in normalized cost?"* | *"Aggregation bias. New York contains 3 facilities totaling \$4.34M (\$1.45M/bldg), while Phoenix has only 1 facility totaling \$1.48M. On a like-for-like facility basis, Phoenix is 2.4% more expensive than New York."* |

---

## 4. Proposed Data Enhancements for Future Iterations

1. **Facility Master Enrichment:** Ingest building gross floor area ($\text{sq ft}$), construction year, HVAC equipment type, and occupant headcount.
2. **Weather API Integration:** Ingest NOAA monthly Heating and Cooling Degree Days (HDD/CDD) to build weather-normalized regression baselines.
3. **Sub-Metered Telemetry:** Obtain interval smart-meter data (15-minute or hourly kW readings) to analyze peak demand charges and power factor penalties.
