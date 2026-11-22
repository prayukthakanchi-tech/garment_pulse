"""
GarmentPulse Dashboard — Page 6: Sales Channel Analytics (Module E)
Objective comparison of Channel 1 and Channel 2 without unverified channel labels.
"""

from typing import Optional
import duckdb
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.components.metrics import render_kpi_row
from dashboard.components.charts import apply_chart_style, CHART_THEME
from dashboard.data_service import (
    get_channel_overview_cached,
    get_channel_trends_cached,
    get_channel_customer_overlap_cached,
    get_channel_department_contribution_cached,
)
from dashboard.components.headers import render_page_header
from dashboard.components.containers import render_card_header


def render(conn: Optional[duckdb.DuckDBPyConnection] = None) -> None:
    render_page_header(
        title="Sales Channel Dynamics & Distribution",
        subtitle="Evaluate purchasing behaviors, customer penetration, and department preferences across Channel 1 and Channel 2.",
        breadcrumb="OMNICHANNEL INTELLIGENCE",
        badges=[
            ("Channel 1 vs Channel 2", "blue"),
            ("Cross-Channel Penetration", "violet"),
            ("Price Index Spread", "amber"),
        ],
    )

    # 1. Macro Channel Metrics
    with st.spinner("Loading sales channel statistics..."):
        ch_df = get_channel_overview_cached()

    c1_row = ch_df[ch_df["sales_channel_id"] == 1].iloc[0]
    c2_row = ch_df[ch_df["sales_channel_id"] == 2].iloc[0]

    render_kpi_row([
        {
            "label": "Channel 1 Total Volume",
            "value": f"{c1_row['purchase_volume']:,}",
            "delta": f"{c1_row['volume_share_pct']}% of total",
            "badge": "CHANNEL 1",
            "caption": "Physical store / channel 1",
            "help": "Observed lines attributed to Channel 1.",
        },
        {
            "label": "Channel 2 Total Volume",
            "value": f"{c2_row['purchase_volume']:,}",
            "delta": f"{c2_row['volume_share_pct']}% of total",
            "badge": "CHANNEL 2",
            "caption": "Online digital / channel 2",
            "help": "Observed lines attributed to Channel 2.",
        },
        {
            "label": "Channel 1 Mean Price Index",
            "value": f"{c1_row['avg_normalised_price']:.4f}",
            "badge": "INDEX",
            "caption": "Dimensionless average ratio",
            "help": "Dimensionless average normalized purchase price in Channel 1.",
        },
        {
            "label": "Channel 2 Mean Price Index",
            "value": f"{c2_row['avg_normalised_price']:.4f}",
            "badge": "INDEX",
            "caption": "Dimensionless average ratio",
            "help": "Dimensionless average normalized purchase price in Channel 2.",
        },
    ])

    st.markdown("---")

    colA, colB = st.columns([6, 6])

    with colA:
        st.markdown("### Monthly Volume Trends by Sales Channel")
        trends_df = get_channel_trends_cached(freq="month")
        fig_t = px.line(
            trends_df,
            x="period_date",
            y="purchase_volume",
            color="channel_label",
            markers=True,
            color_discrete_map={"Channel 1": "#1E3A8A", "Channel 2": "#0D9488"},
        )
        fig_t = apply_chart_style(
            fig_t,
            title="Monthly Channel Purchase Volume Trajectory",
            x_title="Observation Month",
            y_title="Purchase Lines",
            height=400,
        )
        st.plotly_chart(fig_t, use_container_width=True)

    with colB:
        st.markdown("### Cross-Channel Customer Overlap")
        overlap = get_channel_customer_overlap_cached()

        overlap_fig = go.Figure(
            go.Pie(
                labels=["Channel 1 Exclusively", "Channel 2 Exclusively", "Both Channels (Omnichannel)"],
                values=[overlap["channel_1_only"], overlap["channel_2_only"], overlap["both_channels"]],
                hole=0.55,
                marker=dict(colors=["#1E3A8A", "#0D9488", "#2563EB"]),
                textinfo="label+percent",
            )
        )
        overlap_fig = apply_chart_style(
            overlap_fig,
            title="Customer Channel Penetration & Overlap",
            height=400,
            show_legend=False,
        )
        st.plotly_chart(overlap_fig, use_container_width=True)

    # Department level contribution
    st.markdown("### Top Department Distribution by Channel")
    dept_contrib = get_channel_department_contribution_cached(top_n=12)

    fig_d = px.bar(
        dept_contrib,
        x="department_name",
        y="channel_volume",
        color="channel_label",
        barmode="group",
        color_discrete_map={"Channel 1": "#1E3A8A", "Channel 2": "#0D9488"},
        title="Department Volume Comparison Across Channels",
    )
    fig_d = apply_chart_style(
        fig_d,
        x_title="Department",
        y_title="Purchase Lines",
        height=450,
    )
    st.plotly_chart(fig_d, use_container_width=True)

    st.info(
        "**Data Governance Note:** The Kaggle dataset metadata documents only numeric codes (1 and 2) without specifying which represents physical stores vs online e-commerce. "
        "To uphold integrity, they are analyzed objectively without assuming either channel is digital or brick-and-mortar."
    )
