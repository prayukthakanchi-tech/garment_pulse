"""
GarmentPulse Dashboard — Page 1: Executive Overview
High-level merchandising demand overview, portfolio KPIs, and volume trends.
"""

import duckdb
import streamlit as st
import pandas as pd

from dashboard.components.metrics import render_kpi_row
from dashboard.components.charts import apply_chart_style
from dashboard.visualisations.category_charts import plot_category_ranking_bar
from src.analytics.category_intelligence import CategoryIntelligence


def render(conn: duckdb.DuckDBPyConnection) -> None:
    st.markdown("## 📈 Executive Merchandising Overview")
    st.markdown(
        "Macro demand signals, portfolio volume velocity, and top department contributions across the observation window."
    )

    # 1. Macro KPIs
    kpi_sql = """
    SELECT
        COUNT(*) AS total_volume,
        COUNT(DISTINCT customer_id) AS total_customers,
        COUNT(DISTINCT article_id) AS total_articles,
        ROUND(AVG(price), 6) AS avg_price_index
    FROM transactions
    """
    macro = conn.execute(kpi_sql).fetchdf().to_dict(orient="records")[0]

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
    col1, col2 = st.columns([6, 5])

    ci = CategoryIntelligence(conn)
    dept_df = ci.get_category_performance(level="department")

    with col1:
        st.plotly_chart(plot_category_ranking_bar(dept_df, top_n=10), use_container_width=True)

    with col2:
        # Monthly Volume Trend
        trend_sql = """
        SELECT
            DATE_TRUNC('month', t_dat) AS month,
            COUNT(*) AS monthly_volume,
            COUNT(DISTINCT customer_id) AS active_customers
        FROM transactions
        GROUP BY DATE_TRUNC('month', t_dat)
        ORDER BY month ASC
        """
        trend_df = conn.execute(trend_sql).fetchdf()

        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=trend_df["month"],
                y=trend_df["monthly_volume"],
                mode="lines+markers",
                line=dict(color="#264653", width=2.5),
                marker=dict(size=4),
                name="Monthly Purchase Volume",
                hovertemplate="Month: %{x|%Y-%m}<br>Volume: %{y:,}<extra></extra>",
            )
        )
        fig = apply_chart_style(
            fig,
            title="Portfolio Purchase Volume Trajectory (Monthly)",
            x_title="Observation Month",
            y_title="Purchase Lines",
            height=450,
            show_legend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # 3. Category Momentum Highlights
    st.markdown("### ⚡ Category Demand Momentum Leaders")
    growth_df = ci.get_category_growth(level="department")
    top_accel = growth_df[growth_df["momentum_signal"] == "Accelerating Demand"].head(5)

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

    st.info(
        "💡 **Data Limitation Notice:** Transaction values represent normalised purchase-price indices, not actual monetary revenues. "
        "Inventory levels and stockout records are absent from the source dataset, so volume growth reflects observed consumer demand pull rather than supply availability."
    )
