# -*- coding: utf-8 -*-
"""
=============================================================
  DELISKY WORKFLOW — DATA ANALYSIS SCRIPT
  Requires: cleaned/ CSV files produced by data_cleaning.py
  Produces: 7 analysis tables  →  analysis_results/ folder
=============================================================
  Analysis 1 : Sales per VAN per Day
  Analysis 2 : Sales per VAN per Region
  Analysis 3 : Loading (Chargement) vs Sales quantity per Article per VAN
  Analysis 4 : Inventory Balance  (Opening + Loaded − Sold)  per VAN
  Analysis 5 : PoS daily client visits per VAN
  Analysis 6 : Top-selling Articles per Company
  Analysis 7 : Null value summary per cleaned file
=============================================================
"""

import sys
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─── PATHS ──────────────────────────────────────────────────────────────────
BASE    = Path(__file__).parent
CLEANED = BASE / "cleaned"
OUT     = BASE / "analysis_results"
OUT.mkdir(exist_ok=True)

SEP  = "=" * 72
SEP2 = "-" * 72

# ─── LOAD CLEANED FILES ─────────────────────────────────────────────────────

print(SEP)
print("  DELISKY WORKFLOW -- DATA ANALYSIS")
print(SEP)

def load_csv(name: str) -> pd.DataFrame:
    path = CLEANED / name
    if not path.exists():
        print(f"  [ERR] File not found: {path}")
        print("        --> Run data_cleaning.py first!")
        sys.exit(1)
    return pd.read_csv(path, encoding="utf-8-sig")

df_sales  = load_csv("Sales_all.csv")
df_charg  = load_csv("Chargement_all.csv")
df_open   = load_csv("OpeningStock_all.csv")
df_pos    = load_csv("PoS_all.csv")
df_items  = load_csv("Items_all.csv")

# Re-parse date columns after CSV round-trip
df_sales["Date_Heure"] = pd.to_datetime(df_sales["Date_Heure"], errors="coerce")
df_pos["Date"]         = pd.to_datetime(df_pos["Date"],         errors="coerce")

# Extract date-only from Sales datetime
df_sales["Date"] = df_sales["Date_Heure"].dt.normalize()

print(f"\n  Loaded:")
for name, df in [("Sales", df_sales), ("Chargement", df_charg),
                 ("OpeningStock", df_open), ("PoS", df_pos), ("Items", df_items)]:
    print(f"    {name:<15} {len(df):>7} rows  x  {len(df.columns)} cols")

# ─── HELPER ─────────────────────────────────────────────────────────────────

def save(df: pd.DataFrame, filename: str):
    path = OUT / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path

def print_table(df: pd.DataFrame, max_rows: int = 30):
    print(df.to_string(index=False, max_rows=max_rows))

# ─── ANALYSIS 1 — SALES PER VAN PER DAY ─────────────────────────────────────

print(f"\n{SEP}")
print("  ANALYSIS 1 — Sales Revenue per VAN per Day")
print(SEP)

a1 = (df_sales
      .groupby(["Company", "VAN", "Date"], dropna=False)
      .agg(
          Transactions = ("Total", "count"),
          Revenue_DA   = ("Total", "sum"),
      )
      .reset_index()
      .sort_values(["Company", "VAN", "Date"])
)

print_table(a1)
p = save(a1, "A1_sales_per_van_per_day.csv")
print(f"\n  --> Saved: {p.name}  ({len(a1)} rows)")

# Summary per VAN
a1_summary = (a1.groupby(["Company", "VAN"])
               .agg(Days_Active=("Date", "nunique"),
                    Total_Transactions=("Transactions", "sum"),
                    Total_Revenue_DA=("Revenue_DA", "sum"))
               .reset_index()
               .sort_values("Total_Revenue_DA", ascending=False))

print(f"\n  SUMMARY — Total revenue per VAN:")
print(a1_summary.to_string(index=False))

# ─── ANALYSIS 2 — SALES PER VAN PER REGION ──────────────────────────────────

print(f"\n{SEP}")
print("  ANALYSIS 2 — Sales Revenue per VAN per Region")
print(SEP)

a2 = (df_sales
      .groupby(["Company", "VAN", "Region"], dropna=False)
      .agg(
          Transactions = ("Total", "count"),
          Revenue_DA   = ("Total", "sum"),
      )
      .reset_index()
      .sort_values(["Company", "VAN", "Revenue_DA"], ascending=[True, True, False])
)

print_table(a2)
p = save(a2, "A2_sales_per_van_per_region.csv")
print(f"\n  --> Saved: {p.name}  ({len(a2)} rows)")

