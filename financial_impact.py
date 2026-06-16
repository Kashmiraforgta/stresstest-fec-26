
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patches as mpatches
import os, sys, warnings
warnings.filterwarnings("ignore")

BALANCE_SHEET = {
    # SBI FY24: Total Assets ~₹61 lakh cr, Advances ₹37.7 lakh cr
    # RWA back-calc: 42% of total assets = ₹25.6 lakh cr (consistent with Tier-1 10.36% * RWA = Tier-1 capital)
    "SBI": {
        "gross_advances":   3_77_000,
        "total_assets":     61_00_000,
        "tier1_capital":    2_65_423,   
        "tier2_capital":    1_00_430,   
        "rwa":              25_62_000,
        "nii_baseline":     1_41_000,
        "non_ii":           57_000,
        "opex":             1_07_000,
        "tax_rate":         0.25,
        "retention_ratio":  0.75,
    },
    # BOM FY24: Total Assets ₹3.40 lakh cr
    # RWA ~44% of total assets = ₹1.50 lakh cr
    "BOM": {
        "gross_advances":   2_16_000,
        "total_assets":     3_40_000,
        "tier1_capital":    21_692,     
        "tier2_capital":    4_308,
        "rwa":              1_49_600,
        "nii_baseline":     8_700,
        "non_ii":           2_100,
        "opex":             5_800,
        "tax_rate":         0.25,
        "retention_ratio":  0.80,
    },
    # HDFC FY24: Total Assets ₹36.17 lakh cr (post-merger)
    # RWA ~57% of total assets = ₹20.6 lakh cr
    "HDFC": {
        "gross_advances":   25_19_000,
        "total_assets":     36_17_000,
        "tier1_capital":    3_60_796,   
        "tier2_capital":    26_802,
        "rwa":              20_61_690,
        "nii_baseline":     89_500,
        "non_ii":           42_000,
        "opex":             68_000,
        "tax_rate":         0.25,
        "retention_ratio":  0.85,
    },
    # Kotak FY24: Total Assets ₹6.60 lakh cr
    # RWA ~57% of total assets = ₹3.76 lakh cr
    "Kotak": {
        "gross_advances":   4_19_000,
        "total_assets":     6_60_000,
        "tier1_capital":    77_873,     
        "tier2_capital":    4_138,
        "rwa":              3_76_200,
        "nii_baseline":     24_600,
        "non_ii":           12_500,
        "opex":             18_800,
        "tax_rate":         0.25,
        "retention_ratio":  0.80,
    },
}

FY24 = {
    "SBI":   {"gnpa":2.24,"nim":3.28,"car":14.28,"tier1":10.36,"roa":1.04,"pcr":75.0},
    "BOM":   {"gnpa":1.88,"nim":3.60,"car":17.38,"tier1":14.50,"roa":1.24,"pcr":98.2},
    "HDFC":  {"gnpa":1.24,"nim":3.46,"car":18.80,"tier1":17.50,"roa":1.90,"pcr":70.0},
    "Kotak": {"gnpa":1.73,"nim":4.97,"car":21.80,"tier1":20.70,"roa":2.30,"pcr":75.0},
}

SCENARIOS = {
    "Baseline":        {"gnpa_shock":0.00, "nim_shock":0.00, "pcr_compression":0.0,  "credit_cost_mult":1.00},
    "Moderate_Stress": {"gnpa_shock":2.50, "nim_shock":-0.40,"pcr_compression":5.0,  "credit_cost_mult":1.80},
    "Severe_Stress":   {"gnpa_shock":4.50, "nim_shock":-0.70,"pcr_compression":10.0, "credit_cost_mult":3.00},
}

RBI_MIN_CAR   = {"SBI":9.0,"BOM":9.0,"HDFC":9.2,"Kotak":9.0}
RBI_MIN_TIER1 = 7.0
BANKS = ["SBI","BOM","HDFC","Kotak"]
BANK_TYPES = {"SBI":"PSU","BOM":"PSU","HDFC":"Private","Kotak":"Private"}

