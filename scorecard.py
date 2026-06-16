
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
import numpy as np
import os, sys, warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(__file__))
from config import BANKS, FY24_ACTUALS, RBI_FLOORS, DSIB_BANKS
from financial_impact import run_transmission, SCENARIOS, BALANCE_SHEET

os.makedirs("outputs/charts", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

BANK_COLORS = {"SBI": "#1B4332", "BOM": "#2D6A4F", "HDFC": "#1A3A5C", "Kotak": "#2C5F8A"}
SC_COLORS   = {"Baseline": "#4CAF50", "Moderate_Stress": "#FF9800", "Severe_Stress": "#F44336"}
BANKS_LIST  = ["SBI", "BOM", "HDFC", "Kotak"]


def load_results():
    results = []
    for bank in BANKS_LIST:
        for sc in SCENARIOS:
            results.append(run_transmission(bank, sc))
    return results

def score_bank(r):
    car_floor = RBI_FLOORS["car_min_dsib"] if r["bank"] in DSIB_BANKS else RBI_FLOORS["car_min"]
    car_buf   = r["car_stressed_pct"] - car_floor
    nim_buf   = r["nim_stressed"] - 2.0
    roa       = r["roa_stressed_pct"]
    pcr       = r["pcr_stressed"]
    tier1_buf = r["tier1_stressed_pct"] - RBI_FLOORS["tier1_min"]

    d = {
        "Capital buffer":      min(20, max(0, car_buf * 2.0)),
        "NIM resilience":      min(20, max(0, nim_buf * 4.0)),
        "Profitability":       min(20, max(0, (roa + 1.5) * 7.0)),
        "Provision coverage":  min(20, pcr / 5.0),
        "Tier-1 headroom":     min(20, max(0, tier1_buf * 1.5)),
    }
    d["Total"] = round(sum(d.values()), 1)
    return d


def build_scorecard(results):
    severe = [r for r in results if r["scenario"] == "Severe_Stress"]
    rows = []
    for r in severe:
        s = score_bank(r)
        rows.append({
            "Bank": r["bank"], "Type": r["bank_type"],
            **s,
            "CAR stressed":  r["car_stressed_pct"],
            "ROA stressed":  r["roa_stressed_pct"],
            "NIM stressed":  r["nim_stressed"],
            "PCR stressed":  r["pcr_stressed"],
            "CAR breach":    r["car_breach"],
            "ROA negative":  r["roa_negative"],
        })
    df = pd.DataFrame(rows).sort_values("Total", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", df.index + 1)
    return df


def print_scorecard(df):
    dims = ["Capital buffer", "NIM resilience", "Profitability", "Provision coverage", "Tier-1 headroom"]
    print("\n" + "═" * 78)
    print("  RESILIENCE SCORECARD  —  Severe Stress")
    print("  5 dimensions × 20 pts each  =  100 pts total")
    print("═" * 78)
    print(f"  {'Rank':<5} {'Bank':<8} {'Type':<10} {'Cap':>6} {'NIM':>6} "
          f"{'Prof':>6} {'PCR':>6} {'T1':>6} {'TOTAL':>7}")
    print("  " + "─" * 62)
    for _, row in df.iterrows():
        flags = ""
        if row["ROA negative"]: flags += " ⚠ LOSS"
        if row["CAR breach"]:   flags += " ⚠ CAR BREACH"
        print(f"  #{int(row['Rank']):<4} {row['Bank']:<8} {row['Type']:<10} "
              f"{row['Capital buffer']:>6.1f} {row['NIM resilience']:>6.1f} "
              f"{row['Profitability']:>6.1f} {row['Provision coverage']:>6.1f} "
              f"{row['Tier-1 headroom']:>6.1f} {row['Total']:>7.1f}{flags}")
    print("═" * 78)

def psu_vs_private(results):
    df_all = pd.DataFrame(results)
    print("\n" + "═" * 68)
    print("  PSU vs PRIVATE  —  Comparative Analysis")
    print("═" * 68)

    for sc in SCENARIOS:
        df = df_all[df_all["scenario"] == sc]
        psu  = df[df["bank_type"] == "PSU"]
        pvt  = df[df["bank_type"] == "Private"]
        print(f"\n  [{sc.replace('_',' ')}]")
        print(f"  {'Metric':<22} {'PSU avg':>10} {'Private avg':>12} {'Delta':>10}")
        print("  " + "─" * 54)
        for col, lbl in [("gnpa_stressed_pct","GNPA %"), ("nim_stressed","NIM %"),
                         ("car_stressed_pct","CAR %"), ("roa_stressed_pct","ROA %"),
                         ("pcr_stressed","PCR %")]:
            p_avg  = psu[col].mean()
            pv_avg = pvt[col].mean()
            delta  = pv_avg - p_avg
            sign   = "+" if delta > 0 else ""
            print(f"  {lbl:<22} {p_avg:>10.2f}% {pv_avg:>11.2f}% {sign}{delta:>9.2f}pp")
    print("═" * 68)

def plot_radar(df):
    dims = ["Capital buffer", "NIM resilience", "Profitability", "Provision coverage", "Tier-1 headroom"]
    N = len(dims)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, axes = plt.subplots(1, 4, figsize=(18, 5), subplot_kw=dict(polar=True))
    for ax, (_, row) in zip(axes, df.iterrows()):
        vals = [row[d] for d in dims]
        vals += vals[:1]
        ax.plot(angles, vals, linewidth=2, color=BANK_COLORS[row["Bank"]])
        ax.fill(angles, vals, alpha=0.25, color=BANK_COLORS[row["Bank"]])
        ax.plot(angles, [20]*len(angles), linewidth=0.8, linestyle="--",
                color="gray", alpha=0.4)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(["Cap", "NIM", "Prof", "PCR", "T1"], fontsize=9)
        ax.set_ylim(0, 20)
        ax.set_yticks([5, 10, 15, 20])
        ax.set_yticklabels(["5","10","15","20"], fontsize=7)
        rank = int(row["Rank"])
        ax.set_title(f"#{rank} {row['Bank']} ({row['Type']})\n{row['Total']:.1f}/100",
                     fontweight="bold", fontsize=11, pad=12)

    fig.suptitle("Resilience Radar — Severe Stress", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("outputs/charts/resilience_radar.png", dpi=150)
    plt.close()
    print("Saved: outputs/charts/resilience_radar.png")


def plot_scorecard_bars(df):
    dims = ["Capital buffer", "NIM resilience", "Profitability", "Provision coverage", "Tier-1 headroom"]
    dim_colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336"]

    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(df))
    bottoms = np.zeros(len(df))

    for dim, color in zip(dims, dim_colors):
        vals = df[dim].values
        bars = ax.bar(x, vals, bottom=bottoms, color=color, label=dim,
                      edgecolor="white", linewidth=0.6)
        bottoms += vals

    for i, (_, row) in enumerate(df.iterrows()):
        ax.text(i, row["Total"] + 0.5, f"{row['Total']:.1f}",
                ha="center", fontsize=10, fontweight="bold")
        if row["ROA negative"]:
            ax.text(i, -4, "⚠ LOSS", ha="center", fontsize=8, color="#F44336")

    ax.axhline(50, color="orange", linestyle="--", alpha=0.6, linewidth=1.2, label="Moderate threshold (50)")
    ax.axhline(70, color="green",  linestyle="--", alpha=0.6, linewidth=1.2, label="Strong threshold (70)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"#{int(r['Rank'])} {r['Bank']}\n({r['Type']})" for _, r in df.iterrows()],
                       fontsize=11)
    ax.set_ylabel("Resilience Score (out of 100)")
    ax.set_ylim(-8, 108)
    ax.legend(loc="upper right", fontsize=8, ncol=2)
    ax.grid(axis="y", alpha=0.3)
    ax.set_title("Resilience Scorecard — Severe Stress (5 dimensions)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("outputs/charts/scorecard_bars.png", dpi=150)
    plt.close()
    print("Saved: outputs/charts/scorecard_bars.png")


def plot_psu_vs_private(results):
    df = pd.DataFrame(results)
    metrics = [
        ("gnpa_stressed_pct", "GNPA %",  False),
        ("nim_stressed",       "NIM %",   True),
        ("car_stressed_pct",   "CAR %",   True),
        ("roa_stressed_pct",   "ROA %",   True),
        ("pcr_stressed",       "PCR %",   True),
    ]
    sc_list = list(SCENARIOS.keys())
    fig, axes = plt.subplots(1, len(metrics), figsize=(18, 6))

    for ax, (col, label, higher_better) in zip(axes, metrics):
        psu_vals = [df[(df.scenario==sc) & (df.bank_type=="PSU")][col].mean() for sc in sc_list]
        pvt_vals = [df[(df.scenario==sc) & (df.bank_type=="Private")][col].mean() for sc in sc_list]
        x = np.arange(len(sc_list))
        w = 0.35
        ax.bar(x - w/2, psu_vals, w, label="PSU",     color="#1B4332", edgecolor="white")
        ax.bar(x + w/2, pvt_vals, w, label="Private", color="#1A3A5C", edgecolor="white")
        ax.set_xticks(x)
        ax.set_xticklabels(["Base", "Mod", "Severe"], fontsize=8)
        ax.set_title(label, fontweight="bold", fontsize=10)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=7)

    fig.suptitle("PSU vs Private Banks — Stressed Metrics Across Scenarios", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("outputs/charts/psu_vs_private.png", dpi=150)
    plt.close()
    print("Saved: outputs/charts/psu_vs_private.png")


def plot_scenario_heatmap(results):
    df = pd.DataFrame(results)
    pivot = df.pivot_table(index="bank", columns="scenario", values="car_stressed_pct")
    pivot = pivot[list(SCENARIOS.keys())]
    pivot = pivot.loc[BANKS_LIST]

    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=8, vmax=25)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(["Baseline", "Moderate Stress", "Severe Stress"], fontsize=11)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=11)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            color = "black" if val > 13 else "white"
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                    fontsize=12, fontweight="bold", color=color)
    plt.colorbar(im, ax=ax, label="CAR %")
    ax.set_title("Stressed CAR Heatmap — All Banks × All Scenarios", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("outputs/charts/car_heatmap.png", dpi=150)
    plt.close()
    print("Saved: outputs/charts/car_heatmap.png")


if __name__ == "__main__":
    results = load_results()
    df_sc = build_scorecard(results)

    print_scorecard(df_sc)
    psu_vs_private(results)

    plot_radar(df_sc)
    plot_scorecard_bars(df_sc)
    plot_psu_vs_private(results)
    plot_scenario_heatmap(results)

    df_sc.to_csv("data/processed/resilience_scorecard.csv", index=False)
    print("\nSaved: data/processed/resilience_scorecard.csv")