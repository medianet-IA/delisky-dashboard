# -*- coding: utf-8 -*-
"""
=============================================================
  DELISKY WORKFLOW — DATA VISUALIZATION SCRIPT
  Requires: analysis_results/ CSVs produced by data_analysis.py

  Charts produced  (saved in  charts/  folder):
    Chart 1 — Revenue per VAN per Day  (line chart, per company)
    Chart 2 — Total Revenue per VAN    (horizontal bar, all companies)
    Chart 3 — Sales per Region         (pie charts, per company)
    Chart 4 — Top 15 Articles per Company (bar charts)
    Chart 5 — Inventory Balance per VAN  (grouped bar: loaded vs sold)
    Chart 6 — PoS Client Visits per Day  (area chart per company)
=============================================================
"""

import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend — no display needed
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─── PATHS ──────────────────────────────────────────────────────────────────
BASE   = Path(__file__).parent
RES    = BASE / "analysis_results"
OUT    = BASE / "charts"
OUT.mkdir(exist_ok=True)

SEP = "=" * 72

# ─── GLOBAL STYLE ────────────────────────────────────────────────────────────
PALETTE = {
    "BIFA":    "#4F46E5",   # indigo
    "DELISKY": "#10B981",   # emerald
    "NITA":    "#F59E0B",   # amber
}
COMPANY_COLORS = list(PALETTE.values())

plt.rcParams.update({
    "figure.facecolor":  "#0F172A",
    "axes.facecolor":    "#1E293B",
    "axes.edgecolor":    "#334155",
    "axes.labelcolor":   "#CBD5E1",
    "axes.titlecolor":   "#F1F5F9",
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.labelsize":    10,
    "xtick.color":       "#94A3B8",
    "ytick.color":       "#94A3B8",
    "xtick.labelsize":   8,
    "ytick.labelsize":   8,
    "grid.color":        "#334155",
    "grid.linestyle":    "--",
    "grid.alpha":        0.6,
    "legend.facecolor":  "#1E293B",
    "legend.edgecolor":  "#334155",
    "legend.labelcolor": "#CBD5E1",
    "legend.fontsize":   9,
    "text.color":        "#F1F5F9",
    "font.family":       "DejaVu Sans",
})

def save_fig(name: str):
    path = OUT / name
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="#0F172A")
    plt.close()
    print(f"  [OK]  Saved: {name}")
    return path

def fmt_da(x, pos=None):
    """Format large numbers as k/M DA."""
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    if abs(x) >= 1_000:
        return f"{x/1_000:.0f}k"
    return str(int(x))

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
print(SEP)
print("  DELISKY WORKFLOW -- DATA VISUALIZATION")
print(SEP)

def load(fname):
    p = RES / fname
    if not p.exists():
        print(f"  [ERR] {fname} not found — run data_analysis.py first!")
        sys.exit(1)
    return pd.read_csv(p, encoding="utf-8-sig")

a1 = load("A1_sales_per_van_per_day.csv")
a2 = load("A2_sales_per_van_per_region.csv")
a3 = load("A3_chargement_vs_sales.csv")
a4 = load("A4_inventory_balance_by_van.csv")
a5 = load("A5_pos_visits_per_van_per_day.csv")
a6 = load("A6_top_articles_per_company.csv")

# Parse dates
a1["Date"] = pd.to_datetime(a1["Date"], errors="coerce")
a5["Date"] = pd.to_datetime(a5["Date"], errors="coerce")

print("  All analysis CSVs loaded.\n")

# ─── CHART 1 — REVENUE PER VAN PER DAY (line, per company) ──────────────────
print("  Building Chart 1 — Revenue per VAN per Day ...")

companies = ["BIFA", "DELISKY", "NITA"]
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=False)
fig.suptitle("Daily Revenue per VAN by Company (Mar 2026)", fontsize=15,
             fontweight="bold", color="#F1F5F9", y=1.01)

for i, (co, ax) in enumerate(zip(companies, axes)):
    subset = a1[(a1["Company"] == co) & a1["Date"].notna()].copy()
    if subset.empty:
        ax.set_title(f"{co} — No daily data")
        continue
    vans = sorted(subset["VAN"].unique())
    cmap = plt.cm.get_cmap("tab10", len(vans))
    for j, van in enumerate(vans):
        v = subset[subset["VAN"] == van].sort_values("Date")
        display = van.replace(co + " ", "")
        ax.plot(v["Date"], v["Revenue_DA"], marker="o", linewidth=2.2,
                markersize=6, label=display, color=cmap(j))
        ax.fill_between(v["Date"], v["Revenue_DA"], alpha=0.08, color=cmap(j))
    ax.set_title(f"{co}", fontsize=12, pad=8, color=PALETTE[co])
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_da))
    ax.set_ylabel("Revenue (DA)", fontsize=9)
    ax.grid(True, axis="y")
    ax.legend(loc="upper right", ncol=2)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

