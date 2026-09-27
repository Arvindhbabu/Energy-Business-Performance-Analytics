# Project Audit & Discovery Report
**Project Name:** Energy Consumption & Business Performance Analytics  
**Original Foundation:** Edunet Foundation (AICTE Cycle 6) — Data Analytics Internship  
**Auditor / Lead Analytics Engineer:** Antigravity Senior Analytics Engineering Lead  
**Audit Date:** September 2026  
**Status:** Audit Complete — Baseline Established  

---

## 1. Executive Summary

This audit comprehensively documents the existing state of the Edunet Foundation Data Analytics Internship workspace. The workspace contains original raw datasets, Excel assignment sheets, preliminary Power BI Desktop files, internship guideline documents, milestone presentations, and student artifacts.

The original internship effort was titled *"Energy Consumption Trend Analysis with Power BI"*. While it succeeded in loading raw data and generating basic visuals, the analysis remained rudimentary: **no utility cost metrics were computed in Power BI**, **no custom DAX measures were built**, **rates were erroneously summed across time**, and **different utility units were combined without normalization**. 

This document serves as the formal baseline. In compliance with strict project governance rules:
- **100% of original source files are preserved untouched.**
- **Zero data, records, or e-commerce columns are fabricated.**
- A rigorous, production-grade analytics engineering structure (`energy-business-analytics/`) is created alongside the legacy files to transform this work into an executive-ready, interview-grade case study.

---

## 2. Complete File Inventory

The workspace root contains 15 files totaling approximately 5.86 MB.

| File Name | File Type | Size (Bytes) | Category | Description / Role |
| :--- | :--- | :--- | :--- | :--- |
| `Energy Consumption Data.xlsx` | Excel Workbook (.xlsx) | 31,943 | Primary Dataset | Ground truth data file containing 3 core sheets: Consumptions, Rates, Building Master. |
| `Data Analytics Assignment 1.xlsx` | Excel Workbook (.xlsx) | 186,682 | Academic / Assignment | Assignment sheet containing pivot tables and duplicated raw sheets. |
| `Energy Consumption Trend Analysis.pbix` | Power BI (.pbix) | 91,950 | BI Dashboard (Final) | 4-page report (Overview, Energy Consumption, Level of Details, Example). |
| `Energy Consumption  Week 2 Task.pbix` | Power BI (.pbix) | 83,965 | BI Dashboard (WIP) | 3-page intermediate milestone submission for Week 2. |
| `Energy Consumption Week 1 Task.pbix` | Power BI (.pbix) | 79,013 | BI Dashboard (WIP) | Single-visual milestone submission for Week 1 (clustered column chart). |
| `Energy Consumption and Trend Analysis.pptx` | PowerPoint (.pptx) | 1,730,714 | Milestone Presentation | 8-slide internship presentation submitted for final evaluation. |
| `Week_3_Project_PPT_Template1.pptx` | PowerPoint (.pptx) | 1,042,300 | Template | Edunet Foundation mandatory Week 3 submission presentation template. |
| `Data Analytics Assignment 1.pdf` | PDF Document | 169,216 | Assignment Output | Exported PDF showing Excel pivot tables and consumption charts. |
| `Project_exp.pdf` | PDF Document | 66,337 | Official Documentation | Edunet internship syllabus defining the 5 project tracks. |
| `LMS_Process_Document.pdf` | PDF Document | 1,210,093 | Operational Guide | Student onboarding and LMS portal navigation instructions. |
| `Weekly_Milestones_and_Project_Submission_Process_Document_3.pdf` | PDF Document | 646,976 | Operational Guide | Submission instructions for GitHub repo linking and PPT milestones. |
| `Arvindh  babu V _INTERNSHIP_174099535967c57b1f336c3_offer_letter.pdf` | PDF Document | 239,217 | Administrative | Official AICTE/Edunet internship offer letter. |
| `photo_2025-04-25_18-37-32.jpg` | JPEG Image | 87,749 | Administrative | AICTE Cycle 6 project-wise timetable schedule. |
| `photo_2025-04-25_18-44-07.jpg` | JPEG Image | 110,515 | Official Documentation | Edunet project list overview graphic. |
| `photo_2025-04-25_19-59-16.jpg` | JPEG Image | 147,829 | Administrative | AICTE Cycle 6 timetable full view graphic. |

---

## 3. Original Project Purpose