os.makedirs("outputs/charts", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
def run_transmission(bank, scenario):
    """
    Full P&L and capital transmission chain.
    Returns a dict with every intermediate step so nothing is a black box.
    """
    bs   = BALANCE_SHEET[bank]
    base = FY24[bank]
    sc   = SCENARIOS[scenario]

    adv  = bs["gross_advances"]
    car_floor = RBI_MIN_CAR[bank]

    gnpa_base_pct      = base["gnpa"]
    gnpa_stressed_pct  = gnpa_base_pct + sc["gnpa_shock"]
    gnpa_base_cr       = adv * gnpa_base_pct / 100
    gnpa_stressed_cr   = adv * gnpa_stressed_pct / 100
    incremental_npa_cr = gnpa_stressed_cr - gnpa_base_cr   
    pcr_base      = base["pcr"]
    pcr_stressed  = max(50.0, pcr_base - sc["pcr_compression"])  
    incr_prov_cr  = incremental_npa_cr * (pcr_stressed / 100)
    baseline_prov_cr = gnpa_base_cr * (pcr_base / 100) * 0.25  
    total_prov_stressed = baseline_prov_cr * sc["credit_cost_mult"] + incr_prov_cr
    nim_base      = base["nim"]
    nim_stressed  = nim_base + sc["nim_shock"]
    interest_earning_assets = bs["total_assets"] * 0.80
    nii_baseline  = bs["nii_baseline"]
    nii_stressed  = nii_baseline * (nim_stressed / nim_base)   
    nii_delta     = nii_stressed - nii_baseline                 
    ppop_baseline = nii_baseline + bs["non_ii"] - bs["opex"]
    ppop_stressed = nii_stressed + bs["non_ii"] - bs["opex"]  
    pbt_stressed  = ppop_stressed - total_prov_stressed
    tax_stressed  = max(0, pbt_stressed * bs["tax_rate"])
    pat_stressed  = pbt_stressed - tax_stressed
    baseline_prov    = baseline_prov_cr * 1.0
    pbt_baseline     = ppop_baseline - baseline_prov
    pat_baseline     = pbt_baseline * (1 - bs["tax_rate"])
    pat_delta         = pat_stressed - pat_baseline            
    retained_delta    = pat_delta * bs["retention_ratio"]
    tier1_baseline_cr = bs["tier1_capital"]
    tier1_stressed_cr = tier1_baseline_cr + retained_delta    
    rwa_baseline   = bs["rwa"]
    rwa_uplift     = incremental_npa_cr * (1.50 - 0.75) 
    rwa_stressed   = rwa_baseline + rwa_uplift
    tier2_cr          = bs["tier2_capital"]
    total_cap_stressed= tier1_stressed_cr + tier2_cr
    car_stressed_pct  = (total_cap_stressed / rwa_stressed) * 100
    tier1_stressed_pct= (tier1_stressed_cr  / rwa_stressed) * 100
    roa_stressed_pct  = (pat_stressed / bs["total_assets"]) * 100
    car_breach   = car_stressed_pct  < car_floor
    tier1_breach = tier1_stressed_pct < RBI_MIN_TIER1
    roa_negative = pat_stressed < 0

    return {
        
        "bank": bank, "scenario": scenario, "bank_type": BANK_TYPES[bank],
        
        "gnpa_base_pct":       round(gnpa_base_pct, 2),
        "gnpa_stressed_pct":   round(gnpa_stressed_pct, 2),
        "incremental_npa_cr":  round(incremental_npa_cr, 0),
    
        "pcr_base":            round(pcr_base, 1),
        "pcr_stressed":        round(pcr_stressed, 1),
        "incr_prov_cr":        round(incr_prov_cr, 0),
        "total_prov_stressed": round(total_prov_stressed, 0),
        "baseline_prov_cr":    round(baseline_prov_cr, 0),
        
        "nim_base":            round(nim_base, 2),
        "nim_stressed":        round(nim_stressed, 2),
        "nii_baseline_cr":     round(nii_baseline, 0),
        "nii_stressed_cr":     round(nii_stressed, 0),
        "nii_delta_cr":        round(nii_delta, 0),
        
        "ppop_baseline_cr":    round(ppop_baseline, 0),
        "ppop_stressed_cr":    round(ppop_stressed, 0),
        
        "pat_baseline_cr":     round(pat_baseline, 0),
        "pat_stressed_cr":     round(pat_stressed, 0),
        "pat_delta_cr":        round(pat_delta, 0),
        
        "tier1_baseline_cr":   round(tier1_baseline_cr, 0),
        "tier1_stressed_cr":   round(tier1_stressed_cr, 0),
        "retained_delta_cr":   round(retained_delta, 0),
        
        "rwa_baseline_cr":     round(rwa_baseline, 0),
        "rwa_stressed_cr":     round(rwa_stressed, 0),
        "rwa_uplift_cr":       round(rwa_uplift, 0),
    
        "car_baseline_pct":    round(base["car"], 2),
        "car_stressed_pct":    round(car_stressed_pct, 2),
        "tier1_stressed_pct":  round(tier1_stressed_pct, 2),
        "car_floor":           car_floor,
        "car_buffer_cr":       round(car_stressed_pct - car_floor, 2),

        "roa_baseline_pct":    round(base["roa"], 2),
        "roa_stressed_pct":    round(roa_stressed_pct, 2),
        
        "car_breach":    car_breach,
        "tier1_breach":  tier1_breach,
        "roa_negative":  roa_negative,
    }

def print_transmission(r):
    sep = "─" * 62
    print(f"\n{'═'*62}")
    print(f"  {r['bank']}  ({r['bank_type']})  ·  {r['scenario']}")
    print(f"{'═'*62}")
    print(f"  Step 1 │ GNPA Shock")
    print(f"         │  Base GNPA        : {r['gnpa_base_pct']:.2f}%")
    print(f"         │  Stressed GNPA    : {r['gnpa_stressed_pct']:.2f}%")
    print(f"         │  Incremental NPA  : ₹{r['incremental_npa_cr']:,.0f} cr")
    print(sep)
    print(f"  Step 2 │ Provisioning Requirement")
    print(f"         │  PCR base → stressed : {r['pcr_base']:.1f}% → {r['pcr_stressed']:.1f}%")
    print(f"         │  Incremental prov    : ₹{r['incr_prov_cr']:,.0f} cr")
    print(f"         │  Total stressed prov : ₹{r['total_prov_stressed']:,.0f} cr")
    print(sep)
    print(f"  Step 3 │ NIM Compression → NII Impact")
    print(f"         │  NIM base → stressed : {r['nim_base']:.2f}% → {r['nim_stressed']:.2f}%")
    print(f"         │  NII baseline        : ₹{r['nii_baseline_cr']:,.0f} cr")
    print(f"         │  NII stressed        : ₹{r['nii_stressed_cr']:,.0f} cr")
    print(f"         │  NII delta           : ₹{r['nii_delta_cr']:,.0f} cr")
    print(sep)
    print(f"  Step 4 │ Pre-Provision Operating Profit")
    print(f"         │  PPOP baseline : ₹{r['ppop_baseline_cr']:,.0f} cr")
    print(f"         │  PPOP stressed : ₹{r['ppop_stressed_cr']:,.0f} cr")
    print(sep)
    print(f"  Step 5 │ Stressed PAT")
    print(f"         │  PAT baseline  : ₹{r['pat_baseline_cr']:,.0f} cr")
    print(f"         │  PAT stressed  : ₹{r['pat_stressed_cr']:,.0f} cr  {'⚠ LOSS' if r['roa_negative'] else '✓'}")
    print(f"         │  PAT delta     : ₹{r['pat_delta_cr']:,.0f} cr")
    print(sep)
    print(f"  Step 6 │ Tier-1 Capital Erosion")
    print(f"         │  Tier-1 baseline  : ₹{r['tier1_baseline_cr']:,.0f} cr")
    print(f"         │  Retained Δ       : ₹{r['retained_delta_cr']:,.0f} cr")
    print(f"         │  Tier-1 stressed  : ₹{r['tier1_stressed_cr']:,.0f} cr")
    print(sep)
    print(f"  Step 7 │ RWA Uplift (NPA reclassification)")
    print(f"         │  RWA baseline : ₹{r['rwa_baseline_cr']:,.0f} cr")
    print(f"         │  RWA uplift   : ₹{r['rwa_uplift_cr']:,.0f} cr")
    print(f"         │  RWA stressed : ₹{r['rwa_stressed_cr']:,.0f} cr")
    print(sep)
    print(f"  Step 8 │ Stressed CAR")
    print(f"         │  CAR baseline  : {r['car_baseline_pct']:.2f}%")
    print(f"         │  CAR stressed  : {r['car_stressed_pct']:.2f}%  (RBI floor: {r['car_floor']}%)")
    print(f"         │  Buffer above floor: {r['car_buffer_cr']:.2f} pp  {'⚠ BREACH' if r['car_breach'] else '✓ Safe'}")
    print(sep)
    print(f"  Step 9 │ Stressed ROA")
    print(f"         │  ROA baseline : {r['roa_baseline_pct']:.2f}%")
    print(f"         │  ROA stressed : {r['roa_stressed_pct']:.2f}%  {'⚠ NEGATIVE' if r['roa_negative'] else '✓'}")
    print(f"{'═'*62}")

COLORS = {"Baseline":"#4CAF50","Moderate_Stress":"#FF9800","Severe_Stress":"#F44336"}
BANK_COLORS = {"SBI":"#1B4332","BOM":"#2D6A4F","HDFC":"#1A3A5C","Kotak":"#2C5F8A"}

def plot_pat_waterfall(results):
    """Waterfall chart: how PAT erodes from baseline to severe stress for each bank."""
    fig, axes = plt.subplots(1, 4, figsize=(18, 6))
    for ax, bank in zip(axes, BANKS):
        sc_results = {sc: next(r for r in results if r["bank"]==bank and r["scenario"]==sc)
                      for sc in SCENARIOS}
        pat_vals = [sc_results[sc]["pat_stressed_cr"] / 1000 for sc in SCENARIOS]  # ₹ '000 cr
        labels   = ["Baseline", "Moderate", "Severe"]
        bar_colors = [COLORS[sc] for sc in SCENARIOS]
        bars = ax.bar(labels, pat_vals, color=bar_colors, width=0.5, edgecolor="white", linewidth=0.8)
        ax.axhline(0, color="red", linewidth=1.2, linestyle="--", alpha=0.7)
        ax.set_title(f"{bank}\n({BANK_TYPES[bank]})", fontweight="bold", fontsize=11)
        ax.set_ylabel("PAT (₹ '000 cr)")
        ax.grid(axis="y", alpha=0.3)
        for bar, v in zip(bars, pat_vals):
            ax.text(bar.get_x()+bar.get_width()/2,
                    bar.get_height() + (0.05 if v >= 0 else -0.15),
                    f"₹{v:.1f}k cr", ha="center", fontsize=8,
                    color="black")
    fig.suptitle("Stressed PAT (₹ '000 cr) — P&L Transmission Impact", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("outputs/charts/pat_transmission.png", dpi=150); plt.close()
    print("Saved: outputs/charts/pat_transmission.png")

def plot_car_waterfall(results):
    fig, ax = plt.subplots(figsize=(13, 6))
    x = range(len(BANKS)); width = 0.22
    for i, sc in enumerate(SCENARIOS):
        vals = [next(r for r in results if r["bank"]==b and r["scenario"]==sc)["car_stressed_pct"]
                for b in BANKS]
        offset = [xi + i*width for xi in x]
        bars = ax.bar(offset, vals, width, label=sc.replace("_"," "),
                      color=COLORS[sc], edgecolor="white", linewidth=0.8)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
                    f"{v:.1f}%", ha="center", fontsize=7.5)
    ax.axhline(9.0,  color="darkred",  linestyle="--", linewidth=1.5, label="RBI Min CAR (9%)")
    ax.axhline(9.2,  color="red",      linestyle=":",  linewidth=1.2, label="D-SIB floor HDFC (9.2%)")
    ax.axhline(11.5, color="orange",   linestyle=":",  linewidth=1.0, label="Early warning (11.5%)", alpha=0.7)
    ax.set_xticks([xi + width for xi in x]); ax.set_xticklabels(BANKS, fontsize=11)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_title("Stressed CAR % — P&L Transmission Model", fontsize=13, fontweight="bold")
    ax.set_ylabel("Capital Adequacy Ratio (%)")
    ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/charts/car_transmission.png", dpi=150); plt.close()
    print("Saved: outputs/charts/car_transmission.png")

def plot_tier1_erosion(results):
    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    for ax, bank in zip(axes, BANKS):
        sc_list = list(SCENARIOS.keys())
        t1_vals = [next(r for r in results if r["bank"]==bank and r["scenario"]==sc)["tier1_stressed_cr"] / 1000
                   for sc in sc_list]
        t1_floor_cr = (RBI_MIN_TIER1/100) * next(
            r for r in results if r["bank"]==bank and r["scenario"]=="Baseline")["rwa_baseline_cr"] / 1000
        bars = ax.bar(["Base","Moderate","Severe"], t1_vals,
                      color=[COLORS[s] for s in sc_list], width=0.5, edgecolor="white")
        ax.axhline(t1_floor_cr, color="red", linestyle="--", linewidth=1.3,
                   label=f"RBI Tier-1 floor ≈ ₹{t1_floor_cr:.0f}k cr")
        ax.set_title(f"{bank}", fontweight="bold")
        ax.set_ylabel("Tier-1 Capital (₹ '000 cr)")
        ax.legend(fontsize=7); ax.grid(axis="y", alpha=0.3)
        for bar, v in zip(bars, t1_vals):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
                    f"₹{v:.0f}k", ha="center", fontsize=8)
    fig.suptitle("Tier-1 Capital Erosion — All Scenarios", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("outputs/charts/tier1_erosion.png", dpi=150); plt.close()
    print("Saved: outputs/charts/tier1_erosion.png")

def plot_transmission_chain(results):
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    axes = axes.flatten()
    for ax, bank in zip(axes, BANKS):
        r = next(x for x in results if x["bank"]==bank and x["scenario"]=="Severe_Stress")
        b = next(x for x in results if x["bank"]==bank and x["scenario"]=="Baseline")
        steps  = ["NII\nBaseline","NII\nStressed","PPOP\nStressed","PAT\nStressed"]
        values = [b["nii_baseline_cr"]/1000, r["nii_stressed_cr"]/1000,
                  r["ppop_stressed_cr"]/1000, r["pat_stressed_cr"]/1000]
        bar_c  = ["#4CAF50","#FF9800","#FF5722",
                  "#F44336" if r["roa_negative"] else "#E91E63"]
        bars = ax.bar(steps, values, color=bar_c, width=0.5, edgecolor="white")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(f"{bank} — P&L Chain (Severe Stress)", fontweight="bold", fontsize=11)
        ax.set_ylabel("₹ '000 cr"); ax.grid(axis="y", alpha=0.3)
        for bar, v in zip(bars, values):
            ax.text(bar.get_x()+bar.get_width()/2,
                    bar.get_height() + (0.02 if v >= 0 else -0.08),
                    f"₹{v:.1f}k", ha="center", fontsize=9)
        info = (f"CAR: {r['car_stressed_pct']:.1f}%  "
                f"{'⚠ BREACH' if r['car_breach'] else '✓'}\n"
                f"ROA: {r['roa_stressed_pct']:.2f}%  "
                f"{'⚠ LOSS' if r['roa_negative'] else '✓'}")
        ax.text(0.98, 0.04, info, transform=ax.transAxes, fontsize=9,
                ha="right", va="bottom",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3CD", alpha=0.8))
    fig.suptitle("P&L Transmission Chain — Severe Stress (per bank)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("outputs/charts/pl_chain_severe.png", dpi=150); plt.close()
    print("Saved: outputs/charts/pl_chain_severe.png")

def resilience_scorecard(results):
    severe = {r["bank"]: r for r in results if r["scenario"]=="Severe_Stress"}
    print(f"\n{'═'*70}")
    print(f"  RESILIENCE SCORECARD  —  Severe Stress  (P&L Transmission Model)")
    print(f"{'═'*70}")
    print(f"  {'Bank':<8}  {'Type':<8}  {'CAR buf':>8}  {'NIM buf':>8}  "
          f"{'ROA':>8}  {'PCR':>8}  {'Score':>8}")
    print(f"  {'─'*64}")

    scores = {}
    for bank in BANKS:
        r = severe[bank]
        car_buf   = r["car_stressed_pct"] - r["car_floor"]    
        nim_buf   = r["nim_stressed"] - 2.0                   
        roa       = r["roa_stressed_pct"]
        pcr       = r["pcr_stressed"]
        s_car  = min(25, car_buf  * 2.5)    
        s_nim  = min(20, nim_buf  * 3.0)     
        s_roa  = min(25, max(0, roa * 15))  
        s_pcr  = min(15, pcr / 6.67)         
        s_type = 15 if BANK_TYPES[bank]=="Private" else 10  
        total  = round(s_car + s_nim + s_roa + s_pcr + s_type, 1)
        scores[bank] = total

        flag = " ⚠ LOSS" if r["roa_negative"] else ""
        print(f"  {bank:<8}  {BANK_TYPES[bank]:<8}  {car_buf:>7.2f}pp  "
              f"{nim_buf:>7.2f}pp  {roa:>7.2f}%  {pcr:>7.1f}%  {total:>7.1f}{flag}")

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    print(f"\n  Ranking:  " + "  >  ".join([f"#{i+1} {b} ({s})" for i,(b,s) in enumerate(ranked)]))
    print(f"{'═'*70}")
    return scores

if __name__ == "__main__":
    results = []
    for bank in BANKS:
        for sc in SCENARIOS:
            results.append(run_transmission(bank, sc))
    df = pd.DataFrame(results)
    df.to_csv("data/processed/pl_transmission_results.csv", index=False)
    print("Saved: data/processed/pl_transmission_results.csv")
    print("\n" + "█"*62)
    print("  STEP-BY-STEP TRANSMISSION  —  SEVERE STRESS")
    print("█"*62)
    for bank in BANKS:
        r = next(x for x in results if x["bank"]==bank and x["scenario"]=="Severe_Stress")
        print_transmission(r)
    print("\nGenerating charts...")
    plot_pat_waterfall(results)
    plot_car_waterfall(results)
    plot_tier1_erosion(results)
    plot_transmission_chain(results)
    resilience_scorecard(results)