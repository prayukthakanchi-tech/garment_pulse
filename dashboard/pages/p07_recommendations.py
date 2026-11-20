"""
GarmentPulse Dashboard — Page 7: Fashion Recommendation Engine (Module F)
Personalised product recommendations with model evaluation metrics (MAP@12, Recall@12, Coverage).
DO NOT CLAIM RECOMMENDATIONS INCREASE CONVERSION WITHOUT AN EXPERIMENT.
"""

import duckdb
import streamlit as st
import pandas as pd

from src.recommendations.hybrid_recommender import HybridRecommender
from src.recommendations.evaluator import RecommendationEvaluator


def render(conn: duckdb.DuckDBPyConnection) -> None:
    st.markdown("## 🎯 Personalised Fashion Recommendation Engine")
    st.markdown(
        "Generate personalised article discovery sets using hybrid ranking: community popularity, design attribute affinities, and collaborative co-purchase graphs."
    )

    # Sample active customers with diverse history
    sample_cust_sql = """
    SELECT
        t.customer_id,
        COUNT(DISTINCT t.article_id) AS distinct_articles,
        COUNT(*) AS total_purchases
    FROM transactions t
    GROUP BY t.customer_id
    HAVING COUNT(DISTINCT t.article_id) BETWEEN 8 AND 25
    LIMIT 10
    """
    sample_customers = conn.execute(sample_cust_sql).fetchdf()

    t1, t2 = st.tabs(["🛍️ Customer Discovery Simulator", "📐 Chronological Model Evaluation"])

    with t1:
        c1, c2 = st.columns([8, 4])
        with c1:
            cust_options = sample_customers["customer_id"].tolist() if not sample_customers.empty else []
            selected_cust = st.selectbox(
                "Select Sample Customer with Purchase History",
                options=cust_options,
                format_func=lambda x: f"{x[:12]}... (Purchases: {sample_customers[sample_customers['customer_id'] == x]['total_purchases'].values[0]} items)",
            )
        with c2:
            custom_input = st.text_input("Or Enter Custom Customer ID", value="")
            if custom_input.strip():
                selected_cust = custom_input.strip()

        if selected_cust:
            # 1. Customer Closet History
            hist_sql = """
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
            LIMIT 6
            """
            hist_df = conn.execute(hist_sql, [selected_cust]).fetchdf()

            with st.expander(f"👗 Customer Past Purchases ({len(hist_df)} most recent items)", expanded=False):
                st.dataframe(
                    hist_df.rename(columns={
                        "t_dat": "Date",
                        "article_id": "SKU",
                        "prod_name": "Product Name",
                        "department_name": "Department",
                        "garment_group_name": "Garment Group",
                        "colour_group_name": "Colour",
                        "price_index": "Price Index",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

            # 2. Generate Recommendations
            st.markdown("### ✨ Top 12 Recommended Articles for Customer")
            with st.spinner("Generating hybrid recommendations..."):
                recommender = HybridRecommender(conn)
                recs = recommender.recommend(selected_cust, n=12, exclude_purchased=True)

            if recs:
                # Render 3 columns of recommendation cards
                cols = st.columns(3)
                for i, r in enumerate(recs):
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div style="
                            background: #ffffff;
                            border: 1px solid #dee2e6;
                            border-radius: 8px;
                            padding: 14px;
                            margin-bottom: 12px;
                            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
                        ">
                            <div style="font-size: 0.75rem; font-weight: 700; color: #e76f51; text-transform: uppercase;">
                                {r['department_name']}
                            </div>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #1a1a2e; margin: 4px 0;">
                                {r['prod_name']}
                            </div>
                            <div style="font-size: 0.8rem; color: #6c757d; margin-bottom: 6px;">
                                SKU: <code>{r['article_id']}</code> | Colour: <b>{r['colour_group_name']}</b>
                            </div>
                            <div style="font-size: 0.8rem; font-weight: 600; color: #2a9d8f; margin-bottom: 6px;">
                                Affinity Score: {r['hybrid_score']:.3f}
                            </div>
                            <div style="font-size: 0.75rem; color: #495057; background: #f8f9fa; padding: 6px 8px; border-radius: 4px;">
                                💡 {r['reason']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No recommendations found for this customer.")

    with t2:
        st.markdown("### 📊 Chronological Validation Benchmark (MAP@12 vs Popularity Baseline)")
        st.markdown(
            "Evaluation protocol: Strict holdout split. Models are trained on data *before* the cutoff date and evaluated on ground-truth customer purchases *after* the cutoff date. No random train-test splitting."
        )

        with st.spinner("Running chronological evaluation across 40 test holdout customers..."):
            evaluator = RecommendationEvaluator(conn)
            comparison_df = evaluator.compare_all_models(sample_customers=40)

        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        st.warning(
            "⚠️ **Causal Evaluation Disclaimer:** Offline metrics (MAP@12, Recall@12) demonstrate algorithmic ranking efficacy on historical data. "
            "They do NOT prove that displaying these recommendations would increase incremental retail conversion without an active A/B randomized experiment."
        )
