
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os, sys, warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(__file__))
from config import BANKS, FY24_ACTUALS, RBI_FLOORS, DSIB_BANKS

os.makedirs("outputs/charts", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

BANK_COLORS = {"SBI": "#1B4332", "BOM": "#2D6A4F", "HDFC": "#1A3A5C", "Kotak": "#2C5F8A"}
BANKS_LIST  = ["SBI", "BOM", "HDFC", "Kotak"]

HISTORICAL = {
    "SBI":   {
        "FY20": {"gnpa":6.15,"nnpa":2.23,"nim":2.87,"car":13.06,"tier1":9.98, "roa":0.38,"roe":5.00, "pcr":83.0},
        "FY21": {"gnpa":4.98,"nnpa":1.50,"nim":3.18,"car":13.74,"tier1":10.66,"roa":0.48,"roe":8.00, "pcr":87.0},
        "FY22": {"gnpa":3.97,"nnpa":1.02,"nim":3.15,"car":13.83,"tier1":10.27,"roa":0.67,"roe":13.92,"pcr":89.5},
        "FY23": {"gnpa":2.78,"nnpa":0.67,"nim":3.37,"car":14.68,"tier1":10.27,"roa":0.96,"roe":19.43,"pcr":74.0},
        "FY24": {"gnpa":2.24,"nnpa":0.57,"nim":3.28,"car":14.28,"tier1":10.36,"roa":1.04,"roe":20.32,"pcr":75.0},
    },
    "BOM": {
        "FY20": {"gnpa":9.50,"nnpa":3.50,"nim":2.80,"car":13.52,"tier1":10.20,"roa":-0.09,"roe":-1.20,"pcr":78.0},
        "FY21": {"gnpa":7.23,"nnpa":2.47,"nim":2.95,"car":14.13,"tier1":11.30,"roa":0.20, "roe":3.50, "pcr":92.38},
        "FY22": {"gnpa":5.56,"nnpa":1.73,"nim":3.27,"car":15.62,"tier1":12.80,"roa":0.44, "roe":7.10, "pcr":95.00},
        "FY23": {"gnpa":2.47,"nnpa":0.25,"nim":3.55,"car":18.14,"tier1":15.54,"roa":1.14, "roe":18.70,"pcr":98.28},
        "FY24": {"gnpa":1.88,"nnpa":0.20,"nim":3.60,"car":17.38,"tier1":14.50,"roa":1.24, "roe":20.10,"pcr":98.20},
    },
    "HDFC": {
        "FY20": {"gnpa":1.26,"nnpa":0.36,"nim":4.30,"car":18.52,"tier1":17.10,"roa":1.90,"roe":16.50,"pcr":68.0},
        "FY21": {"gnpa":1.32,"nnpa":0.40,"nim":4.20,"car":18.90,"tier1":17.60,"roa":1.90,"roe":16.00,"pcr":70.0},
        "FY22": {"gnpa":1.17,"nnpa":0.32,"nim":4.10,"car":18.90,"tier1":17.90,"roa":1.90,"roe":16.90,"pcr":71.0},
        "FY23": {"gnpa":1.12,"nnpa":0.27,"nim":4.10,"car":19.30,"tier1":18.90,"roa":2.00,"roe":17.40,"pcr":70.0},
        "FY24": {"gnpa":1.24,"nnpa":0.33,"nim":3.46,"car":18.80,"tier1":17.50,"roa":1.90,"roe":16.50,"pcr":70.0},
    },
    "Kotak": {
        "FY20": {"gnpa":2.25,"nnpa":0.71,"nim":4.72,"car":17.90,"tier1":16.50,"roa":2.00,"roe":13.20,"pcr":65.0},
        "FY21": {"gnpa":3.25,"nnpa":1.21,"nim":4.39,"car":21.20,"tier1":19.90,"roa":2.10,"roe":11.50,"pcr":72.5},
        "FY22": {"gnpa":2.34,"nnpa":0.64,"nim":4.62,"car":22.70,"tier1":21.30,"roa":2.00,"roe":13.00,"pcr":73.6},
        "FY23": {"gnpa":1.90,"nnpa":0.37,"nim":5.33,"car":21.80,"tier1":20.90,"roa":2.20,"roe":14.70,"pcr":74.0},
        "FY24": {"gnpa":1.73,"nnpa":0.34,"nim":4.97,"car":21.80,"tier1":20.70,"roa":2.30,"roe":14.10,"pcr":75.0},
    },
}

EWI_THRESHOLDS = {
    "gnpa":  {"green": 3.0,  "amber": 6.0,  "label": "GNPA %",        "direction": "lower_better"},
    "nnpa":  {"green": 1.0,  "amber": 3.0,  "label": "NNPA %",        "direction": "lower_better"},
    "nim":   {"green": 3.0,  "amber": 2.0,  "label": "NIM %",         "direction": "higher_better"},
    "car":   {"green": 12.0, "amber": 10.0, "label": "CAR %",         "direction": "higher_better"},
    "tier1": {"green": 9.0,  "amber": 7.5,  "label": "Tier-1 %",      "direction": "higher_better"},
    "roa":   {"green": 0.5,  "amber": 0.0,  "label": "ROA %",         "direction": "higher_better"},
    "pcr":   {"green": 70.0, "amber": 60.0, "label": "PCR %",         "direction": "higher_better"},
}

def get_signal(metric, value):
    t = EWI_THRESHOLDS[metric]
    if t["direction"] == "lower_better":
        if value <= t["green"]: return "GREEN"
        if value <= t["amber"]: return "AMBER"
        return "RED"
    else:
        if value >= t["green"]: return "GREEN"
        if value >= t["amber"]: return "AMBER"
        return "RED"


def compute_ewi_table():
    rows = []
    for bank in BANKS_LIST:
        for yr, data in HISTORICAL[bank].items():
            for metric in EWI_THRESHOLDS:
                val = data[metric]
                signal = get_signal(metric, val)
                rows.append({
                    "bank": bank, "type": BANKS[bank]["type"],
                    "year": yr, "metric": metric,
                    "value": val, "signal": signal,
                    "label": EWI_THRESHOLDS[metric]["label"],
                })
    return pd.DataFrame(rows)


def print_ewi_summary(df):
    print("\n" + "═" * 62)
    print("  EARLY WARNING INDICATORS — FY24 Snapshot")
    print("  G = Green  A = Amber  R = Red")
    print("═" * 62)
    fy24 = df[df["year"] == "FY24"]
    metrics = list(EWI_THRESHOLDS.keys())
    header = f"  {'Bank':<8} {'Type':<10}" + "".join(f"{EWI_THRESHOLDS[m]['label']:>9}" for m in metrics)
    print(header)
    print("  " + "─" * 56)
    for bank in BANKS_LIST:
        row = fy24[fy24["bank"] == bank]
        signals = ""
        for m in metrics:
            s = row[row["metric"] == m]["signal"].values[0]
            signals += f"{'G' if s=='GREEN' else ('A' if s=='AMBER' else 'R'):>9}"
        print(f"  {bank:<8} {BANKS[bank]['type']:<10}{signals}")
    print("═" * 62)


def plot_ewi_heatmap(df):
    years = ["FY20", "FY21", "FY22", "FY23", "FY24"]
    metrics = list(EWI_THRESHOLDS.keys())
    signal_map = {"GREEN": 2, "AMBER": 1, "RED": 0}
    cmap = plt.cm.RdYlGn

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    for ax, bank in zip(axes, BANKS_LIST):
        data = np.zeros((len(metrics), len(years)))
        for i, m in enumerate(metrics):
            for j, yr in enumerate(years):
                val = df[(df.bank==bank) & (df.year==yr) & (df.metric==m)]["signal"].values[0]
                data[i, j] = signal_map[val]

        im = ax.imshow(data, cmap=cmap, aspect="auto", vmin=0, vmax=2)
        ax.set_xticks(range(len(years))); ax.set_xticklabels(years, fontsize=10)
        ax.set_yticks(range(len(metrics)))
        ax.set_yticklabels([EWI_THRESHOLDS[m]["label"] for m in metrics], fontsize=10)
        ax.set_title(f"{bank}  ({BANKS[bank]['type']})", fontweight="bold", fontsize=12)

        for i in range(len(metrics)):
            for j in range(len(years)):
                val_raw = HISTORICAL[bank][years[j]][metrics[i]]
                ax.text(j, i, f"{val_raw:.1f}", ha="center", va="center",
                        fontsize=8.5, fontweight="bold",
                        color="black" if data[i,j] == 1 else "white")

    patches = [
        mpatches.Patch(color=cmap(0.1), label="Red — Stressed"),
        mpatches.Patch(color=cmap(0.5), label="Amber — Caution"),
        mpatches.Patch(color=cmap(0.9), label="Green — Healthy"),
    ]
    fig.legend(handles=patches, loc="lower center", ncol=3, fontsize=10,
               bbox_to_anchor=(0.5, 0.01))
    fig.suptitle("Early Warning Indicators Heatmap — FY20 to FY24", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig("outputs/charts/ewi_heatmap.png", dpi=150)
    plt.close()
    print("Saved: outputs/charts/ewi_heatmap.png")


def plot_ewi_trend_bank(bank):
    years = ["FY20", "FY21", "FY22", "FY23", "FY24"]
    metrics_to_plot = ["gnpa", "car", "roa", "nim", "pcr"]
    colors_m = ["#F44336", "#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]

    fig, axes = plt.subplots(1, len(metrics_to_plot), figsize=(18, 4))
    for ax, m, col in zip(axes, metrics_to_plot, colors_m):
        vals = [HISTORICAL[bank][yr][m] for yr in years]
        ax.plot(years, vals, marker="o", linewidth=2.2, color=col)
        t = EWI_THRESHOLDS[m]
        ax.axhline(t["green"], color="green", linestyle="--", alpha=0.5, linewidth=1)
        ax.axhline(t["amber"], color="orange", linestyle=":",  alpha=0.5, linewidth=1)
        ax.set_title(t["label"], fontweight="bold", fontsize=10)
        ax.grid(alpha=0.3)
        for x_i, v in enumerate(vals):
            signal = get_signal(m, v)
            c = "#2e7d32" if signal=="GREEN" else ("#e65100" if signal=="AMBER" else "#c62828")
            ax.annotate(f"{v:.1f}", (years[x_i], v), textcoords="offset points",
                        xytext=(0, 7), ha="center", fontsize=8, color=c)

    fig.suptitle(f"{bank} — EWI Trend (FY20–FY24)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = f"outputs/charts/ewi_trend_{bank.lower()}.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


if __name__ == "__main__":
    df_ewi = compute_ewi_table()
    df_ewi.to_csv("data/processed/ewi_signals.csv", index=False)
    print("Saved: data/processed/ewi_signals.csv")

    print_ewi_summary(df_ewi)
    plot_ewi_heatmap(df_ewi)
    for bank in BANKS_LIST:
        plot_ewi_trend_bank(bank)