"""
GarmentPulse Dashboard — Page 7: Fashion Recommendation Engine (Module F)
Personalised product recommendations with model evaluation metrics (MAP@12, Recall@12, Coverage).
DO NOT CLAIM RECOMMENDATIONS INCREASE CONVERSION WITHOUT AN EXPERIMENT.
"""

from typing import Optional
import duckdb
import streamlit as st
import pandas as pd

from dashboard.data_service import (
    get_sample_customers_cached,
    get_customer_history_cached,
    get_hybrid_recommendations_cached,
    get_model_evaluation_cached,
)
from dashboard.components.headers import render_page_header
from dashboard.components.containers import render_card_header


def render(conn: Optional[duckdb.DuckDBPyConnection] = None) -> None:
    render_page_header(
        title="Personalised Fashion Recommendation Engine",
        subtitle="Generate discovery sets using hybrid ranking: community popularity, content attribute affinity, and item-item co-purchase graphs.",
        breadcrumb="MACHINE LEARNING & DISCOVERY",
        badges=[
            ("Hybrid Ensembling", "blue"),
            ("Chronological Holdout", "green"),
            ("MAP@12 Benchmarked", "violet"),
        ],
    )

    # Sample active customers with diverse history
    sample_customers = get_sample_customers_cached()

    t1, t2 = st.tabs(["Customer Discovery Simulator", "Chronological Model Evaluation"])

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
            hist_df = get_customer_history_cached(selected_cust, limit=6)

            with st.expander(f"Customer Past Purchases ({len(hist_df)} most recent items)", expanded=False):
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
            st.markdown("### Top 12 Recommended Articles for Customer")
            with st.spinner("Generating hybrid recommendations..."):
                recs = get_hybrid_recommendations_cached(selected_cust, n=12)

            if recs:
                # Render 3 columns of recommendation cards
                cols = st.columns(3)
                for i, r in enumerate(recs):
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div style="
                            background: #FFFFFF;
                            border: 1px solid #E2E8F0;
                            border-radius: 10px;
                            padding: 16px;
                            margin-bottom: 14px;
                            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
                        ">
                            <div style="font-size: 0.72rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.05em;">
                                {r['department_name']}
                            </div>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; margin: 4px 0;">
                                {r['prod_name']}
                            </div>
                            <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 6px;">
                                SKU: <code>{r['article_id']}</code> | Colour: <b>{r['colour_group_name']}</b>
                            </div>
                            <div style="font-size: 0.82rem; font-weight: 700; color: #059669; margin-bottom: 8px;">
                                Hybrid Affinity Score: {r['hybrid_score']:.3f}
                            </div>
                            <div style="font-size: 0.76rem; color: #334155; background: #F8FAFC; border: 1px solid #F1F5F9; padding: 6px 10px; border-radius: 6px;">
                                {r['reason']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No recommendations found for this customer.")

    with t2:
        st.markdown("### Chronological Validation Benchmark (MAP@12 vs Popularity Baseline)")
        st.markdown(
            "Evaluation protocol: Strict holdout split. Models are trained on data *before* the cutoff date and evaluated on ground-truth customer purchases *after* the cutoff date. No random train-test splitting."
        )

        # Baseline pre-calculated or cached holdout benchmark
        run_live = st.button("Run Live Holdout Benchmark Evaluation (20 Holdout Customers)")
        sample_size = 20 if run_live else 10

        with st.spinner("Computing chronological holdout evaluation..."):
            comparison_df = get_model_evaluation_cached(sample_size=sample_size)

        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        st.warning(
            "**Causal Evaluation Disclaimer:** Offline metrics (MAP@12, Recall@12) demonstrate algorithmic ranking efficacy on historical data. "
            "They do NOT prove that displaying these recommendations would increase incremental retail conversion without an active A/B randomized experiment."
        )
