# -*- coding: utf-8 -*-
"""
===================================================
  DELISKY WORKFLOW -- DATA INTEGRITY REPORT SCRIPT
  Analyzes 15 Excel files for:
    1. Column names & data types
    2. Date format consistency
    3. VAN name consistency across file categories
===================================================
"""

import sys, os, re
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Force UTF-8 output so Arabic / special chars display correctly on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --------------------------------------------------------------------------- #
#  CONFIG
# --------------------------------------------------------------------------- #
FOLDER = Path(
    r"c:\Users\radou\OneDrive\Desktop\google Antigravity"
    r"\new red project V1.0\delisky workflow V1.0"
)

# Categories whose files may contain VAN / truck names
VAN_CATEGORIES = ["Sales", "Chargement", "OpeningStock"]

# Substring hints to locate VAN columns (case-insensitive)
VAN_COL_HINTS  = ["van", "truck", "vehicle", "camion"]

# Substring hints to locate DATE columns (case-insensitive)
DATE_COL_HINTS = ["date", "day", "jour"]

SEP  = "=" * 72
SEP2 = "-" * 72

# --------------------------------------------------------------------------- #
#  HELPERS
# --------------------------------------------------------------------------- #

def detect_columns(df: pd.DataFrame, hints: list) -> list:
    """Return column names that match any hint substring (case-insensitive)."""
    return [c for c in df.columns if any(h in c.lower() for h in hints)]


def infer_date_format(series: pd.Series) -> str:
    """Guess the dominant date format string from a text column sample."""
    sample = series.dropna().astype(str).head(30)
    patterns = {
        r"^\d{4}-\d{2}-\d{2}$":       "YYYY-MM-DD",
        r"^\d{2}/\d{2}/\d{4}$":       "DD/MM/YYYY",
        r"^\d{2}-\d{2}-\d{4}$":       "DD-MM-YYYY",
        r"^\d{2}\.\d{2}\.\d{4}$":     "DD.MM.YYYY",
        r"^\d{4}/\d{2}/\d{2}$":       "YYYY/MM/DD",
        r"^\d{1,2}/\d{1,2}/\d{2,4}$": "D/M/YY or D/M/YYYY",
    }
    counts = defaultdict(int)
    for val in sample:
        for pat, label in patterns.items():
            if re.match(pat, val.strip()):
                counts[label] += 1
                break
        else:
            counts["UNKNOWN/MIXED"] += 1
    return max(counts, key=counts.get) if counts else "EMPTY"


def check_parseable(series: pd.Series):
    """Return (parseable_count, total_non_null)."""
    non_null = series.dropna()
    parsed   = pd.to_datetime(non_null, errors="coerce", dayfirst=True)
    return int(parsed.notna().sum()), len(non_null)


# --------------------------------------------------------------------------- #
#  LOAD ALL FILES
# --------------------------------------------------------------------------- #

files = sorted(FOLDER.glob("*.xlsx"))

print(SEP)
print("  DELISKY WORKFLOW -- DATA INTEGRITY REPORT")
print(f"  Folder : {FOLDER}")
print(f"  Files  : {len(files)} found")
print(SEP)

dataframes: dict   = {}
load_errors: dict  = {}

for f in files:
    try:
        dataframes[f.name] = pd.read_excel(f, engine="openpyxl")
    except Exception as e:
        load_errors[f.name] = str(e)

if load_errors:
    print("\n[!] LOAD ERRORS")
    for fname, err in load_errors.items():
        print(f"    FAIL  {fname}: {err}")

# --------------------------------------------------------------------------- #
#  SECTION 1 -- COLUMN NAMES & DATA TYPES
# --------------------------------------------------------------------------- #

print(f"\n{SEP}")
print("  SECTION 1 -- COLUMN NAMES & DATA TYPES  (per file)")
print(SEP)

for fname, df in dataframes.items():
    print(f"\n  FILE : {fname}  [{len(df)} rows x {len(df.columns)} columns]")
    print(f"  {'COLUMN':<42} {'DTYPE':<18} {'NON-NULL':>10} {'NULL':>8}")
    print(f"  {'-'*42} {'-'*18} {'-'*10} {'-'*8}")
    for col in df.columns:
        nn = df[col].notna().sum()
        nl = df[col].isna().sum()
        print(f"  {col:<42} {str(df[col].dtype):<18} {nn:>10} {nl:>8}")

# --------------------------------------------------------------------------- #
#  SECTION 2 -- DATE FORMAT CONSISTENCY
# --------------------------------------------------------------------------- #

print(f"\n{SEP}")
print("  SECTION 2 -- DATE FORMAT CONSISTENCY")
print(SEP)

all_dates_ok = True
date_rows = []

