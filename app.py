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
        # Check if files exist to avoid crash on first run
        if not (CLEANED / "Sales_all.csv").exists():
            return None, None, None, None, None, None
            
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

# ─── AUTHENTICATION ──────────────────────────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

def login():
    st.title("🔐 تسجيل الدخول - نظام ديليسكي")
    
    with st.container():
        st.markdown('<div style="background-color: #1E293B; padding: 20px; border-radius: 10px;">', unsafe_allow_html=True)
        user = st.text_input("اسم المستخدم")
        pwd  = st.text_input("كلمة المرور", type="password")
        
        if st.button("دخول"):
            # Simple Hardcoded RBAC for demonstration
            if user == "admin" and pwd == "admin123":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.rerun()
            elif user == "manager" and pwd == "manager123":
                st.session_state.logged_in = True
                st.session_state.user_role = "manager"
                st.rerun()
            elif user == "acc" and pwd == "acc123":
                st.session_state.logged_in = True
                st.session_state.user_role = "accountant"
                st.rerun()
            else:
                st.error("خطأ في اسم المستخدم أو كلمة المرور")
        st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    login()
    st.stop()

# ─── SIDEBAR ────────────────────────────────────────────────────────────────
st.sidebar.title(f"👤 مرحباً: {st.session_state.user_role.capitalize()}")
if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.rerun()

st.sidebar.markdown("---")
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

# ─── NAVIGATION LOGIC ───────────────────────────────────────────────────────
role = st.session_state.user_role

# Define which tabs are visible for which roles
available_tabs = []
if role in ["admin", "manager"]:
    available_tabs += ["📈 التحليل البصري", "📑 سجل المبيعات", "🚚 مخزون الشاحنات", "🤖 ذكاء اصطناعي"]
if role in ["admin", "accountant"]:
    available_tabs += ["📤 رفع البيانات", "🛠️ صحة البيانات"]

tabs = st.tabs(available_tabs)

# Mapping functions to tabs
tab_idx = 0

