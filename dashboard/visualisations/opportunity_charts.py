"""
GarmentPulse Dashboard — Opportunity Visualisations
Radar / polar spider charts and opportunity ranking visualisations.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.components.charts import apply_chart_style


def plot_opportunity_radar(df: pd.DataFrame, top_n: int = 4) -> go.Figure:
    """Radar chart comparing opportunity dimensions across top scoring categories."""
    categories_sub = df.head(top_n)
    dimensions = [
        "Volume Growth",
        "Customer Growth",
        "Repeat Buyer Ratio",
        "Category Contribution",
        "Assortment Diversity",
        "Demand Momentum",
    ]

    fig = go.Figure()
    palette = ["#264653", "#2a9d8f", "#e76f51", "#f4a261"]

    for i, (_, row) in enumerate(categories_sub.iterrows()):
        vals = [
            row["s_vol_growth"] * 100,
            row["s_cust_growth"] * 100,
            row["s_repeat"] * 100,
            row["s_contrib"] * 100,
            row["s_concentration"] * 100,
            row["s_momentum"] * 100,
        ]
        # Close the loop
        vals_loop = vals + [vals[0]]
        dims_loop = dimensions + [dimensions[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=vals_loop,
                theta=dims_loop,
                fill="toself",
                name=f"{row['category_name']} ({row['opportunity_score']:.1f})",
                line=dict(color=palette[i % len(palette)], width=2),
                opacity=0.6,
            )
        )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False),
            bgcolor="#ffffff",
        ),
        showlegend=True,
        height=480,
    )
    return apply_chart_style(
        fig,
        title="Category Opportunity Radar: Comparative Multi-Factor Scores",
        height=480,
    )


def plot_opportunity_ranking_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal ranking of categories colored by opportunity tier."""
    sub = df.head(top_n).iloc[::-1]

    color_map = {
        "Strong Demand Signal": "#2a9d8f",
        "Emerging Opportunity": "#457b9d",
        "Stable Performer": "#e9c46a",
        "Declining Demand Signal": "#e76f51",
        "Insufficient Evidence": "#6c757d",
    }
    colors = [color_map.get(s, "#457b9d") for s in sub["classification"]]

    fig = go.Figure(
        go.Bar(
            x=sub["opportunity_score"],
            y=sub["category_name"],
            orientation="h",
            marker_color=colors,
            text=sub["opportunity_score"].apply(lambda s: f"{s:.1f}"),
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}/100<br>Status: %{customdata}<extra></extra>",
            customdata=sub["classification"],
        )
    )
    return apply_chart_style(
        fig,
        title="Relative Commercial Opportunity Index (Top Categories)",
        x_title="Composite Opportunity Score (0 - 100)",
        y_title="",
        height=480,
        show_legend=False,
    )