plt.tight_layout(pad=2.0)
save_fig("C1_revenue_per_van_per_day.png")

# ─── CHART 2 — TOTAL REVENUE PER VAN (horizontal bar) ───────────────────────
print("  Building Chart 2 — Total Revenue per VAN ...")

van_rev = (a1.groupby(["Company", "VAN"])["Revenue_DA"].sum()
             .reset_index()
             .sort_values("Revenue_DA", ascending=True))

fig, ax = plt.subplots(figsize=(12, max(6, len(van_rev) * 0.45)))
fig.suptitle("Total Sales Revenue per VAN (All Days)", fontsize=14,
             fontweight="bold", color="#F1F5F9")

colors = [PALETTE.get(r["Company"], "#6366F1") for _, r in van_rev.iterrows()]
bars = ax.barh(van_rev["VAN"], van_rev["Revenue_DA"], color=colors,
               edgecolor="#0F172A", linewidth=0.5, height=0.65)

# Value labels
for bar, val in zip(bars, van_rev["Revenue_DA"]):
    ax.text(bar.get_width() + van_rev["Revenue_DA"].max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            fmt_da(val) + " DA", va="center", ha="left",
            fontsize=8, color="#CBD5E1")

ax.xaxis.set_major_formatter(mtick.FuncFormatter(fmt_da))
ax.set_xlabel("Revenue (DA)")
ax.grid(True, axis="x")
legend_patches = [mpatches.Patch(color=PALETTE[c], label=c) for c in companies]
ax.legend(handles=legend_patches, loc="lower right")
plt.tight_layout()
save_fig("C2_total_revenue_per_van.png")

# ─── CHART 3 — SALES PER REGION (pie, per company) ──────────────────────────
print("  Building Chart 3 — Sales per Region ...")

fig, axes = plt.subplots(1, 3, figsize=(18, 7))
fig.suptitle("Revenue Distribution by Region", fontsize=14,
             fontweight="bold", color="#F1F5F9")