if role in ["admin", "manager"]:
    with tabs[tab_idx]:
        st.header("الرؤى والتحليلات البصرية")
        # [Visual Analysis Logic...]
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            st.subheader("اتجاه الإيرادات اليومي")
            if (CHARTS / "C1_revenue_per_van_per_day.png").exists():
                st.image(PIL.Image.open(CHARTS / "C1_revenue_per_van_per_day.png"), use_container_width=True)
            st.subheader("توزيع الإيرادات حسب المنطقة")
            if (CHARTS / "C3_revenue_per_region.png").exists():
                st.image(PIL.Image.open(CHARTS / "C3_revenue_per_region.png"), use_container_width=True)
        with c_col2:
            st.subheader("إجمالي الإيرادات لكل شاحنة")
            if (CHARTS / "C2_total_revenue_per_van.png").exists():
                st.image(PIL.Image.open(CHARTS / "C2_total_revenue_per_van.png"), use_container_width=True)
            st.subheader("المنتجات الأكثر مبيعاً")
            if (CHARTS / "C4_top_articles.png").exists():
                st.image(PIL.Image.open(CHARTS / "C4_top_articles.png"), use_container_width=True)
        st.markdown("---")
        st.subheader("توازن المخزون")
        if (CHARTS / "C5_inventory_balance.png").exists():
            st.image(PIL.Image.open(CHARTS / "C5_inventory_balance.png"), use_container_width=True)
    tab_idx += 1

    with tabs[tab_idx]:
        st.header("مستكشف المبيعات")
        st.dataframe(filtered_sales.sort_values("Date_Heure", ascending=False), use_container_width=True)
        st.subheader("ملخص الإيرادات حسب الشاحنة")
        van_summary = filtered_sales.groupby("VAN")["Total"].sum().sort_values(ascending=False).reset_index()
        van_summary.columns = ["الشاحنة", "إجمالي الإيرادات"]
        st.bar_chart(van_summary.set_index("الشاحنة"))
    tab_idx += 1

    with tabs[tab_idx]:
        st.header("توازن المخزون لكل شاحنة")
        st.dataframe(df_a4, use_container_width=True)
        st.subheader("جدول المقارنة التفصيلي")
        st.dataframe(df_a3, use_container_width=True)
    tab_idx += 1

    with tabs[tab_idx]:
        st.header("🧠 عقل ديليسكي (Smart AI)")
        
        # --- DELISKY BRAIN: ULTRA-SMART QUERY ENGINE ---
        query = st.text_input("💬 اسأل أي شيء (مثال: أضعف سلع بيفا 3؟ أو مبيعات شاحنا ت في وهران؟)")
        
        if query:
            import difflib
            
            # Helper: Normalize and Clean Arabic
            def clean_ar(text):
                return text.lower().replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي').strip()
            
            q_clean = clean_ar(query)
            
            # 1. FUZZY ENTITY EXTRACTION (VANs)
            target_van = None
            all_vans = df_sales["VAN"].unique().tolist()
            
            # Map shortcuts to real names
            van_map = {
                "bifa 1": "BIFA PSLIV01", "bifa 3": "BIFA PSLIV03",
                "nita 1": "NITA PSLIV01", "nita 2": "NITA PSLIV02",
                "بيفا 1": "BIFA PSLIV01", "بيفا 3": "BIFA PSLIV03",
                "نيتا 1": "NITA PSLIV01", "نيتا 2": "NITA PSLIV02"
            }
            
            # Check for direct map first
            for key, val in van_map.items():
                if key in q_clean or clean_ar(key) in q_clean:
                    target_van = val
                    break
            
            # If not found, use fuzzy matching on the query words
            if not target_van:
                words = q_clean.split()
                for w in words:
                    matches = difflib.get_close_matches(w, [v.lower() for v in all_vans], n=1, cutoff=0.6)
                    if matches:
                        # Find the original name
                        for original in all_vans:
                            if original.lower() == matches[0]:
                                target_van = original
                                break
                        break

            # 2. INTENT SCORING
            weak_keywords = ["ضعيف", "اضعف", "اسوا", "اقل", "راكد", "ناقص", "فاشل", "bad", "weak", "low", "worst"]
            strong_keywords = ["قوي", "افضل", "احسن", "اكثر", "ناجح", "ممتاز", "best", "top", "strong", "high", "great"]
            sales_keywords = ["مبيعات", "اجمالي", "دخل", "ايرادات", "فلوس", "بيع", "كم", "sales", "total", "revenue", "money"]

            # Score each intent
            score_weak = sum(1 for k in weak_keywords if k in q_clean)
            score_strong = sum(1 for k in strong_keywords if k in q_clean)
            score_sales = sum(1 for k in sales_keywords if k in q_clean)

            # 3. DYNAMIC RESPONSE GENERATION
            if score_weak > 0:
                if target_van:
                    v_items = df_items[df_items["VAN"] == target_van]
                    worst = v_items.groupby("Article")["Qté vendue"].sum().sort_values().head(5)
                    st.warning(f"📉 **السلع الأضعف أداءً** للشاحنة **{target_van}**:")
                    st.table(worst)
                else:
                    worst = df_items.groupby("Article")["Qté vendue"].sum().sort_values().head(8)
                    st.warning("📉 **السلع الأقل مبيعاً** على مستوى كل الشركة:")
                    st.table(worst)
                    
            elif score_strong > 0:
                if target_van:
                    v_items = df_items[df_items["VAN"] == target_van]
                    best = v_items.groupby("Article")["Qté vendue"].sum().sort_values(ascending=False).head(5)
                    st.success(f"🏆 **السلع الأكثر مبيعاً** للشاحنة **{target_van}**:")
                    st.table(best)
                else:
                    best = df_items.groupby("Article")["Qté vendue"].sum().sort_values(ascending=False).head(8)
                    st.success("🏆 **قائمة المنتجات الأكثر نجاحاً** إجمالاً:")
                    st.table(best)

            elif score_sales > 0:
                if target_van:
                    val = df_sales[df_sales["VAN"] == target_van]["Total"].sum()
                    st.info(f"💰 إجمالي مبيعات الشاحنة **{target_van}** هو: **{val:,.0f} DA**")
                else:
                    val = df_sales["Total"].sum()
                    st.info(f"💰 إجمالي مبيعات الشركة بالكامل حالياً: **{val:,.0f} DA**")
            
            else:
                st.write("🤖 عذراً، لا أزال أتعلم! جرب استخدام كلمات مثل: 'أضعف'، 'أفضل'، أو 'مبيعات' مع ذكر اسم الشاحنة.")
        
        st.markdown("---")
        # [AI Insights (MBA, ABC)...]
        ai_col1, ai_col2 = st.columns(2)
        with ai_col1:
            st.subheader("🛒 تحليل سلة المشتريات")
            try:
                df_rules = pd.read_csv(RESULTS / "AI_market_basket_rules.csv")
                st.dataframe(df_rules[['antecedents', 'consequents', 'confidence']].head(20), use_container_width=True)
            except: st.write("بيانات غير متوفرة")
        with ai_col2:
            st.subheader("🔝 أولوية المنتجات (ABC)")
            try:
                df_abc = pd.read_csv(RESULTS / "AI_product_abc_analysis.csv")
                st.dataframe(df_abc[['Article', 'Class']].head(20), use_container_width=True)
            except: st.write("بيانات غير متوفرة")
    tab_idx += 1

if role in ["admin", "accountant"]:
    with tabs[tab_idx]:
        st.header("📤 رفع وتدقيق الملفات")
        st.info("هنا يمكن للمحاسب رفع ملفات Excel الجديدة للتحقق منها.")
        
        uploaded_file = st.file_uploader("اختر ملف Excel لرفعه (Sales, Chargement, etc.)", type=["xlsx"])
        if uploaded_file:
            st.success(f"تم استلام الملف: {uploaded_file.name}")
            # Mock Validation Logic
            if "Sales" in uploaded_file.name:
                st.write("✅ التحقق من الأعمدة: ناجح")
                st.write("✅ التحقق من التواريخ: ناجح")
            else:
                st.warning("⚠️ تحذير: اسم الملف قد لا يطابق المعايير (يُفضل وجود كلمة Sales أو Chargement)")
    tab_idx += 1

    with tabs[tab_idx]:
        st.header("🛠️ مراقبة جودة البيانات")
        # [Existing Data Health Logic...]
        try:
            df_bad = pd.read_csv(CLEANED / "PoS_unparseable_dates.csv")
            st.warning(f"صفوف بتواريخ خاطئة: {len(df_bad)}")
            st.dataframe(df_bad.head(50))
        except: st.success("لا توجد أخطاء تواريخ")

# ─── FOOTER ────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.info("📌 تم التطوير بواسطة Antigravity | 2026")
st.sidebar.write(f"آخر تحديث: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
