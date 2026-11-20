"""
GarmentPulse Dashboard — Centralized Analytical Data Service
Provides thread-safe, cached analytical queries across all dashboard pages.
Prevents redundant scans of 31.8M transaction rows and isolates DuckDB connections.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st

from src.database.connection import get_cursor, get_db_connection


# ─────────────────────────────────────────────
# PAGE 1: EXECUTIVE OVERVIEW
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_executive_kpis() -> Dict[str, Any]:
    """Fetch high-level portfolio KPIs across entire transaction archive."""
    import os
    parquet_path = "data/processed/agg_portfolio_kpis.parquet"
    if os.path.exists(parquet_path):
        import duckdb
        return duckdb.read_parquet(parquet_path).fetchdf().to_dict(orient="records")[0]

    cur = get_cursor()
    try:
        sql = """
        SELECT
            COUNT(*) AS total_volume,
            COUNT(DISTINCT customer_id) AS total_customers,
            COUNT(DISTINCT article_id) AS total_articles,
            ROUND(AVG(price), 6) AS avg_price_index
        FROM transactions
        """
        row = cur.execute(sql).fetchdf().to_dict(orient="records")[0]
        return row
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_monthly_volume_trend() -> pd.DataFrame:
    """Monthly transaction volume trajectory."""
    cur = get_cursor()
    try:
        sql = """
        SELECT
            DATE_TRUNC('month', t_dat) AS month,
            COUNT(*) AS monthly_volume,
            COUNT(DISTINCT customer_id) AS active_customers
        FROM transactions
        GROUP BY DATE_TRUNC('month', t_dat)
        ORDER BY month ASC
        """
        return cur.execute(sql).fetchdf()
    finally:
        cur.close()


# ─────────────────────────────────────────────
# PAGE 2: CATEGORY INTELLIGENCE
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_category_performance_cached(level: str = "department", min_transactions: int = 200) -> pd.DataFrame:
    """Category volume, breadths, concentration, and price indices."""
    from src.analytics.category_intelligence import CategoryIntelligence
    cur = get_cursor()
    try:
        ci = CategoryIntelligence(cur)
        return ci.get_category_performance(level=level, min_transactions=min_transactions)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_category_growth_cached(level: str = "department", min_transactions: int = 200) -> pd.DataFrame:
    """Category period-over-period momentum and acceleration rankings."""
    from src.analytics.category_intelligence import CategoryIntelligence
    cur = get_cursor()
    try:
        ci = CategoryIntelligence(cur)
        return ci.get_category_growth(level=level, min_transactions=min_transactions)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_yoy_comparison_cached(level: str = "department") -> pd.DataFrame:
    """Calendar month YoY volume comparisons."""
    from src.analytics.category_intelligence import CategoryIntelligence
    cur = get_cursor()
    try:
        ci = CategoryIntelligence(cur)
        return ci.get_yoy_comparison(level=level)
    finally:
        cur.close()


# ─────────────────────────────────────────────
# PAGE 3: FASHION ATTRIBUTE INTELLIGENCE
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_colour_performance_cached(min_transactions: int = 1000) -> pd.DataFrame:
    """Colour palette demand distributions."""
    from src.analytics.attribute_intelligence import AttributeIntelligence
    cur = get_cursor()
    try:
        ai = AttributeIntelligence(cur)
        return ai.get_colour_performance(min_transactions=min_transactions)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_garment_group_trends_cached(freq: str = "month") -> pd.DataFrame:
    """Garment group monthly trajectories."""
    from src.analytics.attribute_intelligence import AttributeIntelligence
    cur = get_cursor()
    try:
        ai = AttributeIntelligence(cur)
        return ai.get_garment_group_trends(freq=freq)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_attribute_growth_rankings_cached(attribute: str = "colour_group_name", min_volume: int = 1000) -> pd.DataFrame:
    """Fastest growing attributes over recent 4 weeks."""
    from src.analytics.attribute_intelligence import AttributeIntelligence
    cur = get_cursor()
    try:
        ai = AttributeIntelligence(cur)
        return ai.get_attribute_growth_rankings(attribute=attribute, min_volume=min_volume)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_department_attribute_heatmap_cached(attribute: str = "colour_group_name", top_depts: int = 10, top_attrs: int = 10) -> pd.DataFrame:
    """Cross-tabulation between top departments and design attributes."""
    from src.analytics.attribute_intelligence import AttributeIntelligence
    cur = get_cursor()
    try:
        ai = AttributeIntelligence(cur)
        return ai.get_department_attribute_heatmap(attribute=attribute, top_depts=top_depts, top_attrs=top_attrs)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_colour_garment_combinations_cached(top_n: int = 15) -> pd.DataFrame:
    """Co-occurrence of colour and garment groupings."""
    from src.analytics.attribute_intelligence import AttributeIntelligence
    cur = get_cursor()
    try:
        ai = AttributeIntelligence(cur)
        return ai.get_colour_garment_combinations(top_n=top_n)
    finally:
        cur.close()


# ─────────────────────────────────────────────
# PAGE 4: CUSTOMER INTELLIGENCE
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_customer_overview_cached() -> Dict[str, Any]:
    """Customer base size, active tiers, and repeat rates."""
    from src.segmentation.customer_intelligence import CustomerIntelligence
    cur = get_cursor()
    try:
        ci = CustomerIntelligence(cur)
        return ci.get_customer_overview()
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_customer_segments_cached() -> pd.DataFrame:
    """RFM customer segmentation distributions."""
    from src.segmentation.customer_intelligence import CustomerIntelligence
    cur = get_cursor()
    try:
        ci = CustomerIntelligence(cur)
        return ci.get_customer_segments()
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_cohort_retention_matrix_cached(max_period: int = 12) -> pd.DataFrame:
    """Monthly customer cohort retention matrix."""
    from src.segmentation.cohort_analysis import CohortAnalysis
    cur = get_cursor()
    try:
        ca = CohortAnalysis(cur)
        return ca.get_cohort_retention_matrix(max_period=max_period)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_cohort_summary_cached() -> pd.DataFrame:
    """Cohort sizes and summary repeat milestones."""
    from src.segmentation.cohort_analysis import CohortAnalysis
    cur = get_cursor()
    try:
        ca = CohortAnalysis(cur)
        return ca.get_cohort_summary()
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_customer_activity_trends_cached(freq: str = "month") -> pd.DataFrame:
    """New vs returning customer composition trends."""
    from src.segmentation.customer_intelligence import CustomerIntelligence
    cur = get_cursor()
    try:
        ci = CustomerIntelligence(cur)
        return ci.get_customer_activity_trends(freq=freq)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_repeat_purchase_distribution_cached() -> pd.DataFrame:
    """Purchase frequency tier histogram."""
    from src.segmentation.customer_intelligence import CustomerIntelligence
    cur = get_cursor()
    try:
        ci = CustomerIntelligence(cur)
        return ci.get_repeat_purchase_distribution()
    finally:
        cur.close()


# ─────────────────────────────────────────────
# PAGE 5: PRODUCT INTELLIGENCE
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_product_classifications_cached() -> pd.DataFrame:
    """Article lifecycle stages distribution."""
    from src.analytics.product_intelligence import ProductIntelligence
    cur = get_cursor()
    try:
        pi = ProductIntelligence(cur)
        return pi.get_product_classifications()
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_product_performance_cached(
    limit: int = 25,
    search: Optional[str] = None,
    lifecycle_filter: Optional[str] = None,
    sort_by: str = "purchase_volume",
) -> pd.DataFrame:
    """Searchable, paginated article velocity table."""
    from src.analytics.product_intelligence import ProductIntelligence
    cur = get_cursor()
    try:
        pi = ProductIntelligence(cur)
        return pi.get_product_performance(
            limit=limit,
            search=search if search else None,
            lifecycle_filter=lifecycle_filter if lifecycle_filter != "All" else None,
            sort_by=sort_by,
        )
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_product_trends_cached(article_id: str) -> pd.DataFrame:
    """Weekly sales trend for a selected article."""
    from src.analytics.product_intelligence import ProductIntelligence
    cur = get_cursor()
    try:
        pi = ProductIntelligence(cur)
        return pi.get_product_trends(article_id)
    finally:
        cur.close()


# ─────────────────────────────────────────────
# PAGE 6: CHANNEL ANALYTICS
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_channel_overview_cached() -> pd.DataFrame:
    """Macro channel volume, customer reach, and price indices."""
    from src.analytics.channel_intelligence import ChannelIntelligence
    cur = get_cursor()
    try:
        chi = ChannelIntelligence(cur)
        return chi.get_channel_overview()
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_channel_trends_cached(freq: str = "month") -> pd.DataFrame:
    """Monthly channel purchase volume trajectory."""
    from src.analytics.channel_intelligence import ChannelIntelligence
    cur = get_cursor()
    try:
        chi = ChannelIntelligence(cur)
        return chi.get_channel_trends(freq=freq)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_channel_customer_overlap_cached() -> Dict[str, Any]:
    """Omnichannel vs single-channel customer penetration."""
    from src.analytics.channel_intelligence import ChannelIntelligence
    cur = get_cursor()
    try:
        chi = ChannelIntelligence(cur)
        return chi.get_channel_customer_overlap()
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_channel_department_contribution_cached(top_n: int = 12) -> pd.DataFrame:
    """Department mix across Sales Channel 1 and 2."""
    from src.analytics.channel_intelligence import ChannelIntelligence
    cur = get_cursor()
    try:
        chi = ChannelIntelligence(cur)
        return chi.get_channel_department_contribution(top_n=top_n)
    finally:
        cur.close()


# ─────────────────────────────────────────────
# PAGE 7: RECOMMENDATIONS
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_sample_customers_cached() -> pd.DataFrame:
    """Diverse active sample customers for interactive simulator."""
    cur = get_cursor()
    try:
        sql = """
        SELECT
            t.customer_id,
            COUNT(DISTINCT t.article_id) AS distinct_articles,
            COUNT(*) AS total_purchases
        FROM transactions t
        GROUP BY t.customer_id
        HAVING COUNT(DISTINCT t.article_id) BETWEEN 8 AND 25
        LIMIT 10
        """
        return cur.execute(sql).fetchdf()
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_customer_history_cached(customer_id: str, limit: int = 6) -> pd.DataFrame:
    """Past purchase history of a customer."""
    cur = get_cursor()
    try:
        sql = """
        SELECT
            t.t_dat,
            a.article_id,
            a.prod_name,
            a.department_name,
            a.garment_group_name,
            a.colour_group_name,
            ROUND(t.price, 4) AS price_index
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        WHERE t.customer_id = ?
        ORDER BY t.t_dat DESC
        LIMIT ?
        """
        return cur.execute(sql, [customer_id, limit]).fetchdf()
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_hybrid_recommendations_cached(customer_id: str, n: int = 12) -> List[Dict[str, Any]]:
    """Generate hybrid candidate recommendations for target customer."""
    from src.recommendations.hybrid_recommender import HybridRecommender
    cur = get_cursor()
    try:
        rec = HybridRecommender(cur)
        return rec.recommend(customer_id, n=n, exclude_purchased=True)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_model_evaluation_cached(sample_size: int = 25) -> pd.DataFrame:
    """Chronological model holdout benchmark (MAP@12, Recall@12, Coverage)."""
    from src.recommendations.evaluator import RecommendationEvaluator
    cur = get_cursor()
    try:
        ev = RecommendationEvaluator(cur)
        return ev.compare_all_models(sample_customers=sample_size)
    finally:
        cur.close()


# ─────────────────────────────────────────────
# PAGE 8: DEMAND FORECASTING
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_top_forecasting_categories_cached(level: str = "department") -> List[str]:
    """Categories with sufficient historical transaction density."""
    cur = get_cursor()
    try:
        level_key = level.lower().replace(" ", "_")
        col_name = "department_name" if level_key == "department" else ("product_group_name" if "product" in level_key else "garment_group_name")
        sql = f"""
        SELECT a.{col_name}
        FROM articles a
        JOIN (
            SELECT article_id, COUNT(*) AS vol
            FROM transactions
            GROUP BY article_id
        ) t ON a.article_id = t.article_id
        GROUP BY a.{col_name}
        HAVING SUM(t.vol) >= 5000
        ORDER BY SUM(t.vol) DESC
        LIMIT 25
        """
        res = cur.execute(sql).fetchall()
        return [r[0] for r in res]
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_demand_forecast_cached(category: str, level: str = "department", horizon: int = 8) -> Dict[str, Any]:
    """Generate multi-model forward demand projection with prediction intervals."""
    from src.forecasting.demand_forecaster import DemandForecaster
    cur = get_cursor()
    try:
        df = DemandForecaster(cur)
        return df.generate_forward_forecast(category, level=level, horizon=horizon)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_backtest_cached(category: str, level: str = "department", horizon: int = 8) -> Dict[str, Any]:
    """Walk-forward chronological backtest metrics and leaderboard."""
    from src.forecasting.demand_forecaster import DemandForecaster
    cur = get_cursor()
    try:
        df = DemandForecaster(cur)
        return df.backtest(category, level=level, horizon=horizon)
    finally:
        cur.close()


# ─────────────────────────────────────────────
# PAGE 9: OPPORTUNITY RADAR
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_opportunity_scores_cached(level: str = "department") -> pd.DataFrame:
    """Multi-factor commercial opportunity scoring and quadrant classifications."""
    from src.insights.opportunity_engine import OpportunityEngine
    cur = get_cursor()
    try:
        oe = OpportunityEngine(cur)
        return oe.calculate_opportunity_scores(level=level)
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_opportunity_recommendations_cached(level: str = "department", top_n: int = 6) -> List[Dict[str, Any]]:
    """5-part structured merchandising priority action cards."""
    from src.insights.opportunity_engine import OpportunityEngine
    cur = get_cursor()
    try:
        oe = OpportunityEngine(cur)
        scores_df = get_opportunity_scores_cached(level=level)
        return oe.generate_recommendations(level=level, top_n=top_n, scores_df=scores_df)
    finally:
        cur.close()


# ─────────────────────────────────────────────
# PAGE 10: DATA QUALITY & GOVERNANCE
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_data_validation_suite_cached() -> List[Dict[str, Any]]:
    """Automated rule-based validation checks across all tables."""
    from src.preprocessing.data_validator import DataValidator
    cur = get_cursor()
    try:
        validator = DataValidator(cur)
        return validator.run_all_validations()
    finally:
        cur.close()


@st.cache_data(show_spinner=False)
def get_data_cleaning_summary_cached() -> Dict[str, Any]:
    """Ingestion transformations and deduplication audit log."""
    from src.preprocessing.data_cleaner import DataCleaner
    cur = get_cursor()
    try:
        cleaner = DataCleaner(cur)
        return cleaner.get_cleaning_summary()
    finally:
        cur.close()