# ─── ANALYSIS 3 — CHARGEMENT VS ITEMS SOLD PER ARTICLE PER VAN ──────────────

print(f"\n{SEP}")
print("  ANALYSIS 3 — Chargement Loaded vs Items Sold per Article per VAN")
print(SEP)

# Chargement: loaded qty
charg_grp = (df_charg
             .groupby(["Company", "VAN", "Article"])["Qté"]
             .sum()
             .reset_index()
             .rename(columns={"Qté": "Qty_Loaded"}))

# Items sold
items_grp = (df_items
             .groupby(["Company", "VAN", "Article"])["Qté vendue"]
             .sum()
             .reset_index()
             .rename(columns={"Qté vendue": "Qty_Sold"}))

a3 = pd.merge(charg_grp, items_grp, on=["Company", "VAN", "Article"], how="outer")
a3["Qty_Loaded"] = a3["Qty_Loaded"].fillna(0).astype(int)
a3["Qty_Sold"]   = a3["Qty_Sold"].fillna(0).astype(int)
a3["Balance"]    = a3["Qty_Loaded"] - a3["Qty_Sold"]
a3["Status"]     = a3["Balance"].apply(
    lambda x: "OK" if x >= 0 else "OVER-SOLD"
)
a3 = a3.sort_values(["Company", "VAN", "Article"])

print(f"  Total article-VAN combinations: {len(a3)}")
over_sold = a3[a3["Status"] == "OVER-SOLD"]
if len(over_sold) > 0:
    print(f"\n  [WARN] {len(over_sold)} Article-VAN pairs are OVER-SOLD (Sold > Loaded):")
    print(over_sold[["Company", "VAN", "Article", "Qty_Loaded", "Qty_Sold", "Balance"]].to_string(index=False))
else:
    print("  [OK]  No over-sold articles found.")

print(f"\n  Sample (first 20 rows sorted by Balance ascending):")
print(a3.sort_values("Balance").head(20).to_string(index=False))

p = save(a3, "A3_chargement_vs_sales.csv")
print(f"\n  --> Saved: {p.name}  ({len(a3)} rows)")

# ─── ANALYSIS 4 — INVENTORY BALANCE PER VAN ─────────────────────────────────

print(f"\n{SEP}")
print("  ANALYSIS 4 — Inventory Balance per VAN  (Opening + Loaded − Sold)")
print(SEP)
print("  NOTE: DELISKY LIV03 has Chargement_Qty = 0 (no loading data recorded)")

# Opening stock per VAN
open_grp = (df_open
            .groupby(["Company", "VAN", "Article"])["Qté"]
            .sum()
            .reset_index()
            .rename(columns={"Qté": "Opening_Qty"}))

a4 = pd.merge(open_grp, charg_grp, on=["Company", "VAN", "Article"], how="outer")
a4 = pd.merge(a4,       items_grp, on=["Company", "VAN", "Article"], how="outer")

a4["Opening_Qty"] = a4["Opening_Qty"].fillna(0).astype(int)
a4["Qty_Loaded"]  = a4["Qty_Loaded"].fillna(0).astype(int)
a4["Qty_Sold"]    = a4["Qty_Sold"].fillna(0).astype(int)
a4["Total_In"]    = a4["Opening_Qty"] + a4["Qty_Loaded"]
a4["Stock_Left"]  = a4["Total_In"] - a4["Qty_Sold"]
a4["Status"]      = a4["Stock_Left"].apply(
    lambda x: "OK" if x >= 0 else "DEFICIT"
)

a4 = a4.sort_values(["Company", "VAN", "Article"])

# Per-VAN summary
a4_van = (a4.groupby(["Company", "VAN"])
           .agg(
               Opening_Qty=("Opening_Qty", "sum"),
               Qty_Loaded =("Qty_Loaded",  "sum"),
               Qty_Sold   =("Qty_Sold",    "sum"),
               Stock_Left =("Stock_Left",  "sum"),
           )
           .reset_index()
           .sort_values(["Company", "VAN"]))
a4_van["Return_Rate_%"] = (
    (a4_van["Stock_Left"].astype(float)
     / a4_van["Opening_Qty"].replace(0, float("nan")).astype(float)
     * 100)
    .round(1)
)

print("\n  VAN-level Inventory Summary:")
print(a4_van.to_string(index=False))

deficit = a4[a4["Status"] == "DEFICIT"]
if len(deficit) > 0:
    print(f"\n  [WARN] {len(deficit)} Article-VAN pairs show DEFICIT (Sold > Opening+Loaded):")
    print(deficit[["Company","VAN","Article","Opening_Qty","Qty_Loaded","Qty_Sold","Stock_Left"]]
          .head(20).to_string(index=False))
