"""
GarmentPulse Dashboard — Page 9: Commercial Opportunity Radar & AI Assistant (Modules H & I)
Multi-factor opportunity scoring, spider radar charts, 5-part merchandising action cards, and guarded AI decision assistant.
"""

import duckdb
import streamlit as st
import pandas as pd

from dashboard.visualisations.opportunity_charts import (
    plot_opportunity_radar,
    plot_opportunity_ranking_bar,
)
from src.insights.opportunity_engine import OpportunityEngine
from src.insights.ai_assistant import AIBusinessAssistant


def render(conn: duckdb.DuckDBPyConnection) -> None:
    st.markdown("## 🧭 Commercial Opportunity Radar & AI Decision Assistant")
    st.markdown(
        "Platform differentiating engine: Synthesizes volume growth, customer expansion, repeat retention, and assortment concentration into actionable merchandising priorities."
    )

    oe = OpportunityEngine(conn)
    assistant = AIBusinessAssistant(conn)

    t1, t2, t3 = st.tabs(["🎯 Opportunity Radar & Rankings", "📋 Structured Merchandising Action Cards", "🤖 AI Merchandising Assistant"])

    with t1:
        col_ctrl1, col_ctrl2 = st.columns([6, 6])
        with col_ctrl1:
            level_sel = st.selectbox("Category Taxonomy", options=["Department", "Product Group", "Garment Group"], index=0)
        level_k = level_sel.lower().replace(" ", "_")

        scores_df = oe.calculate_opportunity_scores(level=level_k)

        colA, colB = st.columns([6, 6])
        with colA:
            st.plotly_chart(plot_opportunity_radar(scores_df, top_n=4), use_container_width=True)
        with colB:
            st.plotly_chart(plot_opportunity_ranking_bar(scores_df, top_n=12), use_container_width=True)

        st.markdown("### 📊 Opportunity Scoring Component Breakdown")
        st.dataframe(
            scores_df[[
                "category_name", "opportunity_score", "classification",
                "total_volume", "recent_vol", "volume_growth", "customer_growth", "repeat_rate"
            ]].rename(columns={
                "category_name": level_sel,
                "opportunity_score": "Opportunity Score (0-100)",
                "classification": "Demand Classification",
                "total_volume": "Total Lines",
                "recent_vol": "Recent 4W Vol",
                "volume_growth": "Vol Growth Rate",
                "customer_growth": "Cust Growth Rate",
                "repeat_rate": "Repeat Ratio",
            }),
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("📐 Transparent Scoring Formula & Weighting Schema"):
            st.markdown("""
            **Relative Opportunity Score Formula:**
            $$\\text{Opportunity Score} = 100 \\times \\sum (w_i \\times S_i)$$
            - **Recent Volume Growth ($w = 0.25$):** Normalized growth across recent 4-week window.
            - **Customer Acquisition Growth ($w = 0.20$):** Unique customer participation velocity.
            - **Repeat Customer Ratio ($w = 0.15$):** Share of multi-purchase customer baskets.
            - **Category Portfolio Contribution ($w = 0.15$):** Total volume share within enterprise.
            - **Assortment Breadth / Inverted HHI ($w = 0.10$):** Diversified product demand (lower SKU concentration = higher resilience).
            - **Attribute Momentum Signal ($w = 0.15$):** Average momentum of underlying fashion traits.
            """)

    with t2:
        st.markdown("### 📝 Structured Merchandising Action Cards")
        recs = oe.generate_recommendations(level=level_k, top_n=6)

        for r in recs:
            status_color = "#2a9d8f" if "Strong" in r["classification"] else ("#457b9d" if "Emerging" in r["classification"] else "#e76f51")
            st.markdown(f"""
            <div style="
                background: #ffffff;
                border-left: 5px solid {status_color};
                border-radius: 6px;
                padding: 16px 20px;
                margin-bottom: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 1.15rem; font-weight: 700; color: #1a1a2e;">{r['category']}</span>
                    <span style="background: #f1f3f5; color: {status_color}; font-weight: 700; font-size: 0.85rem; padding: 4px 10px; border-radius: 12px;">
                        {r['classification']} (Score: {r['opportunity_score']:.1f})
                    </span>
                </div>
                <div style="font-size: 0.88rem; color: #212529; margin-bottom: 6px;"><b>🔎 OBSERVATION:</b> {r['observation']}</div>
                <div style="font-size: 0.88rem; color: #495057; margin-bottom: 6px;"><b>📊 EVIDENCE:</b> {r['evidence']}</div>
                <div style="font-size: 0.88rem; color: #264653; margin-bottom: 6px;"><b>💼 BUSINESS IMPLICATION:</b> {r['business_implication']}</div>
                <div style="font-size: 0.88rem; color: #2a9d8f; font-weight: 600; margin-bottom: 6px;"><b>🎯 RECOMMENDED ACTION:</b> {r['recommended_action']}</div>
                <div style="font-size: 0.8rem; color: #868e96; font-style: italic;"><b>⚠️ LIMITATION:</b> {r['limitation']}</div>
            </div>
            """, unsafe_allow_html=True)

    with t3:
        st.markdown("### 🤖 Guarded AI Decision Insights Assistant")
        st.markdown(
            "Executive Q&A engine grounded exclusively in verified DuckDB SQL calculations. "
            "The AI explains verified metrics and is strictly prohibited from fabricating numbers."
        )

        preset_questions = [
            "Which departments showed the strongest recent purchase momentum?",
            "Which garment groups have declining customer activity?",
            "Which customer segments have the highest repeat activity?",
            "Which sales channel drives higher average price contribution?",
            "Which physical fashion attributes dominate consumer volume?",
        ]

        user_q = st.selectbox("Select an Executive Decision Query", options=preset_questions)
        custom_q = st.text_input("Or Ask a Specific Question", value="")
        effective_q = custom_q.strip() if custom_q.strip() else user_q

        if st.button("Generate Verified Business Answer", type="primary"):
            with st.spinner("Executing verified DuckDB calculations..."):
                ans = assistant.answer_question(effective_q)

            st.markdown(f"#### 💡 Grounded Decision Insight")
            st.success(f"**Key Finding:** {ans['finding']}")

            cA, cB = st.columns([6, 6])
            with cA:
                st.markdown(f"**Observation Period:** `{ans['observation_period']}`")
                st.markdown(f"**Business Interpretation:** {ans['business_interpretation']}")
            with cB:
                st.markdown(f"**Recommended Merchandising Action:** {ans['recommended_action']}")
                st.markdown(f"**Governance & Data Limitation:** *{ans['limitations']}*")

            with st.expander("🔍 View Raw Supporting Verified SQL Data"):
                st.write(ans["supporting_metrics"])
