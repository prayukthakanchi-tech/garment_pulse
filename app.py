"""
GarmentPulse — Fashion Category & Customer Decision Intelligence Platform
Main Streamlit Application Entrypoint
"""

from pathlib import Path
import duckdb
import streamlit as st

from config.settings import (
    COLORS,
    DASHBOARD_ICON,
    DASHBOARD_SUBTITLE,
    DASHBOARD_TITLE,
    DATA_LIMITATIONS,
    DUCKDB_PATH,
)
from src.ingestion.db_loader import get_connection

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
# Custom CSS — Clean Editorial Fashion Aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Clean editorial typography */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Subtle main background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Sidebar branding */
    .sidebar-header {
        padding: 10px 0 20px 0;
        border-bottom: 1px solid #e9ecef;
        margin-bottom: 20px;
    }
    
    .brand-title {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #1a1a2e;
    }
    
    .brand-tagline {
        font-size: 0.8rem;
        color: #6c757d;
        margin-top: 2px;
    }
    
    /* Tabs & cards styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 600;
    }
    
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.7rem;
        font-weight: 700;
        color: #1a1a2e;
    }
    
    /* Limitation alert badge */
    .limitation-badge {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Database Connection
# ─────────────────────────────────────────────
@st.cache_resource
def load_db():
    if not DUCKDB_PATH.exists():
        return None
    # Read-only connection for responsive multi-threaded querying
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


conn = load_db()

# ─────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="sidebar-header">
    <div class="brand-title">{DASHBOARD_ICON} {DASHBOARD_TITLE}</div>
    <div class="brand-tagline">{DASHBOARD_SUBTITLE}</div>
</div>
""", unsafe_allow_html=True)

if conn is None:
    st.error(f"⚠️ Analytical database not found at `{DUCKDB_PATH}`. Please run data ingestion first.")
    st.stop()

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

selected_page_name = st.sidebar.radio(
    "Navigation Menu",
    options=list(pages.keys()),
    index=0,
)

# Sidebar metadata & limitation notices
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Data Governance Boundaries", expanded=False):
    st.markdown("""
    - Price is a **dimensionless normalised index**, not actual currency.
    - No order IDs exist; checkout baskets are grouped by customer/date.
    - No stockout or inventory records exist.
    - Independent academic portfolio project.
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
