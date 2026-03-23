# -*- coding: utf-8 -*-
"""
=============================================================
  DELISKY WORKFLOW — DATA CLEANING SCRIPT
  Fixes:
    1. Date columns (Sales Date&Heure, PoS Date) → datetime64
    2. BIFA VAN typo  (PSLIV02 → PSLIV01 in OpeningStock)
    3. DELISKY LIV03 missing from Chargement  (flagged, not invented)
    4. Adds Company column to every DataFrame
  Outputs:
    → cleaned/ subfolder with one CSV per merged category
=============================================================
"""

import sys, os
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─── PATHS ──────────────────────────────────────────────────────────────────
BASE   = Path(__file__).parent
FOLDER = BASE / "delisky workflow V1.0"
OUT    = BASE / "cleaned"
OUT.mkdir(exist_ok=True)

SEP  = "=" * 72
SEP2 = "-" * 72

# ─── KNOWN FIX CONSTANTS ────────────────────────────────────────────────────
# BIFA: OpeningStock uses PSLIV02 but Chargement & Sales use PSLIV01
BIFA_VAN_OLD = "BIFA PSLIV02"
BIFA_VAN_NEW = "BIFA PSLIV01"

# Date format for Sales
SALES_DATE_FMT = "%d/%m/%Y %H:%M:%S"

# Date format for PoS
POS_DATE_FMT = "%d/%m/%Y"

# ─── LOAD HELPER ────────────────────────────────────────────────────────────

def load(filename: str) -> pd.DataFrame:
    path = FOLDER / filename
    return pd.read_excel(path, engine="openpyxl")


def add_company(df: pd.DataFrame, company: str) -> pd.DataFrame:
    df = df.copy()
    df.insert(0, "Company", company)
    return df

# ─── LOAD ALL FILES ─────────────────────────────────────────────────────────

print(SEP)
print("  DELISKY WORKFLOW -- DATA CLEANING")
print(SEP)

companies = ["BIFA", "DELISKY", "NITA"]

raw: dict = {}  # raw[category][company] = df

categories_files = {
    "Sales":        "Sales_{company}_2026-03-07_2026-03-11.xlsx",
    "Chargement":   "Chargement_{company}_2026-03-07_2026-03-10.xlsx",
    "OpeningStock": "OpeningStock_{company}_2026-03-07.xlsx",
    "PoS":          "PoS_{company}_2026-03-07_2026-03-11.xlsx",
    "Items":        "Items_{company}_2026-03-07_2026-03-11.xlsx",
}

for cat, tmpl in categories_files.items():
    raw[cat] = {}
    for co in companies:
        fname = tmpl.format(company=co)
        try:
            raw[cat][co] = load(fname)
            print(f"  [OK]  Loaded  {fname}  ({len(raw[cat][co])} rows)")
        except Exception as e:
            print(f"  [ERR] Failed  {fname}: {e}")

# ─── FIX 1 — SALES: Date&Heure → datetime64 ─────────────────────────────────

print(f"\n{SEP2}")
print("  FIX 1 -- Sales  'Date&Heure'  →  datetime64")
print(SEP2)

date_fix_log = []

for co in companies:
    df = raw["Sales"][co].copy()
    col = "Date&Heure"
    if col not in df.columns:
        print(f"  [WARN] {co} Sales: column '{col}' not found — skipped")
        continue

    before_nulls = df[col].isna().sum()
    df[col] = pd.to_datetime(df[col], format=SALES_DATE_FMT, errors="coerce")
    after_nulls  = df[col].isna().sum()
    new_failures = max(0, after_nulls - before_nulls)

    # Rename to clean name
    df.rename(columns={col: "Date_Heure"}, inplace=True)

    raw["Sales"][co] = df
    status = "OK" if new_failures == 0 else f"WARN ({new_failures} rows failed to parse)"
    print(f"  [{status.split()[0]}]  {co} Sales: '{col}' converted  |  parse failures: {new_failures}")
    date_fix_log.append({"Company": co, "Category": "Sales", "ParseFailures": new_failures})

# ─── FIX 2 — PoS: Date → datetime64 ────────────────────────────────────────

print(f"\n{SEP2}")
print("  FIX 2 -- PoS  'Date'  →  datetime64")
print(SEP2)

pos_bad_rows: list[pd.DataFrame] = []

for co in companies:
    df = raw["PoS"][co].copy()
    col = "Date"
    if col not in df.columns:
        print(f"  [WARN] {co} PoS: column 'Date' not found — skipped")
        continue

    before_nulls = df[col].isna().sum()
    df[col] = pd.to_datetime(df[col], format=POS_DATE_FMT, errors="coerce")
    after_nulls  = df[col].isna().sum()
    new_failures = max(0, after_nulls - before_nulls)

    # Capture bad rows for diagnostics
    if new_failures > 0:
        bad = raw["PoS"][co][df[col].isna()].copy()
        bad.insert(0, "Company", co)
        pos_bad_rows.append(bad)

    raw["PoS"][co] = df
    status = "OK" if new_failures == 0 else f"WARN"
    print(f"  [{status}]  {co} PoS: 'Date' converted  |  parse failures: {new_failures}")
    date_fix_log.append({"Company": co, "Category": "PoS", "ParseFailures": new_failures})

