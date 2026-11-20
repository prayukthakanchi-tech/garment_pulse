"""
GarmentPulse Dashboard — Page 3: Fashion Attribute Intelligence (Module B)
Analyzes design attributes including colours, graphical appearances, and garment groupings.
"""

import duckdb
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.components.charts import apply_chart_style
from src.analytics.attribute_intelligence import AttributeIntelligence


def render(conn: duckdb.DuckDBPyConnection) -> None:
    st.markdown("## 🎨 Fashion Attribute & Design Intelligence")
    st.markdown(
        "Investigate how physical garment attributes (colour palette, garment type, graphical patterns) influence consumer purchasing patterns."
    )

    ai = AttributeIntelligence(conn)

    t1, t2, t3 = st.tabs(["🌈 Colour Palette Performance", "👗 Garment Group Velocity", "🧩 Cross-Attribute Heatmap"])

    with t1:
        colA, colB = st.columns([6, 6])
        colour_df = ai.get_colour_performance(min_transactions=1000)

        with colA:
            top_colours = colour_df.head(12)
            fig = px.bar(
                top_colours,
                x="colour_group_name",
                y="purchase_volume",
                color="colour_group_name",
                title="Top 12 Fashion Colour Groups by Purchase Volume",
            )
            fig = apply_chart_style(fig, x_title="Colour Group", y_title="Purchase Volume", height=420, show_legend=False)
            st.plotly_chart(fig, use_container_width=True)

        with colB:
            st.markdown("### 📋 Colour Palette Demand Metrics")
            st.dataframe(
                colour_df.head(15)[[
                    "colour_group_name", "purchase_volume", "unique_customers",
                    "active_articles", "volume_share_pct", "avg_normalised_price"
                ]].rename(columns={
                    "colour_group_name": "Colour Group",
                    "purchase_volume": "Volume",
                    "unique_customers": "Customers",
                    "active_articles": "Active SKUs",
                    "volume_share_pct": "Volume Share (%)",
                    "avg_normalised_price": "Avg Price Index",
                }),
                use_container_width=True,
                hide_index=True,
            )

    with t2:
        st.markdown("### 📈 Garment Group Demand Over Time")
        trend_df = ai.get_garment_group_trends(freq="month")
        # Keep top 8 garment groups
        top_garments = trend_df.groupby("garment_group_name")["purchase_volume"].sum().nlargest(8).index
        filtered_trends = trend_df[trend_df["garment_group_name"].isin(top_garments)]

        fig_g = px.line(
            filtered_trends,
            x="period_date",
            y="purchase_volume",
            color="garment_group_name",
            markers=True,
        )
        fig_g = apply_chart_style(
            fig_g,
            title="Monthly Trajectory of Top Garment Groups",
            x_title="Observation Month",
            y_title="Purchase Volume (Lines)",
            height=450,
        )
        st.plotly_chart(fig_g, use_container_width=True)

        # Attribute growth ranking
        st.markdown("#### ⚡ Fastest Growing Colours (Recent 4 Wks)")
        growth_colours = ai.get_attribute_growth_rankings(attribute="colour_group_name", min_volume=1000)
        st.dataframe(
            growth_colours.head(10).rename(columns={
                "attribute_value": "Colour",
                "recent_vol": "Recent Volume",
                "prev_vol": "Previous Volume",
                "growth_pct": "Growth Rate (%)",
            }),
            use_container_width=True,
            hide_index=True,
        )

    with t3:
        st.markdown("### 🗺️ Department vs Colour Group Cross-Tabulation")
        heat_df = ai.get_department_attribute_heatmap(attribute="colour_group_name", top_depts=10, top_attrs=10)

        if not heat_df.empty:
            pivot_heat = heat_df.pivot(index="department_name", columns="attribute_value", values="purchase_volume").fillna(0)
            fig_h = go.Figure(
                go.Heatmap(
                    z=pivot_heat.values,
                    x=list(pivot_heat.columns),
                    y=list(pivot_heat.index),
                    colorscale="Blues",
                    hovertemplate="Dept: %{y}<br>Colour: %{x}<br>Volume: %{z:,}<extra></extra>",
                )
            )
            fig_h = apply_chart_style(
                fig_h,
                title="Cross-Tabulation: Top Departments × Top Colours (Purchase Volume)",
                x_title="Colour Group",
                y_title="Department",
                height=500,
                show_legend=False,
            )
            st.plotly_chart(fig_h, use_container_width=True)

        st.markdown("#### 🔗 Common Colour & Garment Group Pairings")
        comb_df = ai.get_colour_garment_combinations(top_n=15)
        st.dataframe(
            comb_df.rename(columns={
                "colour_group_name": "Colour Group",
                "garment_group_name": "Garment Group",
                "purchase_volume": "Purchase Volume",
                "unique_customers": "Customers",
                "avg_price_index": "Avg Price Index",
            }),
            use_container_width=True,
            hide_index=True,
        )