According to `Project_exp.pdf` and `photo_2025-04-25_18-44-07.jpg`, the project was assigned under **AICTE Internship Cycle 6** conducted by **Edunet Foundation**:
- **Track:** Project 1 — *Energy Consumption Trend Analysis with Power BI*.
- **Objective:** Develop an interactive Power BI dashboard to analyze energy consumption data for an enterprise across gas, electricity, and water utilities.
- **Scope:** Provide visual insights into consumption volumes, operational expenditure, and utility-wise trends to empower facilities management and promote environmental sustainability.

---

## 4. Dataset Files & Schema Audit

The source of truth is `Energy Consumption Data.xlsx`. It consists of 3 relational tables:

### Table 1: `Energy Consumptions` (Fact Table)
- **Granularity:** 1 record per Building per Month (`Date` + `Building`).
- **Dimensions:** 528 rows × 5 columns.
- **Time Horizon:** 48 consecutive months from January 1, 2016 (`2016-01-01`) to December 1, 2019 (`2019-12-01`).
- **Entity Coverage:** 11 distinct buildings (`B1000` through `B1010`), each having exactly 48 records. Zero missing months.
- **Fields:**
  1. `Date` (`datetime64[ns]`): First day of each calendar month.
  2. `Building` (`object/string`): Unique building identifier (`B1000`–`B1010`).
  3. `Water Consumption` (`int64`): Monthly water volume (Mean: 352,737 units; Range: 227,108 to 505,757 units).
  4. `Electricity Consumption` (`int64`): Monthly electricity usage (Mean: 41,036 kWh; Range: 26,455 to 59,522 kWh).
  5. `Gas Consumption` (`int64`): Monthly gas usage (Mean: 4,835 units; Range: 1,940 to 7,351 units).
- **Data Quality:** Zero null values, zero duplicate keys, zero negative or zero-value consumption anomalies.

### Table 2: `Rates` (Dimension / Lookup Table)
- **Dimensions:** 15 rows × 3 columns.
- **Fields:**
  1. `Year` (`int64`): Calendar years 2016, 2017, 2018, 2019, 2020.
  2. `Energy Type` (`object/string`): `Water`, `Electricity`, `Gas`.
  3. `Price Per Unit` (`float64`): Unit tariff in USD.
- **Rate Schedule & Growth Analysis:**
  - **Water:** 2016: \$0.0500 | 2017: \$0.0550 | 2018: \$0.0605 | 2019: \$0.06655 | 2020: \$0.073205 (+10.0% p.a. CAGR).
  - **Gas:** 2016: \$1.0000 | 2017: \$1.1000 | 2018: \$1.2100 | 2019: \$1.3310 | 2020: \$1.4641 (+10.0% p.a. CAGR).
  - **Electricity:** 2016: \$0.0800 | 2017: \$0.0880 | 2018: \$0.0968 | 2019: \$0.10648 | 2020: \$0.117128 (+10.0% p.a. CAGR).
  - *Key Structural Finding:* All utility unit prices increase by exactly 10.0% year-over-year.

### Table 3: `Building Master` (Dimension Table)
- **Dimensions:** 11 rows × 3 columns.
- **Fields:**
  1. `Building` (`object/string`): Unique identifier (`B1000`–`B1010`).
  2. `City` (`object/string`): Geographic metropolitan area (5 unique cities).
  3. `Country` (`object/string`): All 11 records are located in `USA`.
- **Geographic Distribution:**
  - `New York` (3 buildings): `B1000`, `B1001`, `B1002`
  - `Los Angeles` (3 buildings): `B1003`, `B1009`, `B1010`
  - `Chicago` (3 buildings): `B1004`, `B1007`, `B1008`
  - `Houston` (1 building): `B1005`
  - `Phoenix` (1 building): `B1006`
  - *Critical Analytical Implication:* Cities have disparate building counts (1 vs 3). Total city comparisons without building-level normalization produce severe aggregation bias.

---

## 5. Existing Power BI Work Audit

Decompilation and inspection of `Energy Consumption Trend Analysis.pbix` revealed:
1. **Model Architecture:** The data model loaded the three sheets as disconnected or flat tables without a unified Star Schema or Bridge Table.
2. **Absence of DAX:** The data model contains **0 custom DAX measures**.
3. **Severe Flaws in Calculations:**
   - **No Cost Engineering:** The project never multiplied consumption by tariff rates. Total utility expenditure ($) was never calculated anywhere in Power BI.
   - **Meaningless Aggregations:** Power BI auto-summarized dimension attributes, resulting in visuals showing `Sum(Rates.Year)` (summing year numbers like 2016+2017 = 4033) and `Sum(Rates.Price Per Unit)`.
   - **Incommensurable Unit Sums:** In several pie and column charts, Water (gallons), Electricity (kWh), and Gas (therms) were summed together into an arbitrary number.
   - **Misconfigured Visuals:** A gauge chart utilized `MinValue: Sum(Gas Consumption)` and `Target: Sum(Electricity Consumption)`.

