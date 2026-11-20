"""
GarmentPulse Dashboard — Category Visualisations
Plotly charts for category rankings, growth distributions, and HHI concentration.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.components.charts import apply_chart_style, CHART_THEME


def plot_category_ranking_bar(df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    """Horizontal bar chart ranking categories by volume."""
    sub = df.head(top_n).iloc[::-1]
    fig = go.Figure(
        go.Bar(
            x=sub["purchase_volume"],
            y=sub["category_name"],
            orientation="h",
            marker=dict(
                color=sub["purchase_volume"],
                colorscale="Blues",
                showscale=False,
            ),
            text=sub["purchase_volume"].apply(lambda v: f"{v:,}"),
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Volume: %{x:,}<br>Share: %{customdata[0]}%<br>Avg Price Index: %{customdata[1]:.4f}<extra></extra>",
            customdata=sub[["volume_share_pct", "avg_normalised_price"]].values,
        )
    )
    return apply_chart_style(
        fig,
        title=f"Top {top_n} Categories by Observed Purchase Volume",
        x_title="Purchase Volume (Lines)",
        y_title="",
        height=450,
        show_legend=False,
    )


def plot_category_growth_scatter(df: pd.DataFrame, top_n: int = 25) -> go.Figure:
    """Scatter plot: Volume vs Growth Rate with bubble size = unique customers."""
    sub = df.dropna(subset=["volume_growth_pct"]).head(top_n)

    fig = px.scatter(
        sub,
        x="prev_volume",
        y="volume_growth_pct",
        size="recent_customers",
        color="momentum_signal",
        hover_name="category_name",
        hover_data={"prev_volume": ":,", "recent_volume": ":,", "volume_growth_pct": ":.1f%"},
        color_discrete_map={
            "Accelerating Demand": "#2a9d8f",
            "Stable Velocity": "#457b9d",
            "Declining Demand": "#e76f51",
        },
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#adb5bd")
    return apply_chart_style(
        fig,
        title="Category Momentum Matrix: Base Volume vs Recent Growth (%)",
        x_title="Previous 4-Week Volume (Lines)",
        y_title="Recent Volume Growth (%)",
        height=450,
    )


def plot_category_treemap(df: pd.DataFrame, top_n: int = 30) -> go.Figure:
    """Treemap showing relative volume share and concentration."""
    sub = df.head(top_n)
    fig = px.treemap(
        sub,
        path=["concentration_tier", "category_name"],
        values="purchase_volume",
        color="avg_normalised_price",
        color_continuous_scale="Viridis",
    )
    return apply_chart_style(
        fig,
        title="Category Hierarchy & Assortment Breadth Treemap",
        height=450,
        show_legend=False,
    )
