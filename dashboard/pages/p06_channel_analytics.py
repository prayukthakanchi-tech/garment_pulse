"""
GarmentPulse Dashboard — Page 6: Sales Channel Analytics (Module E)
Objective comparison of Channel 1 and Channel 2 without unverified channel labels.
"""

import duckdb
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.components.metrics import render_kpi_row
from dashboard.components.charts import apply_chart_style
from src.analytics.channel_intelligence import ChannelIntelligence


def render(conn: duckdb.DuckDBPyConnection) -> None:
    st.markdown("## 📡 Sales Channel Distribution Intelligence")
    st.markdown(
        "Evaluate purchasing behaviors, basket sizes, and category preferences across Sales Channel 1 and Sales Channel 2."
    )

    chi = ChannelIntelligence(conn)

    # 1. Macro Channel Metrics
    ch_df = chi.get_channel_overview()
    c1_row = ch_df[ch_df["sales_channel_id"] == 1].iloc[0]
    c2_row = ch_df[ch_df["sales_channel_id"] == 2].iloc[0]

    render_kpi_row([
        {
            "label": "Channel 1 Total Volume",
            "value": f"{c1_row['purchase_volume']:,}",
            "delta": f"{c1_row['volume_share_pct']}% of total",
            "help": "Observed lines attributed to Channel 1.",
        },
        {
            "label": "Channel 2 Total Volume",
            "value": f"{c2_row['purchase_volume']:,}",
            "delta": f"{c2_row['volume_share_pct']}% of total",
            "help": "Observed lines attributed to Channel 2.",
        },
        {
            "label": "Channel 1 Mean Price Index",
            "value": f"{c1_row['avg_normalised_price']:.4f}",
            "help": "Dimensionless average normalized purchase price in Channel 1.",
        },
        {
            "label": "Channel 2 Mean Price Index",
            "value": f"{c2_row['avg_normalised_price']:.4f}",
            "help": "Dimensionless average normalized purchase price in Channel 2.",
        },
    ])

    st.markdown("---")

    colA, colB = st.columns([6, 6])

    with colA:
        st.markdown("### 📈 Monthly Volume Trends by Sales Channel")
        trends_df = chi.get_channel_trends(freq="month")
        fig_t = px.line(
            trends_df,
            x="period_date",
            y="purchase_volume",
            color="channel_label",
            markers=True,
            color_discrete_map={"Channel 1": "#457b9d", "Channel 2": "#264653"},
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
        st.markdown("### 👥 Cross-Channel Customer Overlap")
        overlap = chi.get_channel_customer_overlap()

        overlap_fig = go.Figure(
            go.Pie(
                labels=["Channel 1 Exclusively", "Channel 2 Exclusively", "Both Channels (Omnichannel)"],
                values=[overlap["channel_1_only"], overlap["channel_2_only"], overlap["both_channels"]],
                hole=0.5,
                marker=dict(colors=["#457b9d", "#264653", "#2a9d8f"]),
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
    st.markdown("### 🏷️ Department Contribution per Sales Channel")
    dept_ch_df = chi.get_channel_department_contribution(top_n=12)

    fig_dept = px.bar(
        dept_ch_df,
        x="department_name",
        y="dept_share_within_channel_pct",
        color="channel_label",
        barmode="group",
        color_discrete_map={"Channel 1": "#457b9d", "Channel 2": "#264653"},
    )
    fig_dept = apply_chart_style(
        fig_dept,
        title="Top 12 Departments: Category Mix Share within Each Channel (%)",
        x_title="Department",
        y_title="Share within Channel (%)",
        height=450,
    )
    st.plotly_chart(fig_dept, use_container_width=True)

    st.info(
        "💡 **Data Integrity Mandate:** As per Project Omega specifications, sales channels are neutrally reported as Channel 1 and Channel 2. "
        "Neither channel is arbitrarily labeled as 'online' or 'store' without official authoritative mapping documentation."
    )