---

## 6. Existing Documentation & Presentations

- **`Energy Consumption and Trend Analysis.pptx`:** Standard 8-slide presentation summarizing problem statement, methodology, and conclusion. Slide 7 contained a placeholder graphic instead of actual dashboard screenshots with analytical callouts.
- **`Data Analytics Assignment 1.xlsx` / `.pdf`:** Excel pivot tables summarizing total water, gas, and electricity consumption by building and month, but completely lacking cost modeling or growth rates.
- **`Project_exp.pdf` & LMS Documents:** Operational guidance for internship completion.

---

## 7. Limitations of Original Project

1. **No Utility Cost Analytics:** Despite having the `Rates` table, financial cost impact was never calculated.
2. **No Growth Metrics:** No Month-over-Month (MoM) or Year-over-Year (YoY) percentage changes.
3. **No Price vs. Volume Decomposition:** Inability to explain whether cost increases stemmed from higher consumption or tariff hikes.
4. **No Data Validation or SQL Pipeline:** Relied strictly on manual Excel manipulation without reproducible Python scripts or SQL queries.
5. **No Statistical Outlier / Anomaly Detection:** No objective identification of operational anomalies versus seasonal spikes.
6. **No Executive-Level Narrative:** Visuals were disjointed charts without business takeaways.

---

## 8. Governance: What is Preserved vs. What is Upgraded

### What Will Be Preserved Untouched
- All 15 original workspace files: `Energy Consumption Data.xlsx`, `Data Analytics Assignment 1.xlsx`, all 3 `.pbix` files, both `.pptx` presentations, all 5 `.pdf` files, and all 3 `.jpg` images.
- File timestamps, original names, and folder locations remain 100% unaltered.

### What Will Be Upgraded in `energy-business-analytics/`
1. **Reproducible Python Pipeline:** Modular architecture (`src/`) for validation, preprocessing, cost modeling, KPI generation, and anomaly detection.
2. **Audited Data Layers:** Clean data stored in `data/processed/` with joined geography, rate dimensions, calendar hierarchies, and calculated costs.
3. **Relational SQL Suite:** Over 20 business-driven analytical SQL queries using advanced CTEs, Window Functions (`RANK`, `DENSE_RANK`, `LAG`, `LEAD`, rolling frames).
4. **Price vs. Volume Analysis:** Rigorous decomposition quantifying tariff inflation effect vs. operational efficiency effect.
5. **Jupyter Notebooks:** Executable, documented notebooks for audit, data prep, and exploratory analysis.
6. **Executive Reporting & Validation:** Business insights report, methodology whitepaper, limitations document, and automated reconciliation test report.
7. **Production DAX & Power BI Upgrade:** A documented enterprise semantic model with standardized DAX measures and page-by-page visual blueprint.

---

## 9. Baseline Reconciliation Numbers (Ground Truth Benchmark)

These exact verified metrics will be used to reconcile all downstream Python, SQL, and Power BI models:

- **Total Consumption:**
  - Water: `186,245,327` units
  - Electricity: `21,666,978` kWh
  - Gas: `2,553,088` units
- **Total Expenditure (USD):**
  - Water Cost: `$10,806,192.07` (68.21% of total spend)
  - Electricity Cost: `$2,025,296.02` (12.78% of total spend)
  - Gas Cost: `$3,011,010.87` (19.01% of total spend)
  - **Total Utility Cost:** **`$15,842,498.96`**
- **Annual Cost Progression:**
  - 2016: `$3,158,569.30`
  - 2017: `$3,754,627.63` (+18.87%)
  - 2018: `$4,234,291.43` (+12.78%)
  - 2019: `$4,695,010.60` (+10.88%)
  - Cumulative 4-Year Cost Growth: **+48.64%**
- **Top Cost Building:** `B1008` (Chicago) — `$1,496,830.40`
- **Lowest Cost Building:** `B1007` (Chicago) — `$1,356,651.48`
- **Highest Cost Per Building City:** `Phoenix` — `$1,479,068.04` (1 building)

---
*Signed and Approved for Project Execution.*
