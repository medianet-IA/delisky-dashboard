# -*- coding: utf-8 -*-
"""
=============================================================
  DELISKY WORKFLOW — STREAMLIT DASHBOARD (ARABIC)
  Interactive Web Interface for Cleaning & Analysis
=============================================================
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import PIL.Image

# ─── CONFIG & STYLE ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="لوحة تحكم ديليسكي - Delisky Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark premium look and RTL support
st.markdown("""
    <style>
    /* Google Font for Arabic */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Cairo', sans-serif;
        # direction: rtl;
        # text-align: right;
    }
    
    .main {
        background-color: #0F172A;
        color: #F1F5F9;
    }
    
    /* RTL adjustments for Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        # direction: rtl;
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
    
    /* Global alignment for Arabic */
    h1, h2, h3, p, span, li, label {
        text-align: right;
        direction: rtl;
    }
    
    /* Metric label alignment */
    [data-testid="stMetricLabel"] {
        text-align: right !important;
        direction: rtl !important;
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
        st.error(f"خطأ في تحميل البيانات: {e}")
        return None, None, None, None, None, None

df_sales, df_items, df_pos, df_a1, df_a3, df_a4 = load_data()

# ─── SIDEBAR ────────────────────────────────────────────────────────────────
st.sidebar.title("🛠️ الفلاتر والمرشحات")

company_list = ["الكل"] + sorted(df_sales["Company"].unique().tolist())
selected_company = st.sidebar.selectbox("اختر الشركة", company_list)

van_list = ["الكل"]
if selected_company != "الكل":
    van_list += sorted(df_sales[df_sales["Company"] == selected_company]["VAN"].unique().tolist())
else:
    van_list += sorted(df_sales["VAN"].unique().tolist())

selected_van = st.sidebar.selectbox("اختر الشاحنة (VAN)", van_list)

filtered_sales = df_sales.copy()

# Date Filter
sales_dates = filtered_sales["Date"].dropna()
if not sales_dates.empty:
    min_date = min(sales_dates)
    max_date = max(sales_dates)
    date_range = st.sidebar.date_input("اختر الفترة الزمنية", [min_date, max_date], min_value=min_date, max_value=max_date)
else:
    date_range = []

# ─── FILTER LOGIC ──────────────────────────────────────────────────────────
if selected_company != "الكل":
    filtered_sales = filtered_sales[filtered_sales["Company"] == selected_company]
if selected_van != "الكل":
    filtered_sales = filtered_sales[filtered_sales["VAN"] == selected_van]

if len(date_range) == 2:
    filtered_sales = filtered_sales[filtered_sales["Date"].notna()]
    filtered_sales = filtered_sales[(filtered_sales["Date"] >= date_range[0]) & (filtered_sales["Date"] <= date_range[1])]

# Filter items/pos based on company/van (simplified)
filtered_items = df_items.copy()
filtered_pos   = df_pos.copy()
if selected_company != "الكل":
    filtered_items = filtered_items[filtered_items["Company"] == selected_company]
    filtered_pos   = filtered_pos[filtered_pos["Company"] == selected_company]
if selected_van != "الكل":
    filtered_items = filtered_items[filtered_items["VAN"] == selected_van]
    filtered_pos   = filtered_pos[filtered_pos["VAN"] == selected_van]

# ─── MAIN DASHBOARD ─────────────────────────────────────────────────────────
st.title("📊 لوحة تحكم ديليسكي - Delisky")
st.markdown("---")

# KPI Metrics
total_revenue = filtered_sales["Total"].sum()
total_trans   = len(filtered_sales)
total_units   = filtered_items["Qté vendue"].sum()
total_visits  = len(filtered_pos)

m1, m2, m3, m4 = st.columns(4)
m1.metric("إجمالي الإيرادات (DA)", f"{total_revenue:,.0f}")
m2.metric("عدد المعاملات", f"{total_trans:,}")
m3.metric("الكميات المباعة", f"{int(total_units):,}")
m4.metric("زيارات العملاء (PoS)", f"{total_visits:,}")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 التحليل البصري", "📑 سجل المبيعات", "🚚 مخزون الشاحنات", "🤖 ذكاء اصطناعي", "🛠️ صحة البيانات"])

with tab1:
    st.header("الرؤى والتحليلات البصرية")
    
    c_col1, c_col2 = st.columns(2)
    
    with c_col1:
        st.subheader("اتجاه الإيرادات اليومي")
        img1 = PIL.Image.open(CHARTS / "C1_revenue_per_van_per_day.png")
        st.image(img1, use_container_width=True)
        
        st.subheader("توزيع الإيرادات حسب المنطقة")
        img3 = PIL.Image.open(CHARTS / "C3_revenue_per_region.png")
        st.image(img3, use_container_width=True)

    with c_col2:
        st.subheader("إجمالي الإيرادات لكل شاحنة")
        img2 = PIL.Image.open(CHARTS / "C2_total_revenue_per_van.png")
        st.image(img2, use_container_width=True)
        
        st.subheader("المنتجات الأكثر مبيعاً")
        img4 = PIL.Image.open(CHARTS / "C4_top_articles.png")
        st.image(img4, use_container_width=True)

    st.markdown("---")
    st.subheader("توازن المخزون (الرصيد الافتتاحي + الشحن مقابل المبيعات)")
    img5 = PIL.Image.open(CHARTS / "C5_inventory_balance.png")
    st.image(img5, use_container_width=True)

with tab2:
    st.header("مستكشف المبيعات")
    st.dataframe(filtered_sales.sort_values("Date_Heure", ascending=False), use_container_width=True)
    
    st.subheader("ملخص الإيرادات حسب الشاحنة")
    van_summary = filtered_sales.groupby("VAN")["Total"].sum().sort_values(ascending=False).reset_index()
    # Translate column names for display
    van_summary.columns = ["الشاحنة", "إجمالي الإيرادات"]
    st.bar_chart(van_summary.set_index("الشاحنة"))

with tab3:
    st.header("توازن المخزون لكل شاحنة")
    st.dataframe(df_a4, use_container_width=True)
    
    st.subheader("جدول المقارنة التفصيلي")
    st.dataframe(df_a3, use_container_width=True)

with tab4:
    st.header("🧠 رؤى مدعومة بالذكاء الاصطناعي")
    st.info("هذه الرؤى تم توليدها باستخدام نماذج تعلم الآلة (Association Rules, K-Means).")
    
    ai_col1, ai_col2 = st.columns(2)
    
    with ai_col1:
        st.subheader("🛒 تحليل سلة المشتريات (ماذا يُباع معاً؟)")
        try:
            df_rules = pd.read_csv(RESULTS / "AI_market_basket_rules.csv")
            df_display = df_rules[['antecedents', 'consequents', 'confidence', 'lift']].copy()
            df_display.columns = ["المنتج الأول", "المنتج المرتبط", "الثقة", "الارتباط"]
            st.dataframe(df_display.head(50), use_container_width=True)
            st.caption("المنتج الأول: إذا اشترى العميل هذا... | المنتج المرتبط: فمن المرجح أن يشتري هذا أيضاً.")
        except:
            st.write("لم يتم العثور على بيانات سلة المشتريات.")

    with ai_col2:
        st.subheader("🔝 أولوية المنتجات (تحليل ABC)")
        try:
            df_abc = pd.read_csv(RESULTS / "AI_product_abc_analysis.csv")
            df_abc.columns = ["المنتج", "الكمية المباعة", "الإجمالي التراكمي", "إجمالي المبيعات", "النسبة التراكمية", "فئة التصنيف"]
            st.dataframe(df_abc[['المنتج', 'الكمية المباعة', 'فئة التصنيف']], use_container_width=True)
        except:
            st.write("لم يتم العثور على بيانات تحليل ABC.")

    st.markdown("---")
    st.subheader("👥 تقسيم العملاء (Clusters)")
    try:
        df_clusters = pd.read_csv(RESULTS / "AI_client_segments.csv")
        
        c_stats = df_clusters.groupby('Segment').agg({
            'Nom du client': 'count',
            'Total': 'mean',
            'Visits': 'mean'
        }).rename(columns={'Nom du client': 'عدد العملاء', 'Total': 'متوسط الإنفاق', 'Visits': 'متوسط الزيارات'}).reset_index()
        c_stats.columns = ["فئة العملاء", "عدد العملاء", "متوسط الإنفاق", "متوسط الزيارات"]
        
        st.write("ملخص حسب فئة العميل:")
        st.table(c_stats)
        
        st.write("قائمة العملاء التفصيلية:")
        df_clusters_display = df_clusters[['Nom du client', 'Total', 'Visits', 'Segment']]
        df_clusters_display.columns = ["اسم العميل", "إجمالي الإنفاق", "عدد الزيارات", "فئة العميل"]
        st.dataframe(df_clusters_display, use_container_width=True)
    except:
        st.write("لم يتم العثور على بيانات تقسيم العملاء.")

with tab5:
    st.header("🛠️ مراقبة جودة البيانات")
    
    st.subheader("تواريخ PoS غير القابلة للتحليل")
    try:
        df_bad = pd.read_csv(CLEANED / "PoS_unparseable_dates.csv")
        st.warning(f"إجمالي الصفوف ذات التواريخ الخاطئة: {len(df_bad)}")
        st.dataframe(df_bad.head(100))
    except:
        st.success("لم يتم العثور على أي تواريخ خاطئة في PoS!")

    st.subheader("ملخص القيم المفقودة (Nulls)")
    try:
        df_nulls = pd.read_csv(RESULTS / "A7_null_summary.csv")
        df_nulls.columns = ["الملف", "العمود", "عدد المفقود", "النسبة %"]
        st.dataframe(df_nulls)
    except:
        st.info("ملخص القيم المفقودة غير متاح.")

# ─── FOOTER ────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.info("📌 تم التطوير بواسطة Antigravity | 2026")
st.sidebar.write(f"آخر تحديث: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