# Save PoS unparseable rows for inspection
if pos_bad_rows:
    bad_df = pd.concat(pos_bad_rows, ignore_index=True)
    bad_path = OUT / "PoS_unparseable_dates.csv"
    bad_df.to_csv(bad_path, index=False, encoding="utf-8-sig")
    print(f"\n  [INFO] Saved {len(bad_df)} unparseable PoS rows → {bad_path.name}")

# ─── FIX 3 — BIFA VAN TYPO ──────────────────────────────────────────────────

print(f"\n{SEP2}")
print(f"  FIX 3 -- BIFA VAN typo: '{BIFA_VAN_OLD}' → '{BIFA_VAN_NEW}' in OpeningStock")
print(SEP2)

df_os_bifa = raw["OpeningStock"]["BIFA"].copy()
mask = df_os_bifa["VAN"] == BIFA_VAN_OLD
count = mask.sum()
df_os_bifa.loc[mask, "VAN"] = BIFA_VAN_NEW
raw["OpeningStock"]["BIFA"] = df_os_bifa
print(f"  [OK]  Replaced {count} occurrences of '{BIFA_VAN_OLD}' with '{BIFA_VAN_NEW}'")

# ─── FIX 4 — ADD COMPANY COLUMN & CONCATENATE ───────────────────────────────

print(f"\n{SEP2}")
print("  FIX 4 -- Adding 'Company' column & concatenating per category")
print(SEP2)

combined: dict[str, pd.DataFrame] = {}

for cat in categories_files:
    frames = []
    for co in companies:
        if co in raw[cat]:
            df = add_company(raw[cat][co], co)
            frames.append(df)
    if frames:
        merged = pd.concat(frames, ignore_index=True)
        combined[cat] = merged
        print(f"  [OK]  {cat:<15} → {len(merged):>6} rows  |  columns: {list(merged.columns)}")

# ─── FIX 5 — FLAG DELISKY LIV03 MISSING FROM CHARGEMENT ────────────────────

print(f"\n{SEP2}")
print("  FIX 5 -- Flagging DELISKY LIV03 (present in Sales/OpeningStock, absent from Chargement)")
print(SEP2)

charg = combined["Chargement"]
missing_van = "DELISKY LIV03"
is_present  = (charg["VAN"] == missing_van).any()

if not is_present:
    print(f"  [INFO] '{missing_van}' has NO rows in Chargement.")
    print(f"         This is documented — no data will be fabricated.")
    print(f"         Analysis scripts will show Chargement_Qty = 0 for this VAN.")
else:
    print(f"  [OK]  '{missing_van}' IS present in Chargement — no issue.")

# ─── SAVE CLEANED FILES ─────────────────────────────────────────────────────

print(f"\n{SEP2}")
print("  SAVING cleaned files to  →  cleaned/")
print(SEP2)

saved = []
for cat, df in combined.items():
    out_path = OUT / f"{cat}_all.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    saved.append(str(out_path.name))
    print(f"  [OK]  Saved  {out_path.name}  ({len(df)} rows x {len(df.columns)} cols)")

# ─── CLEANING SUMMARY ───────────────────────────────────────────────────────

print(f"\n{SEP}")
print("  CLEANING SUMMARY")
print(SEP)

print(f"""
  Files processed            : 15
  Date columns fixed         : Sales Date&Heure (3 files) + PoS Date (3 files)
  VAN typo fixed             : BIFA PSLIV02 → PSLIV01 in OpeningStock ({count} rows)
  Missing VAN flagged        : DELISKY LIV03 absent from Chargement (documented)
  Cleaned CSV files saved    : {len(saved)} → cleaned/ folder
""")

print("  Date parse failures per file:")
print(f"  {'Company':<12} {'Category':<14} {'ParseFailures':>14}")
print(f"  {'-'*12} {'-'*14} {'-'*14}")
for row in date_fix_log:
    flag = "  <-- REVIEW" if row["ParseFailures"] > 0 else ""
    print(f"  {row['Company']:<12} {row['Category']:<14} {row['ParseFailures']:>14}{flag}")

print(f"\n  Cleaned DataFrames ready for analysis:")
for cat, df in combined.items():
    nn = df.isnull().sum().sum()
    print(f"    combined['{cat}']  →  {len(df)} rows x {len(df.columns)} cols  |  nulls: {nn}")

print(f"\n{SEP}")
print("  CLEANING COMPLETE -- Run data_analysis.py to proceed")
print(SEP)
