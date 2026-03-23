# -*- coding: utf-8 -*-
"""
=============================================================
  DELISKY WORKFLOW — STREAMLIT DASHBOARD
  Interactive Web Interface for Cleaning & Analysis
=============================================================
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import PIL.Image

# ─── CONFIG & STYLE ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Delisky Workflow Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark premium look
st.markdown("""
    <style>
    .main {
        background-color: #0F172A;
        color: #F1F5F9;
    }
    .stMetric {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    div[data-testid="stMetricValue"] {
        color: #38BDF8;
    }
    .stDataFrame {
        border: 1px solid #334155;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ─── PATHS ──────────────────────────────────────────────────────────────────
BASE    = Path(__file__).parent
CLEANED = BASE / "cleaned"
RESULTS = BASE / "analysis_results"
CHARTS  = BASE / "charts"

# ─── DATA LOADING ────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        sales = pd.read_csv(CLEANED / "Sales_all.csv", encoding="utf-8-sig")
        items = pd.read_csv(CLEANED / "Items_all.csv", encoding="utf-8-sig")
        pos   = pd.read_csv(CLEANED / "PoS_all.csv",   encoding="utf-8-sig")
        
        # Pre-process dates
        sales["Date_Heure"] = pd.to_datetime(sales["Date_Heure"], errors="coerce")
        sales["Date"]       = sales["Date_Heure"].dt.date
        
        # Load Analysis results
        a1 = pd.read_csv(RESULTS / "A1_sales_per_van_per_day.csv")
        a3 = pd.read_csv(RESULTS / "A3_chargement_vs_sales.csv")
        a4 = pd.read_csv(RESULTS / "A4_inventory_balance_by_van.csv")
        
        return sales, items, pos, a1, a3, a4
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, None, None, None

df_sales, df_items, df_pos, df_a1, df_a3, df_a4 = load_data()

# ─── SIDEBAR ────────────────────────────────────────────────────────────────
st.sidebar.title("🛠️ Filters")

company_list = ["All"] + sorted(df_sales["Company"].unique().tolist())
selected_company = st.sidebar.selectbox("Select Company", company_list)

van_list = ["All"]
if selected_company != "All":
    van_list += sorted(df_sales[df_sales["Company"] == selected_company]["VAN"].unique().tolist())
else:
    van_list += sorted(df_sales["VAN"].unique().tolist())

selected_van = st.sidebar.selectbox("Select VAN", van_list)

filtered_sales = df_sales.copy()
# Date Filter
sales_dates = filtered_sales["Date"].dropna()
if not sales_dates.empty:
    min_date = min(sales_dates)
    max_date = max(sales_dates)
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
else:
    date_range = []

# ─── FILTER LOGIC ──────────────────────────────────────────────────────────
if selected_company != "All":
    filtered_sales = filtered_sales[filtered_sales["Company"] == selected_company]
if selected_van != "All":
    filtered_sales = filtered_sales[filtered_sales["VAN"] == selected_van]

if len(date_range) == 2:
    # Ensure filtered_sales["Date"] is compared correctly
    filtered_sales = filtered_sales[filtered_sales["Date"].notna()]
    filtered_sales = filtered_sales[(filtered_sales["Date"] >= date_range[0]) & (filtered_sales["Date"] <= date_range[1])]

# Filter items/pos based on company/van (simplified)
filtered_items = df_items.copy()
filtered_pos   = df_pos.copy()
if selected_company != "All":
    filtered_items = filtered_items[filtered_items["Company"] == selected_company]
    filtered_pos   = filtered_pos[filtered_pos["Company"] == selected_company]
if selected_van != "All":
    filtered_items = filtered_items[filtered_items["VAN"] == selected_van]
    filtered_pos   = filtered_pos[filtered_pos["VAN"] == selected_van]

# ─── MAIN DASHBOARD ─────────────────────────────────────────────────────────
st.title("📊 Delisky Dashboard")
st.markdown("---")

# KPI Metrics
total_revenue = filtered_sales["Total"].sum()
total_trans   = len(filtered_sales)
total_units   = filtered_items["Qté vendue"].sum()
total_visits  = len(filtered_pos)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Revenue (DA)", f"{total_revenue:,.0f}")
m2.metric("Total Transactions", f"{total_trans:,}")
m3.metric("Total Units Sold", f"{int(total_units):,}")
m4.metric("Client Visits (PoS)", f"{total_visits:,}")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Visual Analysis", "📑 Detailed Jars", "🚚 VAN Inventory", "🛠️ Data Health"])

with tab1:
    st.header("Visual Insights")
    
    c_col1, c_col2 = st.columns(2)
    
    with c_col1:
        st.subheader("Daily Revenue Trends")
        img1 = PIL.Image.open(CHARTS / "C1_revenue_per_van_per_day.png")
        st.image(img1, use_container_width=True)
        
        st.subheader("Regional Distribution")
        img3 = PIL.Image.open(CHARTS / "C3_revenue_per_region.png")
        st.image(img3, use_container_width=True)

    with c_col2:
        st.subheader("Total Revenue per VAN")
        img2 = PIL.Image.open(CHARTS / "C2_total_revenue_per_van.png")
        st.image(img2, use_container_width=True)
        
        st.subheader("Top Best Selling Articles")
        img4 = PIL.Image.open(CHARTS / "C4_top_articles.png")
        st.image(img4, use_container_width=True)

    st.markdown("---")
    st.subheader("Inventory Balance (Opening + Load vs Sold)")
    img5 = PIL.Image.open(CHARTS / "C5_inventory_balance.png")
    st.image(img5, use_container_width=True)

with tab2:
    st.header("Sales Explorer")
    st.dataframe(filtered_sales.sort_values("Date_Heure", ascending=False), use_container_width=True)
    
    st.subheader("Summary by VAN")
    van_summary = filtered_sales.groupby("VAN")["Total"].sum().sort_values(ascending=False).reset_index()
    st.bar_chart(van_summary.set_index("VAN"))

with tab3:
    st.header("VAN Level Balance (Opening + Loaded vs Sold)")
    st.dataframe(df_a4, use_container_width=True)
    
    st.subheader("Comparison Table")
    st.dataframe(df_a3, use_container_width=True)

with tab4:
    st.header("Data Integrity & Issues")
    
    st.subheader("Unparseable PoS Dates")
    try:
        df_bad = pd.read_csv(CLEANED / "PoS_unparseable_dates.csv")
        st.warning(f"Total rows with unparseable dates: {len(df_bad)}")
        st.dataframe(df_bad.head(100))
    except:
        st.success("No unparseable PoS dates found!")

    st.subheader("Null Summary")
    try:
        df_nulls = pd.read_csv(RESULTS / "A7_null_summary.csv")
        st.dataframe(df_nulls)
    except:
        st.info("Null summary not available.")

# ─── FOOTER ────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.info("📌 Dashboard created by Antigravity | 2026")
st.sidebar.write(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
