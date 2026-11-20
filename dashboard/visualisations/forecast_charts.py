"""
GarmentPulse Dashboard — Forecasting Visualisations
Plotly charts for category demand projections, uncertainty bands, and backtest comparisons.
"""

import plotly.graph_objects as go
import pandas as pd

from dashboard.components.charts import apply_chart_style


def plot_demand_forecast(res: dict) -> go.Figure:
    """Historical weekly demand plus projected forward trajectory with uncertainty bounds."""
    fig = go.Figure()

    # 1. Historical Actuals (Solid line)
    fig.add_trace(
        go.Scatter(
            x=res["historical_dates"],
            y=res["historical_volumes"],
            mode="lines+markers",
            name="Historical Volume",
            line=dict(color="#1a1a2e", width=2.5),
            marker=dict(size=4),
            hovertemplate="Week: %{x}<br>Actual Volume: %{y:,}<extra></extra>",
        )
    )

    # 2. Uncertainty Confidence Interval (Shaded band)
    if "upper_bound" in res and "lower_bound" in res:
        fig.add_trace(
            go.Scatter(
                x=res["future_dates"] + res["future_dates"][::-1],
                y=res["upper_bound"] + res["lower_bound"][::-1],
                fill="toself",
                fillcolor="rgba(42, 157, 143, 0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=True,
                name="95% Prediction Interval",
            )
        )

    # 3. Forecast Projections (Dashed lines)
    if "forecast_hw" in res:
        fig.add_trace(
            go.Scatter(
                x=res["future_dates"],
                y=res["forecast_hw"],
                mode="lines+markers",
                name="Holt-Winters Projection",
                line=dict(color="#2a9d8f", width=2.5, dash="dash"),
                marker=dict(size=5),
                hovertemplate="Week: %{x}<br>HW Projected: %{y:,}<extra></extra>",
            )
        )

    if "forecast_lgb" in res:
        fig.add_trace(
            go.Scatter(
                x=res["future_dates"],
                y=res["forecast_lgb"],
                mode="lines+markers",
                name="LightGBM Projection",
                line=dict(color="#e76f51", width=2, dash="dot"),
                marker=dict(size=4),
                hovertemplate="Week: %{x}<br>LGB Projected: %{y:,}<extra></extra>",
            )
        )

    return apply_chart_style(
        fig,
        title=f"Category Purchase Volume Demand Forecast: {res['category']}",
        x_title="Week",
        y_title="Weekly Purchase Volume (Lines)",
        height=450,
    )


def plot_backtest_comparison(res: dict) -> go.Figure:
    """Overlays actual holdout test period against individual model predictions."""
    fig = go.Figure()

    # Actual Holdout Test
    fig.add_trace(
        go.Scatter(
            x=res["test_dates"],
            y=res["actual_test"],
            mode="lines+markers",
            name="Ground Truth (Actuals)",
            line=dict(color="#1a1a2e", width=3),
            marker=dict(size=6),
            hovertemplate="Week: %{x}<br>Actual: %{y:,}<extra></extra>",
        )
    )

    color_dict = {
        "Seasonal Naive": "#6c757d",
        "Moving Average (4-wk)": "#457b9d",
        "Holt-Winters Exp Smoothing": "#2a9d8f",
        "LightGBM Walk-forward": "#e76f51",
    }

    for model_name, preds in res["predictions"].items():
        fig.add_trace(
            go.Scatter(
                x=res["test_dates"],
                y=preds,
                mode="lines",
                name=model_name,
                line=dict(color=color_dict.get(model_name, "#adb5bd"), width=1.8, dash="dash"),
                hovertemplate=f"Week: %{{x}}<br>{model_name}: %{{y:,.1f}}<extra></extra>",
            )
        )

    return apply_chart_style(
        fig,
        title=f"Chronological Backtest Evaluation: {res['category']} (Best Model: {res['best_model']})",
        x_title="Holdout Week",
        y_title="Purchase Volume",
        height=420,
    )