else:
    print("\n  [OK]  No inventory deficits found.")

p  = save(a4,     "A4_inventory_balance_detail.csv")
p2 = save(a4_van, "A4_inventory_balance_by_van.csv")
print(f"\n  --> Saved: {p.name}  ({len(a4)} rows)")
print(f"  --> Saved: {p2.name}  ({len(a4_van)} rows)")

# ─── ANALYSIS 5 — PoS DAILY CLIENT VISITS PER VAN ───────────────────────────

print(f"\n{SEP}")
print("  ANALYSIS 5 — PoS Daily Client Visits per VAN")
print(SEP)

a5 = (df_pos
      .groupby(["Company", "VAN", "Date"], dropna=False)
      .agg(
          Client_Visits   = ("Nom du client", "count"),
          Unique_Clients  = ("Nom du client", "nunique"),
      )
      .reset_index()
      .sort_values(["Company", "VAN", "Date"])
)

print_table(a5)
p = save(a5, "A5_pos_visits_per_van_per_day.csv")
print(f"\n  --> Saved: {p.name}  ({len(a5)} rows)")

# VAN summary
a5_van = (a5.groupby(["Company", "VAN"])
           .agg(Days_Active=("Date", "nunique"),
                Total_Visits=("Client_Visits", "sum"),
                Unique_Clients=("Unique_Clients", "sum"))
           .reset_index()
           .sort_values("Total_Visits", ascending=False))
print("\n  VAN-level PoS summary:")
print(a5_van.to_string(index=False))

# ─── ANALYSIS 6 — TOP ARTICLES PER COMPANY ──────────────────────────────────

print(f"\n{SEP}")
print("  ANALYSIS 6 — Top Selling Articles per Company")
print(SEP)

a6 = (df_items
      .groupby(["Company", "Article"])["Qté vendue"]
      .sum()
      .reset_index()
      .rename(columns={"Qté vendue": "Total_Qty_Sold"})
      .sort_values(["Company", "Total_Qty_Sold"], ascending=[True, False])
)

for co in ["BIFA", "DELISKY", "NITA"]:
    subset = a6[a6["Company"] == co].head(15)
    print(f"\n  Top 15 Articles — {co}:")
    print(subset[["Article", "Total_Qty_Sold"]].to_string(index=False))

p = save(a6, "A6_top_articles_per_company.csv")
print(f"\n  --> Saved: {p.name}  ({len(a6)} rows)")

# ─── ANALYSIS 7 — NULL VALUE SUMMARY ────────────────────────────────────────

print(f"\n{SEP}")
print("  ANALYSIS 7 — Null Value Summary (after cleaning)")
print(SEP)

null_rows = []
for name, df in [("Sales", df_sales), ("Chargement", df_charg),
                 ("OpeningStock", df_open), ("PoS", df_pos), ("Items", df_items)]:
    for col in df.columns:
        nc = int(df[col].isna().sum())
        if nc > 0:
            null_rows.append({
                "Category": name,
                "Column": col,
                "Null_Count": nc,
                "Total_Rows": len(df),
                "Null_Pct": round(nc / len(df) * 100, 1),
            })

a7 = pd.DataFrame(null_rows).sort_values(["Category", "Null_Pct"], ascending=[True, False])
if len(a7) > 0:
    print(a7.to_string(index=False))
else:
    print("  [OK]  No null values found in any cleaned file.")

p = save(a7, "A7_null_summary.csv")
print(f"\n  --> Saved: {p.name}")

# ─── FINAL SUMMARY ──────────────────────────────────────────────────────────

print(f"\n{SEP}")
print("  ANALYSIS COMPLETE — All results saved to  analysis_results/")
print(SEP)

results_files = list(OUT.glob("*.csv"))
print(f"\n  Output files ({len(results_files)}):")
for f in sorted(results_files):
    size = f.stat().st_size
    print(f"    {f.name:<50}  {size:>8} bytes")

print()
print(f"  Key findings:")
print(f"    Total revenue (all companies)    : {df_sales['Total'].sum():>15,.0f} DA")
print(f"    Total transactions (Sales)       : {len(df_sales):>15,}")
print(f"    Total items sold (units)         : {df_items['Qté vendue'].sum():>15,}")
print(f"    Total client visits (PoS)        : {len(df_pos):>15,}")
print(f"    Over-sold article-VAN pairs      : {len(over_sold):>15}")
print(f"    Inventory deficit pairs          : {len(deficit):>15}")

print(f"\n{SEP}")
