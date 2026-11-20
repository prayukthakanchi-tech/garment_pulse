"""
GarmentPulse Dashboard — Cached UI Filters
Provides responsive cached filters for departments, product groups, dates, and channels.
"""

from typing import List, Tuple
import duckdb
import streamlit as st


@st.cache_data
def get_filter_options(_conn: duckdb.DuckDBPyConnection) -> dict:
    """Extracts unique category options for selectboxes and multiselects."""
    depts = [r[0] for r in _conn.execute("SELECT DISTINCT department_name FROM articles ORDER BY department_name").fetchall()]
    garments = [r[0] for r in _conn.execute("SELECT DISTINCT garment_group_name FROM articles ORDER BY garment_group_name").fetchall()]
    prod_groups = [r[0] for r in _conn.execute("SELECT DISTINCT product_group_name FROM articles ORDER BY product_group_name").fetchall()]
    date_bounds = _conn.execute("SELECT MIN(t_dat), MAX(t_dat) FROM transactions").fetchone()

    return {
        "departments": depts,
        "garments": garments,
        "product_groups": prod_groups,
        "min_date": str(date_bounds[0]),
        "max_date": str(date_bounds[1]),
    }


def render_sidebar_filters(conn: duckdb.DuckDBPyConnection) -> dict:
    """Standardized filter panel rendered in the Streamlit sidebar."""
    options = get_filter_options(conn)

    st.sidebar.markdown("### 🔍 Filters & Scopes")

    # Date range selector
    date_range = st.sidebar.date_input(
        "Observation Window",
        value=[],
        help=f"Dataset range: {options['min_date']} to {options['max_date']}",
    )

    selected_dept = st.sidebar.selectbox(
        "Department Focus",
        options=["All Departments"] + options["departments"],
        index=0,
    )

    selected_channel = st.sidebar.selectbox(
        "Sales Channel",
        options=["All Channels", "Channel 1", "Channel 2"],
        index=0,
    )

    return {
        "date_range": date_range,
        "department": None if selected_dept == "All Departments" else selected_dept,
        "channel": None if selected_channel == "All Channels" else (1 if selected_channel == "Channel 1" else 2),
    }