for fname, df in dataframes.items():
    date_cols = detect_columns(df, DATE_COL_HINTS)
    if not date_cols:
        date_rows.append({
            "file": fname, "col": "(none)", "format": "No date column detected",
            "parsed": "-", "total": "-", "status": "WARN"
        })
        continue
    for col in date_cols:
        ser = df[col]
        if pd.api.types.is_datetime64_any_dtype(ser):
            fmt    = "datetime64 (pre-parsed)"
            ok     = int(ser.notna().sum())
            total  = ok
            status = "OK"
        else:
            fmt          = infer_date_format(ser.astype(str))
            ok, total    = check_parseable(ser)
            pct          = (ok / total * 100) if total else 0
            if pct < 95:
                status = f"FAIL ({pct:.1f}% parseable)"
                all_dates_ok = False
            elif fmt in ("UNKNOWN/MIXED", "EMPTY"):
                status = "WARN (mixed/unknown format)"
                all_dates_ok = False
            else:
                status = "OK"
        date_rows.append({
            "file": fname, "col": col, "format": fmt,
            "parsed": ok, "total": total, "status": status
        })

print(f"\n  {'FILE':<42} {'COLUMN':<20} {'FORMAT':<22} {'PARSED':>12}  STATUS")
print(f"  {'-'*42} {'-'*20} {'-'*22} {'-'*12}  {'-'*24}")
for r in date_rows:
    ratio = f"{r['parsed']}/{r['total']}" if r["total"] != "-" else "-"
    mark  = "[OK]  " if r["status"] == "OK" else "[WARN]" if "WARN" in r["status"] else "[FAIL]"
    print(f"  {r['file']:<42} {r['col']:<20} {r['format']:<22} {ratio:>12}  {mark} {r['status']}")

verdict = "ALL DATE COLUMNS ARE CONSISTENT AND PARSEABLE" if all_dates_ok else \
          "SOME DATE COLUMNS HAVE ISSUES -- review the table above"
print(f"\n  >> {verdict}")

# --------------------------------------------------------------------------- #
#  SECTION 3 -- VAN NAME CONSISTENCY
# --------------------------------------------------------------------------- #

print(f"\n{SEP}")
print("  SECTION 3 -- VAN / TRUCK NAME CONSISTENCY")
print(f"  Categories checked : {', '.join(VAN_CATEGORIES)}")
print(SEP)

van_sets = defaultdict(dict)   # {category: {company: set_of_vans}}

for fname, df in dataframes.items():
    for cat in VAN_CATEGORIES:
        if fname.startswith(cat + "_"):
            company  = fname[len(cat) + 1:].split("_")[0]
            van_cols = detect_columns(df, VAN_COL_HINTS)
            if van_cols:
                col  = van_cols[0]
                vans = set(df[col].dropna().astype(str).str.strip().str.upper().unique())
                van_sets[cat][company] = vans
                print(f"\n  FILE : {fname}")
                print(f"  VAN column detected : '{col}'")
                for v in sorted(vans):
                    print(f"    - {v}")
            else:
                print(f"\n  FILE : {fname}")
                print(f"  [WARN] No VAN column detected (hints: {VAN_COL_HINTS})")
            break

print(f"\n  {SEP2}")
print("  CROSS-FILE VAN CONSISTENCY CHECK")
print(f"  {SEP2}")

van_ok = True

for cat, company_vans in van_sets.items():
    if not company_vans:
        continue
    all_vans  = set.union(*company_vans.values())
    companies = list(company_vans.keys())
    print(f"\n  Category : {cat}  |  Unique VAN values across all files : {len(all_vans)}")

    if len(companies) < 2:
        print("  (Only one company file -- nothing to cross-check)")
        continue

    issues_found = False
    for van in sorted(all_vans):
        missing = [c for c in companies if van not in company_vans.get(c, set())]
        if missing:
            print(f"  [WARN] '{van}'  is missing from : {', '.join(missing)}")
            van_ok = False
            issues_found = True

    if not issues_found:
        print(f"  [OK]  All VAN names match across : {', '.join(companies)}")

print("\n  NOTE: VAN values were normalised to UPPERCASE + stripped whitespace before comparison.")
print("        Original casing differences are NOT flagged -- see the per-file listings above.")

# --------------------------------------------------------------------------- #
#  SECTION 4 -- GLOBAL SUMMARY
# --------------------------------------------------------------------------- #

print(f"\n{SEP}")
print("  SECTION 4 -- GLOBAL DATA INTEGRITY SUMMARY")
print(SEP)

total_rows  = sum(len(df)                      for df in dataframes.values())
total_nulls = sum(int(df.isnull().sum().sum()) for df in dataframes.values())
total_cols  = sum(len(df.columns)              for df in dataframes.values())

date_verdict = "[OK]  PASSED" if all_dates_ok else "[FAIL] ISSUES FOUND"
van_verdict  = "[OK]  PASSED" if van_ok       else "[WARN] DIFFERENCES FOUND"

print(f"""
  Files loaded successfully  : {len(dataframes)} / {len(files)}
  Load errors                : {len(load_errors)}
  Total rows  (all files)    : {total_rows:,}
  Total columns (all files)  : {total_cols}
  Total null values          : {total_nulls:,}

  Date format consistency    : {date_verdict}
  VAN name consistency       : {van_verdict}
""")

print(SEP)
print("  END OF REPORT -- Ready to proceed with analysis logic")
print(SEP)
