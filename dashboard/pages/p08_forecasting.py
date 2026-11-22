"""
GarmentPulse Dashboard — Page 8: Demand Forecasting Engine (Module G)
Weekly category demand projections, uncertainty intervals, and chronological backtest benchmarks.
FORECASTS PROJECT PURCHASE VOLUME — NEVER INVENTORY REQUIREMENTS.
"""

from typing import Optional
import duckdb
import streamlit as st
import pandas as pd

from dashboard.visualisations.forecast_charts import (
    plot_demand_forecast,
    plot_backtest_comparison,
)
from dashboard.components.headers import render_page_header
from dashboard.components.containers import render_card_header
from dashboard.data_service import (
    get_top_forecasting_categories_cached,
    get_demand_forecast_cached,
    get_backtest_cached,
)


def render(conn: Optional[duckdb.DuckDBPyConnection] = None) -> None:
    render_page_header(
        title="Fashion Demand Forecasting & Backtesting",
        subtitle="Generate multi-week forward volume projections with prediction intervals and validate models via chronological backtests.",
        breadcrumb="PREDICTIVE INTELLIGENCE",
        badges=[
            ("Ensemble Forecast", "blue"),
            ("8-Week Prediction Interval", "amber"),
            ("Walk-Forward Backtest", "green"),
        ],
    )

    # 1. Category & Level Selection Controls
    c1, c2, c3 = st.columns([4, 4, 4])
    with c1:
        level_choice = st.selectbox(
            "Forecasting Hierarchy Level",
            options=["Department", "Product Group", "Garment Group"],
            index=0,
        )
    level_key = level_choice.lower().replace(" ", "_")

    top_cats = get_top_forecasting_categories_cached(level=level_choice)
    if not top_cats:
        top_cats = ["Jersey Basic", "Baby Basics", "Trousers"]

    with c2:
        selected_cat = st.selectbox("Select Target Category", options=top_cats, index=0)

    with c3:
        horizon = st.slider("Forecast Horizon (Weeks)", min_value=4, max_value=12, value=8)

    st.markdown("---")

    t1, t2 = st.tabs(["Demand Projection & Prediction Bands", "Chronological Backtest Evaluation"])

    with t1:
        with st.spinner(f"Computing demand forecast for '{selected_cat}'..."):
            forecast_data = get_demand_forecast_cached(selected_cat, level=level_key, horizon=horizon)

        st.plotly_chart(plot_demand_forecast(forecast_data), use_container_width=True)

        with st.expander("View Forecast Values & Uncertainty Bands"):
            proj_df = pd.DataFrame({
                "Forecast Week": forecast_data["future_dates"],
                "Holt-Winters Projected Volume": forecast_data["forecast_hw"],
                "LightGBM Projected Volume": forecast_data["forecast_lgb"],
                "Lower Bound (95%)": forecast_data["lower_bound"],
                "Upper Bound (95%)": forecast_data["upper_bound"],
            })
            st.dataframe(proj_df, use_container_width=True, hide_index=True)

    with t2:
        st.markdown("### Walk-Forward Chronological Model Backtesting")
        st.markdown(
            "Evaluates forecast error across an unobserved 8-week holdout window using **MAE, RMSE, and WAPE** (Weighted Absolute Percentage Error). "
            "No unvalidated forecast is presented without empirical backtesting."
        )

        with st.spinner(f"Backtesting models on '{selected_cat}'..."):
            backtest_res = get_backtest_cached(selected_cat, level=level_key, horizon=horizon)

        if "error" in backtest_res:
            st.error(backtest_res["error"])
        else:
            colA, colB = st.columns([5, 7])
            with colA:
                st.markdown("#### Model Leaderboard")
                st.dataframe(backtest_res["leaderboard"], use_container_width=True, hide_index=True)
                st.success(f"Best Performing Model for this Series: **{backtest_res['best_model']}**")

            with colB:
                st.plotly_chart(plot_backtest_comparison(backtest_res), use_container_width=True)

    st.info(
        "**Critical Planning Boundary:** Purchase volume forecasts project expected checkout lines based on historical demand signals. "
        "Because inventory availability, safety stock, lead times, and warehouse allocations are absent from the dataset, "
        "these figures must NOT be interpreted as raw inventory purchase orders."
    )
