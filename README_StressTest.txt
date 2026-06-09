
STRESSTEST – Project File Index
Finance & Economics Club · IIT Guwahati · DIY 2026
=======================================================

BANKS SELECTED
--------------
  PSU     : SBI (State Bank of India)
            Bank of Maharashtra (BoM)
  Private : HDFC Bank
            Kotak Mahindra Bank

FILES IN THIS PACKAGE
----------------------

1. StressTest_BankDataset.xlsx
   → Master Excel workbook (7 sheets)
   Sheets:
     Cover          – project overview & sheet index
     Master Dataset – all 4 banks, all 8 metrics, FY20–FY24
                      (colour-coded: green=good, amber=caution, red=stressed)
     SBI            – detailed SBI history + YoY changes + data notes
     BOM            – detailed BoM history
     HDFC           – detailed HDFC history
     Kotak          – detailed Kotak history
     Crosscheck     – source verification table (27 data points verified)
     CSV_Export     – flat table for direct Python/model import
     Charts         – 4 exploratory charts embedded

2. stresstest_master.csv
   → Long-format: bank_code | bank_name | bank_type | metric | category | FY20–FY24
   → Use for: metric-wise analysis, filtering, charting

3. stresstest_wide.csv
   → Wide-format: one row per bank-year (40 rows × 12 cols)
   → Use for: ML features, scenario modelling, pandas analysis

4. stresstest_sbi.csv       – SBI only
   stresstest_bom.csv       – Bank of Maharashtra only
   stresstest_hdfc.csv      – HDFC Bank only
   stresstest_kotak.csv     – Kotak Mahindra only
   → Use for: individual bank deep-dives

5. stresstest_loader.py
   → Python starter script
   → Loads both CSVs, prints FY24 snapshot, generates 4 plots
   → Run: python stresstest_loader.py
   → Requires: pip install pandas matplotlib seaborn openpyxl

PLOTS GENERATED (also embedded in Excel → Charts sheet)
---------------------------------------------------------
   plot_gnpa_trend.png       – GNPA % trajectory FY20–FY24
   plot_car_trend.png        – CAR % vs RBI minimum
   plot_roa_trend.png        – ROA % trajectory
   plot_fy24_comparison.png  – FY24 bar comparison (6 metrics)

KEY METRICS TRACKED
-------------------
  GNPA %    Gross NPA / Gross Advances          (Asset Quality)
  NNPA %    Net NPA / Net Advances               (Asset Quality)
  NIM %     Net Interest Margin                  (Profitability)
  CAR %     Capital Adequacy Ratio (Basel III)   (Capital)
  Tier-1 %  Tier-1 Capital Ratio                 (Capital)
  ROA %     Return on Assets                     (Profitability)
  ROE %     Return on Equity                     (Profitability)
  PCR %     Provision Coverage Ratio             (Asset Quality)

RBI REGULATORY FLOORS (for stress testing reference)
-----------------------------------------------------
  Minimum CAR        : 9.0%
  Minimum Tier-1     : 7.0%
  D-SIB surcharge    : +0.20% (applies to HDFC Bank)

DATA SOURCES
------------
  SBI        : SBI Annual Reports FY20–FY24; IJSREM26618 (peer-reviewed)
  BoM        : ICRA Rating Report Jun 2024; Business Standard May 2023
  HDFC Bank  : HDFC 6-K SEC filings; toptradetrends FY24 analysis
  Kotak      : ICRA Rating Report Jun 2024; Business Standard quarterly

NEXT STEP → Phase 2: Scenario Design
--------------------------------------
  Build assumption table for 3 scenarios:
    Scenario 1 (Baseline)       – FY24 actuals as starting point
    Scenario 2 (Moderate Stress)– COVID FY2020-21 shock parameters
    Scenario 3 (Severe Stress)  – 2015-16 NPA crisis + 100bps rate hike

  Key shock variables to define:
    ΔGNPA (bps), ΔNIM (bps), ΔCAR (bps), ΔROA, credit cost multiplier

=======================================================
