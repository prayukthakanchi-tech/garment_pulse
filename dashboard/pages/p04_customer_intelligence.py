"""
GarmentPulse Dashboard — Page 4: Customer Intelligence (Module C)
RFM segmentation, repeat purchase distribution, and monthly cohort retention matrices.
"""

from typing import Optional
import duckdb
import streamlit as st
import pandas as pd

from dashboard.components.metrics import render_kpi_row
from dashboard.visualisations.customer_charts import (
    plot_segment_donut,
    plot_cohort_heatmap,
    plot_new_vs_returning_area,
)
from dashboard.data_service import (
    get_customer_overview_cached,
    get_customer_segments_cached,
    get_cohort_retention_matrix_cached,
    get_cohort_summary_cached,
    get_customer_activity_trends_cached,
    get_repeat_purchase_distribution_cached,
)


def render(conn: Optional[duckdb.DuckDBPyConnection] = None) -> None:
    st.markdown("## Customer Lifecycle & Cohort Intelligence")
    st.markdown(
        "Evaluate measurable customer segmentation tiers, repeat purchase activity, and historical monthly cohort progression."
    )

    # 1. Customer Overview KPI Row
    with st.spinner("Loading customer metrics..."):
        overview = get_customer_overview_cached()

    render_kpi_row([
        {
            "label": "Total Purchasing Base",
            "value": f"{overview['total_purchasing_customers']:,}",
            "help": "Distinct customer entities with at least 1 historical purchase.",
        },
        {
            "label": "Active Customers (30D)",
            "value": f"{overview['active_30d']:,}",
            "help": "Customers with purchases in the most recent 30-day window.",
        },
        {
            "label": "Active Customers (90D)",
            "value": f"{overview['active_90d']:,}",
            "help": "Customers active within the last 90 days.",
        },
        {
            "label": "Repeat Customer Ratio",
            "value": f"{overview['repeat_customer_rate_pct']}%",
            "help": "Percentage of customers who made purchases on 2 or more distinct calendar dates.",
        },
    ])

    st.markdown("---")

    t1, t2, t3 = st.tabs(["Lifecycle Segmentation", "Cohort Repeat Matrix", "Repeat Purchase Dynamics"])

    with t1:
        seg_df = get_customer_segments_cached()
        col1, col2 = st.columns([5, 7])

        with col1:
            st.plotly_chart(plot_segment_donut(seg_df), use_container_width=True)

        with col2:
            st.markdown("### Segment Characteristic Profiles")
            st.dataframe(
                seg_df.rename(columns={
                    "segment": "Segment Tier",
                    "customer_count": "Customers",
                    "segment_share_pct": "Share (%)",
                    "avg_recency_days": "Avg Recency (Days)",
                    "avg_purchase_days": "Avg Purchase Days",
                    "avg_purchase_lines": "Avg Lines",
                    "avg_price_contribution": "Avg Price Contrib.",
                }),
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "Segmentation Rules: Frequent Buyers (10+ days & <=30d recency), Emerging (first seen <=90d & 2+ trips), "
            "Recently Active (<=30d), Cooling (31-90d), At-Risk (91-180d), Dormant (>180d)."
        )

    with t2:
        st.markdown("### Monthly Cohort Retention & Repeat Activity Heatmap")
        st.markdown(
            "*Note: This measures repeat purchase transaction activity across successive calendar months. "
            "Because website visit sessions are not tracked, this does NOT measure platform browsing retention.*"
        )
        cohort_matrix = get_cohort_retention_matrix_cached(max_period=12)
        st.plotly_chart(plot_cohort_heatmap(cohort_matrix), use_container_width=True)

        with st.expander("View Tabular Cohort Summary Table"):
            st.dataframe(get_cohort_summary_cached(), use_container_width=True, hide_index=True)

    with t3:
        colA, colB = st.columns([6, 6])
        with colA:
            st.markdown("### Customer Composition: New vs Returning")
            trends_df = get_customer_activity_trends_cached(freq="month")
            st.plotly_chart(plot_new_vs_returning_area(trends_df), use_container_width=True)

        with colB:
            st.markdown("### Purchase Frequency Tier Breakdown")
            freq_df = get_repeat_purchase_distribution_cached()
            st.dataframe(
                freq_df.rename(columns={
                    "frequency_tier": "Purchase Frequency Tier",
                    "customer_count": "Customer Count",
                    "share_pct": "Customer Share (%)",
                }),
                use_container_width=True,
                hide_index=True,
            )
