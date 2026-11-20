"""
GarmentPulse Dashboard — Page 5: Product Lifecycle Intelligence (Module D)
Article-level performance, velocities, lifecycle classifications, and SKU drilldowns.
NOTE: First observed purchase != launch date. Last observed != discontinuation.
"""

import duckdb
import streamlit as st
import pandas as pd

from dashboard.visualisations.product_charts import (
    plot_product_classification_bar,
    plot_article_trend_line,
)
from src.analytics.product_intelligence import ProductIntelligence


def render(conn: duckdb.DuckDBPyConnection) -> None:
    st.markdown("## 👗 Product Lifecycle & Article Velocity Intelligence")
    st.markdown(
        "Evaluate individual SKU performance, demand growth rates, active lifespans, and lifecycle transition stages."
    )

    pi = ProductIntelligence(conn)

    # 1. Lifecycle Classification Distribution
    col1, col2 = st.columns([5, 7])
    class_df = pi.get_product_classifications()

    with col1:
        st.plotly_chart(plot_product_classification_bar(class_df), use_container_width=True)

    with col2:
        st.markdown("### 🏷️ Article Classification Definitions")
        st.markdown("""
        - **🚀 Emerging:** First observed purchase within recent 8 weeks with volume >= 5 units.
        - **⚡ Accelerating:** Recent 4-wk volume grew > 20% vs prior 4 weeks (min 5 units).
        - **📊 Stable:** Velocity within ±20% growth band.
        - **📉 Slowing:** Recent 4-wk volume contracted > 20% vs prior window.
        - **💤 Low Activity:** Fewer than 5 total observed purchases across catalogue history.
        """)
        st.warning(
            "⚠️ **Analytical Proxy Disclaimer:** 'First observed purchase' is not guaranteed to be the factory launch date. "
            "'Last observed purchase' is not verified product discontinuation. These represent transaction-observation proxies."
        )

    st.markdown("---")

    # 2. Article Catalog Table with Search & Filtering
    st.markdown("### 🔍 Article Performance Explorer")
    f1, f2, f3, f4 = st.columns([3, 3, 3, 3])
    with f1:
        search_kw = st.text_input("Search Article Name or SKU ID", value="")
    with f2:
        stage_filter = st.selectbox(
            "Lifecycle Filter",
            options=["All", "Accelerating", "Emerging", "Stable", "Slowing", "Low Activity"],
            index=0,
        )
    with f3:
        sort_opt = st.selectbox(
            "Sort Order",
            options=["purchase_volume", "recent_volume", "growth_rate", "unique_customers"],
            format_func=lambda x: {
                "purchase_volume": "Total Volume (High → Low)",
                "recent_volume": "Recent 4-Wk Volume",
                "growth_rate": "Growth Rate (%)",
                "unique_customers": "Unique Customers",
            }.get(x, x),
            index=0,
        )
    with f4:
        limit_n = st.selectbox("Display Rows", options=[25, 50, 100], index=0)

    articles_df = pi.get_product_performance(
        limit=limit_n,
        search=search_kw if search_kw else None,
        lifecycle_filter=stage_filter,
        sort_by=sort_opt,
    )

    if not articles_df.empty:
        st.dataframe(
            articles_df[[
                "article_id", "prod_name", "product_type_name", "department_name",
                "colour_group_name", "total_purchase_lines", "recent_4wk_volume",
                "prev_4wk_volume", "volume_growth_rate", "active_weeks", "lifecycle_status"
            ]].rename(columns={
                "article_id": "Article ID",
                "prod_name": "Product Name",
                "product_type_name": "Product Type",
                "department_name": "Department",
                "colour_group_name": "Colour",
                "total_purchase_lines": "Total Lines",
                "recent_4wk_volume": "Recent 4W Vol",
                "prev_4wk_volume": "Prev 4W Vol",
                "volume_growth_rate": "Growth Rate",
                "active_weeks": "Active Wks",
                "lifecycle_status": "Lifecycle Stage",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # SKU Drilldown
        st.markdown("### 🔎 Individual SKU Velocity Drilldown")
        selected_sku = st.selectbox(
            "Select Article from Table for Weekly Trajectory",
            options=articles_df["article_id"].tolist(),
            format_func=lambda x: f"{x} — {articles_df[articles_df['article_id'] == x]['prod_name'].values[0]}",
        )
        if selected_sku:
            prod_name = articles_df[articles_df["article_id"] == selected_sku]["prod_name"].values[0]
            trend_df = pi.get_product_trends(selected_sku)
            if not trend_df.empty:
                st.plotly_chart(plot_article_trend_line(trend_df, prod_name), use_container_width=True)
    else:
        st.info("No articles match the current filter criteria.")
