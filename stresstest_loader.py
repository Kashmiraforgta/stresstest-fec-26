"""
StressTest – Data Loader & Analysis Starter
FEC · IIT Guwahati · DIY 2026
------------------------------------------------------------
Usage:
    python stresstest_loader.py
Requires:
    pip install pandas matplotlib seaborn openpyxl
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ── Load data ────────────────────────────────────────────────────────────────
def load_data():
    """Returns two DataFrames: long-format and wide-format."""
    df_long = pd.read_csv("stresstest_master.csv")
    df_wide = pd.read_csv("stresstest_wide.csv")
    return df_long, df_wide

# ── Quick summary ────────────────────────────────────────────────────────────
def summary(df_wide):
    print("\n" + "="*60)
    print("  STRESSTEST – FY2024 SNAPSHOT (All 4 Banks)")
    print("="*60)
    fy24 = df_wide[df_wide["year"] == "FY24"].copy()
    fy24 = fy24[["bank_code","bank_type","gnpa_pct","nnpa_pct",
                  "nim_pct","car_pct","roa_pct","roe_pct","pcr_pct"]]
    fy24.columns = ["Bank","Type","GNPA%","NNPA%","NIM%","CAR%","ROA%","ROE%","PCR%"]
    print(fy24.to_string(index=False))

    print("\n" + "-"*60)
    print("  RBI REGULATORY MINIMUMS (for reference)")
    print("-"*60)
    print("  CAR (Basel III): 9.0%  |  Tier-1: 7.0%")
    print("  CAR (D-SIB like HDFC): 9.2% (0.2% surcharge)")
    print("="*60)

# ── Plot: GNPA trend ─────────────────────────────────────────────────────────
def plot_gnpa(df_wide):
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = {"SBI":"#1B4332","BOM":"#2D6A4F","HDFC":"#1A3A5C","Kotak":"#2C5F8A"}
    for bank, grp in df_wide.groupby("bank_code"):
        ax.plot(grp["year"], grp["gnpa_pct"], marker="o", linewidth=2.2,
                label=bank, color=colors.get(bank,"gray"))
        ax.annotate(f'{grp["gnpa_pct"].iloc[-1]:.2f}%',
                    (grp["year"].iloc[-1], grp["gnpa_pct"].iloc[-1]),
                    textcoords="offset points", xytext=(6,0), fontsize=9)
    ax.axhline(y=9.0, color="red", linestyle="--", alpha=0.4, label="~RBI stress threshold (indicative)")
    ax.set_title("GNPA % Trend – All Banks (FY20–FY24)", fontsize=13, fontweight="bold")
    ax.set_ylabel("GNPA %"); ax.legend(); ax.grid(alpha=0.3)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.tight_layout(); plt.savefig("plot_gnpa_trend.png", dpi=150); plt.close()
    print("Saved: plot_gnpa_trend.png")

# ── Plot: CAR vs RBI minimum ─────────────────────────────────────────────────
def plot_car(df_wide):
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = {"SBI":"#1B4332","BOM":"#2D6A4F","HDFC":"#1A3A5C","Kotak":"#2C5F8A"}
    for bank, grp in df_wide.groupby("bank_code"):
        ax.plot(grp["year"], grp["car_pct"], marker="s", linewidth=2.2,
                label=bank, color=colors.get(bank,"gray"))
    ax.axhline(y=9.0, color="red", linestyle="--", linewidth=1.5, label="RBI Minimum CAR (9%)")
    ax.axhline(y=11.5, color="orange", linestyle=":", linewidth=1.2, label="Stress warning (11.5%)")
    ax.set_title("Capital Adequacy Ratio (CAR) – All Banks (FY20–FY24)", fontsize=13, fontweight="bold")
    ax.set_ylabel("CAR %"); ax.legend(); ax.grid(alpha=0.3)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.tight_layout(); plt.savefig("plot_car_trend.png", dpi=150); plt.close()
    print("Saved: plot_car_trend.png")

# ── Plot: ROA comparison ─────────────────────────────────────────────────────
def plot_roa(df_wide):
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = {"SBI":"#1B4332","BOM":"#2D6A4F","HDFC":"#1A3A5C","Kotak":"#2C5F8A"}
    for bank, grp in df_wide.groupby("bank_code"):
        ax.plot(grp["year"], grp["roa_pct"], marker="^", linewidth=2.2,
                label=bank, color=colors.get(bank,"gray"))
    ax.axhline(y=0, color="red", linestyle="--", alpha=0.5, label="Break-even (ROA=0)")
    ax.axhline(y=1.0, color="green", linestyle=":", alpha=0.5, label="Strong ROA threshold (1%)")
    ax.set_title("Return on Assets (ROA) – All Banks (FY20–FY24)", fontsize=13, fontweight="bold")
    ax.set_ylabel("ROA %"); ax.legend(); ax.grid(alpha=0.3)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.tight_layout(); plt.savefig("plot_roa_trend.png", dpi=150); plt.close()
    print("Saved: plot_roa_trend.png")

# ── Plot: FY24 radar / bar comparison ────────────────────────────────────────
def plot_fy24_bar(df_wide):
    fy24 = df_wide[df_wide["year"]=="FY24"].set_index("bank_code")
    metrics = ["gnpa_pct","nim_pct","car_pct","roa_pct","roe_pct","pcr_pct"]
    labels  = ["GNPA%","NIM%","CAR%","ROA%","ROE%","PCR%"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    colors = ["#1B4332","#2D6A4F","#1A3A5C","#2C5F8A"]
    banks  = ["SBI","BOM","HDFC","Kotak"]
    for i, (m, lbl) in enumerate(zip(metrics, labels)):
        ax = axes[i//3][i%3]
        vals = [fy24.loc[b, m] for b in banks]
        bars = ax.bar(banks, vals, color=colors, width=0.5, edgecolor="white")
        ax.set_title(lbl, fontweight="bold")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.grid(axis="y", alpha=0.3)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
                    f"{v:.2f}%", ha="center", va="bottom", fontsize=8)
    fig.suptitle("FY2024 Key Metrics – All 4 Banks Compared", fontsize=14, fontweight="bold")
    plt.tight_layout(); plt.savefig("plot_fy24_comparison.png", dpi=150); plt.close()
    print("Saved: plot_fy24_comparison.png")

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df_long, df_wide = load_data()
    summary(df_wide)
    plot_gnpa(df_wide)
    plot_car(df_wide)
    plot_roa(df_wide)
    plot_fy24_bar(df_wide)
    print("\nAll plots saved. Next step: build scenario assumption tables.")
