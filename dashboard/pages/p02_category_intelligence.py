"""
GarmentPulse Dashboard — Page 2: Category Intelligence (Module A)
Deep-dive performance, momentum, concentration, and YoY analytics across category hierarchies.
"""

import duckdb
import streamlit as st
import pandas as pd

from dashboard.visualisations.category_charts import (
    plot_category_ranking_bar,
    plot_category_growth_scatter,
    plot_category_treemap,
)
from src.analytics.category_intelligence import CategoryIntelligence


def render(conn: duckdb.DuckDBPyConnection) -> None:
    st.markdown("## 🏷️ Category Performance & Momentum Intelligence")
    st.markdown(
        "Analyze demand distribution, growth velocity, and concentration across departments, sections, and garment groups."
    )

    ci = CategoryIntelligence(conn)

    # Level selector controls
    c1, c2, c3 = st.columns([4, 4, 4])
    with c1:
        level_choice = st.selectbox(
            "Taxonomy Level",
            options=["Department", "Section", "Product Group", "Garment Group", "Product Type"],
            index=0,
        )
    with c2:
        min_vol = st.number_input(
            "Minimum Transaction Filter",
            min_value=50,
            max_value=10000,
            value=200,
            step=50,
            help="Filters out minor low-volume categories to prevent misleading growth spikes.",
        )
    with c3:
        view_mode = st.radio("Analytics Lens", options=["Volume & Concentration", "Growth Momentum", "YoY Comparison"], horizontal=True)

    level_key = level_choice.lower().replace(" ", "_")

    if view_mode == "Volume & Concentration":
        perf_df = ci.get_category_performance(level=level_key, min_transactions=min_vol)

        st.plotly_chart(plot_category_ranking_bar(perf_df, top_n=15), use_container_width=True)

        colA, colB = st.columns([6, 6])
        with colA:
            st.plotly_chart(plot_category_treemap(perf_df, top_n=25), use_container_width=True)
        with colB:
            st.markdown("### 📊 Category Assortment Performance Table")
            st.dataframe(
                perf_df[[
                    "category_name", "purchase_volume", "unique_customers",
                    "active_articles", "volume_share_pct", "avg_normalised_price", "hhi_concentration"
                ]].rename(columns={
                    "category_name": level_choice,
                    "purchase_volume": "Purchase Volume",
                    "unique_customers": "Unique Customers",
                    "active_articles": "Active SKUs",
                    "volume_share_pct": "Volume Share (%)",
                    "avg_normalised_price": "Avg Price Index",
                    "hhi_concentration": "HHI Concentration",
                }),
                use_container_width=True,
                hide_index=True,
            )

    elif view_mode == "Growth Momentum":
        growth_df = ci.get_category_growth(level=level_key, min_transactions=min_vol)

        st.plotly_chart(plot_category_growth_scatter(growth_df, top_n=30), use_container_width=True)

        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### 🚀 Top Growing Categories (Recent 4 Wks)")
            st.dataframe(
                growth_df.dropna(subset=["volume_growth_pct"]).head(10)[[
                    "category_name", "recent_volume", "prev_volume", "volume_growth_pct", "momentum_signal"
                ]].rename(columns={
                    "category_name": level_choice,
                    "recent_volume": "Recent Volume",
                    "prev_volume": "Previous Volume",
                    "volume_growth_pct": "Growth (%)",
                    "momentum_signal": "Signal",
                }),
                use_container_width=True,
                hide_index=True,
            )
        with c_right:
            st.markdown("#### 📉 Categories Showing Deceleration")
            st.dataframe(
                growth_df.dropna(subset=["volume_growth_pct"]).tail(10).iloc[::-1][[
                    "category_name", "recent_volume", "prev_volume", "volume_growth_pct", "momentum_signal"
                ]].rename(columns={
                    "category_name": level_choice,
                    "recent_volume": "Recent Volume",
                    "prev_volume": "Previous Volume",
                    "volume_growth_pct": "Growth (%)",
                    "momentum_signal": "Signal",
                }),
                use_container_width=True,
                hide_index=True,
            )

    else:
        st.markdown("### 📅 Year-over-Year Comparative Analysis (2019 vs 2018)")
        yoy_df = ci.get_yoy_comparison(level=level_key)
        st.dataframe(
            yoy_df.rename(columns={
                "category_name": level_choice,
                "calendar_month": "Month (1-12)",
                "volume_2018": "2018 Volume",
                "volume_2019": "2019 Volume",
                "volume_2020": "2020 Volume",
                "yoy_growth_2019_vs_2018_pct": "YoY Growth 2019 vs 2018 (%)",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.caption("Threshold rule: Categories with fewer than {min_vol} transactions are excluded to safeguard metric validity.")
