"""
GarmentPulse Dashboard — Page 1: Executive Overview
High-level merchandising demand overview, portfolio KPIs, and volume trends.
"""

from typing import Any, Optional
import duckdb
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.components.metrics import render_kpi_row
from dashboard.components.charts import apply_chart_style
from dashboard.visualisations.category_charts import plot_category_ranking_bar
from dashboard.data_service import (
    get_executive_kpis,
    get_monthly_volume_trend,
    get_category_performance_cached,
    get_category_growth_cached,
)


def render(conn: Optional[duckdb.DuckDBPyConnection] = None) -> None:
    st.markdown("## Executive Merchandising Overview")
    st.markdown(
        "Macro demand signals, portfolio volume velocity, and top department contributions across the observation window."
    )

    # 1. Macro KPIs
    with st.spinner("Loading portfolio metrics..."):
        macro = get_executive_kpis()

    render_kpi_row([
        {
            "label": "Total Observed Lines",
            "value": f"{macro['total_volume']:,}",
            "help": "Total physical purchase records observed across historical transaction logs.",
        },
        {
            "label": "Unique Purchasing Customers",
            "value": f"{macro['total_customers']:,}",
            "help": "Distinct customer entities with at least one recorded purchase event.",
        },
        {
            "label": "Active Catalogue Articles",
            "value": f"{macro['total_articles']:,}",
            "help": "Distinct article SKUs purchased in transaction records.",
        },
        {
            "label": "Normalised Price Index",
            "value": f"{macro['avg_price_index']:.4f}",
            "help": "Dimensionless average price index (0 to 1). Not currency amount.",
        },
    ])

    st.markdown("---")

    # 2. Charts Row
    col1, col2 = st.columns([6, 6])

    with col1:
        dept_df = get_category_performance_cached(level="department", min_transactions=200)
        st.plotly_chart(plot_category_ranking_bar(dept_df, top_n=10), use_container_width=True)

    with col2:
        trend_df = get_monthly_volume_trend()
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=trend_df["month"],
                y=trend_df["monthly_volume"],
                mode="lines+markers",
                line=dict(color="#1E3A8A", width=2.5),
                marker=dict(size=5, color="#1D4ED8"),
                name="Monthly Purchase Volume",
                hovertemplate="Month: %{x|%Y-%m}<br>Volume: %{y:,}<extra></extra>",
            )
        )
        fig = apply_chart_style(
            fig,
            title="Portfolio Purchase Volume Trajectory (Monthly)",
            x_title="Observation Month",
            y_title="Purchase Lines",
            height=420,
            show_legend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # 3. Category Momentum Highlights
    st.markdown("### Category Demand Momentum Leaders")
    growth_df = get_category_growth_cached(level="department", min_transactions=200)
    top_accel = growth_df[growth_df["momentum_signal"] == "Accelerating Demand"].head(6)

    if not top_accel.empty:
        st.dataframe(
            top_accel[[
                "category_name", "recent_volume", "prev_volume",
                "volume_growth_pct", "customer_growth_pct", "momentum_signal"
            ]].rename(columns={
                "category_name": "Department",
                "recent_volume": "Recent 4-Wk Volume",
                "prev_volume": "Previous 4-Wk Volume",
                "volume_growth_pct": "Volume Growth (%)",
                "customer_growth_pct": "Customer Growth (%)",
                "momentum_signal": "Demand Signal",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No departments currently in Accelerating Demand phase under current filter criteria.")