for ax, co in zip(axes, companies):
    sub = (a2[a2["Company"] == co]
           .groupby("Region", dropna=False)["Revenue_DA"].sum()
           .reset_index())
    sub["Region"] = sub["Region"].fillna("N/A")
    sub = sub.sort_values("Revenue_DA", ascending=False)

    # Keep top 8, group rest as "Autres"
    if len(sub) > 8:
        top   = sub.head(8)
        other = pd.DataFrame([{"Region": "Autres", "Revenue_DA": sub.iloc[8:]["Revenue_DA"].sum()}])
        sub   = pd.concat([top, other], ignore_index=True)

    cmap   = plt.cm.get_cmap("tab20", len(sub))
    colors = [cmap(j) for j in range(len(sub))]
    wedges, texts, autotexts = ax.pie(
        sub["Revenue_DA"], labels=None,
        autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
        colors=colors, startangle=140,
        wedgeprops={"edgecolor": "#0F172A", "linewidth": 1},
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_color("white")
    ax.set_title(co, color=PALETTE[co], fontsize=13, pad=14)
    ax.legend(wedges, sub["Region"], loc="lower center",
              bbox_to_anchor=(0.5, -0.3), ncol=2, fontsize=7,
              framealpha=0.3)

plt.tight_layout(pad=3)
save_fig("C3_revenue_per_region.png")

# ─── CHART 4 — TOP 15 ARTICLES PER COMPANY ──────────────────────────────────
print("  Building Chart 4 — Top 15 Articles per Company ...")

fig, axes = plt.subplots(1, 3, figsize=(20, 9))
fig.suptitle("Top 15 Best-Selling Articles per Company (Units)",
             fontsize=14, fontweight="bold", color="#F1F5F9")

for ax, co in zip(axes, companies):
    sub = (a6[a6["Company"] == co]
           .sort_values("Total_Qty_Sold", ascending=False)
           .head(15)
           .sort_values("Total_Qty_Sold", ascending=True))

    color = PALETTE[co]
    cmap  = plt.cm.get_cmap("Blues", len(sub) + 4)
    bar_colors = [cmap(j + 4) for j in range(len(sub))]

    bars = ax.barh(sub["Article"], sub["Total_Qty_Sold"],
                   color=bar_colors, edgecolor="#0F172A", linewidth=0.4)
    for bar, val in zip(bars, sub["Total_Qty_Sold"]):
        ax.text(bar.get_width() + sub["Total_Qty_Sold"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center", ha="left", fontsize=7, color="#CBD5E1")

    ax.set_title(co, color=color, fontsize=12, pad=10)
    ax.set_xlabel("Units Sold")
    ax.grid(True, axis="x")
    # Truncate long article names
    ax.set_yticklabels(
        [t.get_text()[:28] + "…" if len(t.get_text()) > 28 else t.get_text()
         for t in ax.get_yticklabels()],
        fontsize=7
    )

plt.tight_layout(pad=2.5)
save_fig("C4_top_articles.png")

# ─── CHART 5 — INVENTORY BALANCE PER VAN ────────────────────────────────────
print("  Building Chart 5 — Inventory Balance per VAN ...")

fig, ax = plt.subplots(figsize=(14, 7))
fig.suptitle("Inventory Balance per VAN  (Opening + Loaded vs Sold)",
             fontsize=14, fontweight="bold", color="#F1F5F9")

a4_sorted = a4.sort_values(["Company", "VAN"]).reset_index(drop=True)
x      = range(len(a4_sorted))
width  = 0.25

bars_in  = ax.bar([i - width for i in x], a4_sorted["Opening_Qty"],
                  width, label="Opening Stock", color="#3B82F6", alpha=0.85)
bars_ld  = ax.bar([i          for i in x], a4_sorted["Qty_Loaded"],
                  width, label="Loaded (Chargement)", color="#10B981", alpha=0.85)
bars_sl  = ax.bar([i + width  for i in x], a4_sorted["Qty_Sold"],
                  width, label="Sold (Items)", color="#F59E0B", alpha=0.85)

ax.set_xticks(list(x))
ax.set_xticklabels(
    [f"{r['VAN'].replace(r['Company'] + ' ', '')}\n({r['Company']})"
     for _, r in a4_sorted.iterrows()],
    fontsize=8, rotation=0
)
ax.set_ylabel("Quantity (units)")
ax.grid(True, axis="y")
ax.legend(loc="upper right")

# Annotate Stock_Left
for i, row in a4_sorted.iterrows():
    color = "#EF4444" if row["Stock_Left"] < 0 else "#34D399"
    ax.text(i, max(row["Opening_Qty"], row["Qty_Loaded"], row["Qty_Sold"]) + 50,
            f"Left: {int(row['Stock_Left']):,}",
            ha="center", va="bottom", fontsize=7, color=color, fontweight="bold")

plt.tight_layout()
save_fig("C5_inventory_balance.png")

# ─── CHART 6 — PoS CLIENT VISITS PER DAY (area) ─────────────────────────────
print("  Building Chart 6 — PoS Client Visits per Day ...")

a5_day = a5[a5["Date"].notna()].copy()
a5_day = (a5_day.groupby(["Company", "Date"])["Client_Visits"].sum()
           .reset_index().sort_values(["Company", "Date"]))

fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=False)
fig.suptitle("Daily PoS Client Visits per Company (Mar 2026)",
             fontsize=14, fontweight="bold", color="#F1F5F9", y=1.01)

for ax, co in zip(axes, companies):
    sub = a5_day[a5_day["Company"] == co]
    if sub.empty:
        ax.set_title(f"{co} — No daily data")
        continue
    color = PALETTE[co]
    ax.fill_between(sub["Date"], sub["Client_Visits"], alpha=0.25, color=color)
    ax.plot(sub["Date"], sub["Client_Visits"], color=color, linewidth=2.5,
            marker="o", markersize=7)
    # Annotate each point
    for _, r in sub.iterrows():
        ax.text(r["Date"], r["Client_Visits"] + sub["Client_Visits"].max() * 0.04,
                str(int(r["Client_Visits"])), ha="center", va="bottom",
                fontsize=9, color=color, fontweight="bold")
    ax.set_title(f"{co}", color=color, fontsize=12, pad=8)
    ax.set_ylabel("Client Visits")
    ax.grid(True, axis="y")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")
    ax.set_ylim(bottom=0)

plt.tight_layout(pad=2.0)
save_fig("C6_pos_visits_per_day.png")

# ─── FINAL SUMMARY ──────────────────────────────────────────────────────────
print(f"\n{SEP}")
print(f"  VISUALIZATION COMPLETE — All charts saved to  charts/")
print(SEP)

charts = sorted(OUT.glob("*.png"))
for c in charts:
    kb = c.stat().st_size // 1024
    print(f"    {c.name:<45}  {kb:>5} KB")

print(f"\n  Total: {len(charts)} chart files generated.")
print(SEP)
