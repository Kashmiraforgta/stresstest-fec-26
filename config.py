
BANKS = {
    "SBI":   {"label": "State Bank of India",   "type": "PSU"},
    "BOM":   {"label": "Bank of Maharashtra",   "type": "PSU"},
    "HDFC":  {"label": "HDFC Bank",             "type": "Private"},
    "Kotak": {"label": "Kotak Mahindra Bank",   "type": "Private"},
}


FY24_ACTUALS = {
    "SBI":   {"gnpa":2.24,"nnpa":0.57,"nim":3.28,"car":14.28,"tier1":10.36,"roa":1.04,"roe":20.32,"pcr":75.0},
    "BOM":   {"gnpa":1.88,"nnpa":0.20,"nim":3.60,"car":17.38,"tier1":14.50,"roa":1.24,"roe":20.10,"pcr":98.2},
    "HDFC":  {"gnpa":1.24,"nnpa":0.33,"nim":3.46,"car":18.80,"tier1":17.50,"roa":1.90,"roe":16.50,"pcr":70.0},
    "Kotak": {"gnpa":1.73,"nnpa":0.34,"nim":4.97,"car":21.80,"tier1":20.70,"roa":2.30,"roe":14.10,"pcr":75.0},
}

SCENARIOS = {
    "Baseline": {
        "gnpa_shock":0.0, "nim_shock":0.0, "car_shock":0.0,
        "roa_shock":0.0,  "pcr_shock":0.0, "credit_cost_mult":1.0,
    },
    "Moderate_Stress": {
        "gnpa_shock":2.50, "nim_shock":-0.40, "car_shock":-1.20,
        "roa_shock":-0.50, "pcr_shock":-5.0,  "credit_cost_mult":1.80,
    },
    "Severe_Stress": {
        "gnpa_shock":4.50, "nim_shock":-0.70, "car_shock":-2.50,
        "roa_shock":-1.20, "pcr_shock":-10.0, "credit_cost_mult":3.00,
    },
}

RBI_FLOORS = {
    "car_min":       9.0,
    "car_min_dsib":  9.2,   
    "tier1_min":     7.0,
    "pcr_guidance":  70.0,
}

DSIB_BANKS = ["HDFC"]  

DATA_DIR    = "data/raw"
PROC_DIR    = "data/processed"
OUTPUT_DIR  = "outputs"
CHART_DIR   = "outputs/charts"
