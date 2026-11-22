"""
GarmentPulse — Fashion Category & Customer Decision Intelligence Platform
Main Streamlit Application Entrypoint
"""

from pathlib import Path
import streamlit as st

from config.settings import (
    COLORS,
    DASHBOARD_ICON,
    DASHBOARD_SUBTITLE,
    DASHBOARD_TITLE,
    DATA_LIMITATIONS,
    DUCKDB_PATH,
)
from src.database.connection import get_db_connection

# ─────────────────────────────────────────────
# Streamlit Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title=f"{DASHBOARD_TITLE} — Retail Intelligence",
    page_icon=DASHBOARD_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS — Premium Enterprise Fashion-Tech Aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Google Fonts typography import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0F172A;
    }
    
    /* Modern crisp slate background with top mesh highlight */
    .stApp {
        background-color: #F8FAFC;
        background-image: radial-gradient(at 50% 0%, rgba(241, 245, 249, 0.8) 0px, transparent 65%);
    }

    /* Main container max width and padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
        padding-left: 2.8rem;
        padding-right: 2.8rem;
        max-width: 1440px;
    }
    
    /* Sidebar styling — Deep Obsidian with subtle border */
    [data-testid="stSidebar"] {
        background-color: #090D16;
        border-right: 1px solid #1E293B;
    }

    [data-testid="stSidebar"] [class*="css"], [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #E2E8F0 !important;
    }

    /* Brand Header in Sidebar */
    .brand-container {
        padding: 12px 4px 18px 4px;
        border-bottom: 1px solid #1E293B;
        margin-bottom: 20px;
    }
    
    .brand-header-flex {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .brand-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        border-radius: 9px;
        color: #FFFFFF;
        font-weight: 800;
        font-size: 0.95rem;
        letter-spacing: -0.02em;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .brand-title {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #FFFFFF !important;
        line-height: 1.1;
    }
    
    .brand-tagline {
        font-size: 0.74rem;
        font-weight: 500;
        color: #94A3B8 !important;
        margin-top: 5px;
        line-height: 1.3;
    }

    .brand-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #34D399;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.25);
        padding: 3px 8px;
        border-radius: 9999px;
        margin-top: 10px;
    }
    
    .pulse-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 8px #10B981;
        display: inline-block;
    }

    .sidebar-nav-title {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B !important;
        margin-bottom: 8px;
        padding-left: 4px;
    }

    /* Transform Streamlit Radio Navigation into Linear/Stripe style Navigation Items */
    div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 3px;
    }

    div[data-testid="stRadio"] label > div:first-child {
        display: none !important;
    }

    div[data-testid="stRadio"] label {
        display: flex !important;
        align-items: center;
        padding: 9px 12px !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: #94A3B8 !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        cursor: pointer !important;
        transition: all 0.15s ease-in-out !important;
        margin: 0 !important;
    }

    div[data-testid="stRadio"] label:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #F8FAFC !important;
        border-color: rgba(255, 255, 255, 0.08) !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(90deg, rgba(37, 99, 235, 0.2) 0%, rgba(37, 99, 235, 0.05) 100%) !important;
        border-left: 3px solid #3B82F6 !important;
        border-top: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-right: 1px solid rgba(59, 130, 246, 0.1) !important;
        border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    /* Tabs styling — Modern Segmented Control */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #F1F5F9;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 4px;
        margin-bottom: 18px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        border-radius: 7px;
        font-weight: 600;
        font-size: 0.84rem;
        color: #64748B;
        background-color: transparent;
        border: none;
        transition: all 0.15s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
        border: 1px solid #E2E8F0 !important;
    }
    
    /* Metric styling override */
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
    }
    
    /* DataFrame containers */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        background: #FFFFFF;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        overflow: hidden;
    }

    /* Buttons styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.86rem;
        padding: 8px 18px;
        transition: all 0.15s ease-in-out;
        border: 1px solid #CBD5E1;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%);
        border: 1px solid #1D4ED8;
        color: #FFFFFF;
        box-shadow: 0 1px 3px rgba(37, 99, 235, 0.25);
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E3A8A 100%);
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35);
        transform: translateY(-1px);
    }

    /* Selectboxes and Inputs */
    div[data-baseweb="select"] {
        border-radius: 8px;
    }

    div[data-baseweb="select"] > div {
        border-radius: 8px;
        border-color: #CBD5E1;
        background-color: #FFFFFF;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02);
    }

    /* Headings hierarchy */
    h1, h2, h3 {
        color: #0F172A;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    h2 {
        font-size: 1.65rem;
        margin-bottom: 0.3rem;
    }

    h3 {
        font-size: 1.15rem;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }

    /* Custom expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1E293B;
        background-color: #FFFFFF;
        border-radius: 6px;
    }

    /* Limitation alert badge */
    .limitation-badge {
        background-color: #FEF3C7;
        border: 1px solid #FDE68A;
        color: #92400E;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        line-height: 1.4;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Database Connection Check & Cloud Native Bootstrap
# ─────────────────────────────────────────────
if not DUCKDB_PATH.exists():
    from src.database.bootstrap import bootstrap_database_if_needed
    with st.spinner("Initializing analytical database on cloud container..."):
        bootstrap_database_if_needed(DUCKDB_PATH)

if not DUCKDB_PATH.exists():
    st.error(f"Analytical database not found at `{DUCKDB_PATH}`. Please run data ingestion first.")
    st.stop()

# Obtain thread-local connection
conn = get_db_connection()

# ─────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="brand-container">
    <div class="brand-header-flex">
        <div class="brand-mark">GP</div>
        <div>
            <div class="brand-title">{DASHBOARD_TITLE}</div>
            <div class="brand-tagline">{DASHBOARD_SUBTITLE}</div>
        </div>
    </div>
    <div class="brand-status-pill">
        <span class="pulse-dot"></span>
        <span>LIVE OLAP ENGINE</span>
    </div>
</div>
""", unsafe_allow_html=True)

pages = {
    "1. Executive Overview": "p01",
    "2. Category Intelligence": "p02",
    "3. Fashion Attribute Intelligence": "p03",
    "4. Customer Intelligence": "p04",
    "5. Product Intelligence": "p05",
    "6. Sales Channel Analytics": "p06",
    "7. Recommendation Engine": "p07",
    "8. Demand Forecasting": "p08",
    "9. Category Opportunity Radar": "p09",
    "10. Data Quality & Governance": "p10",
}

st.sidebar.markdown('<div class="sidebar-nav-title">Intelligence Modules</div>', unsafe_allow_html=True)
selected_page_name = st.sidebar.radio(
    "Navigation Menu",
    options=list(pages.keys()),
    index=0,
    label_visibility="collapsed",
)

# Sidebar metadata & limitation notices
st.sidebar.markdown("""
<div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #1E293B;">
    <div style="font-size: 0.66rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #64748B; margin-bottom: 6px;">
        AUDITED DATA ARCHIVE
    </div>
    <div style="font-size: 0.74rem; color: #94A3B8; line-height: 1.6;">
        <div>Transactions: <span style="color: #F8FAFC; font-weight: 600;">31,788,324</span></div>
        <div>Customers: <span style="color: #F8FAFC; font-weight: 600;">1,362,281</span></div>
        <div>Engine: <span style="color: #60A5FA; font-weight: 600;">DuckDB Vectorized OLAP</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
with st.sidebar.expander("Data Governance Guardrails", expanded=False):
    st.markdown("""
    - **Price Index:** Dimensionless normalised index, not actual currency.
    - **Order IDs:** Not present; baskets grouped by customer & date.
    - **Inventory:** Zero stockout/inventory records available.
    - **Scope:** Independent academic portfolio project.
    """)

# ─────────────────────────────────────────────
# Page Router
# ─────────────────────────────────────────────
page_code = pages[selected_page_name]

if page_code == "p01":
    from dashboard.pages import p01_executive_overview
    p01_executive_overview.render(conn)
elif page_code == "p02":
    from dashboard.pages import p02_category_intelligence
    p02_category_intelligence.render(conn)
elif page_code == "p03":
    from dashboard.pages import p03_attribute_intelligence
    p03_attribute_intelligence.render(conn)
elif page_code == "p04":
    from dashboard.pages import p04_customer_intelligence
    p04_customer_intelligence.render(conn)
elif page_code == "p05":
    from dashboard.pages import p05_product_intelligence
    p05_product_intelligence.render(conn)
elif page_code == "p06":
    from dashboard.pages import p06_channel_analytics
    p06_channel_analytics.render(conn)
elif page_code == "p07":
    from dashboard.pages import p07_recommendations
    p07_recommendations.render(conn)
elif page_code == "p08":
    from dashboard.pages import p08_forecasting
    p08_forecasting.render(conn)
elif page_code == "p09":
    from dashboard.pages import p09_opportunity_radar
    p09_opportunity_radar.render(conn)
elif page_code == "p10":
    from dashboard.pages import p10_data_quality
    p10_data_quality.render(conn)
