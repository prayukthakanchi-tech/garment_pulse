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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0F172A;
    }
    
    /* Warm ivory / neutral background */
    .stApp {
        background-color: #FAF9F6;
    }

    /* Main container max width and padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }

    [data-testid="stSidebar"] [class*="css"], [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #E2E8F0 !important;
    }

    .sidebar-header {
        padding: 12px 4px 20px 4px;
        border-bottom: 1px solid #1E293B;
        margin-bottom: 20px;
    }
    
    .brand-title {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .brand-tagline {
        font-size: 0.78rem;
        font-weight: 500;
        color: #94A3B8 !important;
        margin-top: 4px;
        line-height: 1.3;
    }

    .sidebar-nav-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B !important;
        margin-bottom: 8px;
        padding-left: 2px;
    }
    
    /* Tabs & cards styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid #E2E8F0;
        background-color: transparent;
        padding-bottom: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        color: #475569;
        background-color: transparent;
        border: none;
        transition: all 0.15s ease-in-out;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
        border: 1px solid #E2E8F0;
    }
    
    /* Metric styling override */
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
    }
    
    /* DataFrame containers */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        background: #FFFFFF;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
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
        font-size: 1.25rem;
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
# Database Connection Check & Cloud Bootstrap
# ─────────────────────────────────────────────
CLOUD_DB_PATH = Path("data/garmentpulse_cloud.duckdb")

if not DUCKDB_PATH.exists():
    if CLOUD_DB_PATH.exists():
        try:
            import shutil
            DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(CLOUD_DB_PATH, DUCKDB_PATH)
        except Exception:
            pass

if not DUCKDB_PATH.exists() and not CLOUD_DB_PATH.exists():
    st.error(f"Analytical database not found at `{DUCKDB_PATH}`. Please run data ingestion first.")
    st.stop()

# Obtain thread-local connection
conn = get_db_connection()

# ─────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="sidebar-header">
    <div class="brand-title">{DASHBOARD_TITLE}</div>
    <div class="brand-tagline">{DASHBOARD_SUBTITLE}</div>
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
