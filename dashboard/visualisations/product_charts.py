"""
GarmentPulse Dashboard — Product Visualisations
Plotly charts for article lifecycle distribution and SKU purchase histories.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.components.charts import apply_chart_style


def plot_product_classification_bar(df: pd.DataFrame) -> go.Figure:
    """Bar chart showing count of articles in each lifecycle stage."""
    color_map = {
        "Emerging": "#2a9d8f",
        "Accelerating": "#264653",
        "Stable": "#457b9d",
        "Slowing": "#e76f51",
        "Low Activity": "#6c757d",
    }
    colors = [color_map.get(s, "#457b9d") for s in df["lifecycle_status"]]

    fig = go.Figure(
        go.Bar(
            x=df["lifecycle_status"],
            y=df["article_count"],
            marker_color=colors,
            text=df["share_pct"].apply(lambda p: f"{p}%"),
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Articles: %{y:,}<br>Share: %{text}<extra></extra>",
        )
    )
    return apply_chart_style(
        fig,
        title="Catalogue Lifecycle Stage Distribution",
        x_title="Lifecycle Classification",
        y_title="Article SKU Count",
        height=380,
        show_legend=False,
    )


def plot_article_trend_line(df: pd.DataFrame, prod_name: str) -> go.Figure:
    """Time series for an individual article."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["week_date"],
            y=df["purchase_volume"],
            mode="lines+markers",
            line=dict(color="#1a1a2e", width=2),
            marker=dict(size=4),
            name="Weekly Volume",
            hovertemplate="Week: %{x|%Y-%m-%d}<br>Volume: %{y:,}<extra></extra>",
        )
    )
    return apply_chart_style(
        fig,
        title=f"Observed Weekly Purchase Velocity: {prod_name}",
        x_title="Week",
        y_title="Purchase Volume (Lines)",
        height=360,
        show_legend=False,
    )
