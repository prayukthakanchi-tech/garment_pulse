"""
GarmentPulse Dashboard — Customer Visualisations
Plotly charts for RFM segments, cohort retention heatmaps, and repeat activity trends.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard.components.charts import apply_chart_style, CHART_THEME


def plot_segment_donut(df: pd.DataFrame) -> go.Figure:
    """Donut chart showing customer distribution across lifecycle segments."""
    colors = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#6c757d"]
    fig = go.Figure(
        go.Pie(
            labels=df["segment"],
            values=df["customer_count"],
            hole=0.55,
            marker=dict(colors=colors),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>Share: %{percent}<extra></extra>",
        )
    )
    return apply_chart_style(
        fig,
        title="Customer Lifecycle Segmentation Distribution",
        height=400,
        show_legend=False,
    )


def plot_cohort_heatmap(pivot_df: pd.DataFrame) -> go.Figure:
    """Heatmap with explicit repeat purchasing percentage annotations."""
    if pivot_df.empty:
        return go.Figure()

    # Create formatted text matrix (compatible across pandas < 2.1 and pandas >= 2.1/2.2)
    format_fn = lambda v: f"{v:.1f}%" if pd.notnull(v) else ""
    if hasattr(pivot_df, "map"):
        text_matrix = pivot_df.map(format_fn)
    else:
        text_matrix = pivot_df.applymap(format_fn)

    fig = go.Figure(
        go.Heatmap(
            z=pivot_df.values,
            x=list(pivot_df.columns),
            y=list(pivot_df.index),
            colorscale="Purples",
            zmin=0,
            zmax=pivot_df.iloc[:, 1:].max().max() if pivot_df.shape[1] > 1 else 100,
            text=text_matrix.values,
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate="Cohort: %{y}<br>Period: %{x}<br>Repeat Activity: %{z:.2f}%<extra></extra>",
        )
    )
    return apply_chart_style(
        fig,
        title="Monthly Cohort Repeat Purchasing Activity Matrix (%)",
        x_title="Months Since First Observed Purchase (M+N)",
        y_title="Acquisition Cohort Month",
        height=520,
        show_legend=False,
    )


def plot_new_vs_returning_area(df: pd.DataFrame) -> go.Figure:
    """Stacked area chart of new vs returning customers over time."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["period_date"],
            y=df["new_customers"],
            name="New Customers",
            mode="lines",
            stackgroup="one",
            line=dict(width=0.5, color="#2a9d8f"),
            fillcolor="rgba(42, 157, 143, 0.7)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["period_date"],
            y=df["returning_customers"],
            name="Returning Customers",
            mode="lines",
            stackgroup="one",
            line=dict(width=0.5, color="#264653"),
            fillcolor="rgba(38, 70, 83, 0.85)",
        )
    )
    return apply_chart_style(
        fig,
        title="Monthly Active Customer Composition: New vs Returning",
        x_title="Month",
        y_title="Active Purchasing Customers",
        height=400,
    )
