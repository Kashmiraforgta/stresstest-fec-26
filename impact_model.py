"""
Phase 3 — Financial Impact Model
Run: python src/impact_model.py
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import warnings; warnings.filterwarnings("ignore")
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config import BANKS, FY24_ACTUALS, SCENARIOS, RBI_FLOORS, DSIB_BANKS, CHART_DIR

os.makedirs(CHART_DIR, exist_ok=True)

# ── Core stress engine ────────────────────────────────────────────────────────
def compute_stressed(bank_key, scenario_key):
    """Apply scenario shocks to FY24 actuals. Returns stressed dict."""
    base   = FY24_ACTUALS[bank_key].copy()
    shocks = SCENARIOS[scenario_key]
    car_floor = RBI_FLOORS["car_min_dsib"] if bank_key in DSIB_BANKS else RBI_FLOORS["car_min"]

    stressed = {
        "gnpa": base["gnpa"] + shocks["gnpa_shock"],
        "nnpa": max(0, base["nnpa"] * (1 + shocks["gnpa_shock"] / base["gnpa"]) * (1 - shocks["pcr_shock"]/100)),
        "nim":  base["nim"]  + shocks["nim_shock"],
        "car":  base["car"]  + shocks["car_shock"],
        "tier1":base["tier1"]+ shocks["car_shock"] * 0.8,   # tier1 absorbs ~80% of CAR shock
        "roa":  base["roa"]  + shocks["roa_shock"],
        "roe":  base["roe"]  + shocks["roa_shock"] * 10,    # rough ROE multiplier
        "pcr":  max(0, base["pcr"] + shocks["pcr_shock"]),
    }
    stressed["car_breach"]  = stressed["car"]  < car_floor
    stressed["tier1_breach"]= stressed["tier1"]< RBI_FLOORS["tier1_min"]
    stressed["roa_negative"]= stressed["roa"]  < 0
    stressed["car_floor"]   = car_floor
    return stressed

# ── Build full results table ─────────────────────────────────────────────────
def build_results():
    rows = []
    for bkey in BANKS:
        for sc in SCENARIOS:
            s = compute_stressed(bkey, sc)
            rows.append({
                "bank": bkey, "type": BANKS[bkey]["type"], "scenario": sc,
                **{k: round(v, 2) for k, v in s.items() if not isinstance(v, bool)},
                "car_breach": s["car_breach"],
                "tier1_breach": s["tier1_breach"],
                "roa_negative": s["roa_negative"],
            })
    return pd.DataFrame(rows)

# ── Plots ────────────────────────────────────────────────────────────────────
def plot_stressed_car(df):
    fig, axes = plt.subplots(1, 4, figsize=(16, 5), sharey=False)
    colors = {"Baseline":"#2196F3","Moderate_Stress":"#FF9800","Severe_Stress":"#F44336"}
    for ax, (bkey, grp) in zip(axes, df.groupby("bank")):
        vals = [grp[grp.scenario==s]["car"].values[0] for s in SCENARIOS]
        bars = ax.bar(list(SCENARIOS.keys()), vals, color=list(colors.values()), width=0.5, edgecolor="white")
        car_floor = RBI_FLOORS["car_min_dsib"] if bkey in DSIB_BANKS else RBI_FLOORS["car_min"]
        ax.axhline(y=car_floor, color="red", linestyle="--", linewidth=1.5, label=f"RBI Min ({car_floor}%)")
        ax.set_title(bkey, fontweight="bold")
        ax.set_xticklabels(["Base","Moderate","Severe"], fontsize=8)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.legend(fontsize=7); ax.grid(axis="y", alpha=0.3)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1, f"{v:.1f}%", ha="center", fontsize=8)
    fig.suptitle("Stressed CAR % — All Banks × All Scenarios", fontsize=13, fontweight="bold")
    plt.tight_layout(); plt.savefig(f"{CHART_DIR}/stressed_car.png", dpi=150); plt.close()
    print(f"Saved: {CHART_DIR}/stressed_car.png")

def plot_stressed_gnpa(df):
    fig, ax = plt.subplots(figsize=(11, 5))
    x = range(len(BANKS)); width = 0.25
    colors = {"Baseline":"#2196F3","Moderate_Stress":"#FF9800","Severe_Stress":"#F44336"}
    for i, (sc, color) in enumerate(colors.items()):
        vals = [df[(df.bank==b)&(df.scenario==sc)]["gnpa"].values[0] for b in BANKS]
        bars = ax.bar([xi + i*width for xi in x], vals, width, label=sc, color=color, edgecolor="white")
    ax.axhline(y=9.0, color="darkred", linestyle="--", linewidth=1.5, label="Indicative stress ceiling 9%")
    ax.set_xticks([xi + width for xi in x]); ax.set_xticklabels(list(BANKS.keys()))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_title("Stressed GNPA % — All Scenarios", fontsize=13, fontweight="bold")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout(); plt.savefig(f"{CHART_DIR}/stressed_gnpa.png", dpi=150); plt.close()
    print(f"Saved: {CHART_DIR}/stressed_gnpa.png")

# ── Scorecard ────────────────────────────────────────────────────────────────
def resilience_scorecard(df):
    """
    Simple composite score (0-100) per bank under severe stress.
    Higher = more resilient.
    """
    severe = df[df.scenario == "Severe_Stress"].copy()
    severe = severe.set_index("bank")
    scores = {}
    for bkey in BANKS:
        row = severe.loc[bkey]
        s = 0
        s += max(0, (9.0 - row["gnpa"]) * 5)           # lower GNPA → better
        s += min(20, row["car"] * 1.2)                   # higher CAR → better
        s += max(0, row["roa"] * 20)                     # positive ROA → better
        s += min(15, row["nim"] * 3)                     # higher NIM = buffer
        s += min(10, row["pcr"] / 10)                    # higher PCR = better
        scores[bkey] = round(min(100, s), 1)
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    print("\n" + "="*45)
    print("  RESILIENCE SCORECARD (Severe Stress)")
    print("="*45)
    for rank, (bank, score) in enumerate(ranked, 1):
        t = BANKS[bank]["type"]
        print(f"  #{rank}  {bank:<10} ({t:<7})  Score: {score}/100")
    print("="*45)
    return scores

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = build_results()
    df.to_csv("data/processed/stressed_results.csv", index=False)
    print("Stressed results saved → data/processed/stressed_results.csv")
    print("\nFull impact table:\n")
    print(df[["bank","scenario","gnpa","nim","car","roa","car_breach","roa_negative"]].to_string(index=False))
    plot_stressed_car(df)
    plot_stressed_gnpa(df)
    resilience_scorecard(df)
