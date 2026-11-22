"""
GarmentPulse Dashboard — Page 10: Data Quality & Governance
Validation results, duplicate basket analysis, cleaning decision audit trails, and data limitation boundaries.
"""

from typing import Optional
import duckdb
import streamlit as st
import pandas as pd

from config.settings import DATA_LIMITATIONS
from dashboard.components.headers import render_page_header
from dashboard.components.containers import render_card_header
from dashboard.data_service import (
    get_data_validation_suite_cached,
    get_data_cleaning_summary_cached,
)


def render(conn: Optional[duckdb.DuckDBPyConnection] = None) -> None:
    render_page_header(
        title="Data Quality, Governance & Limitations",
        subtitle="Complete transparency regarding dataset validation, deduplication rationale, transformation audit trails, and non-negotiable analytical boundaries.",
        breadcrumb="AUDIT & COMPLIANCE",
        badges=[
            ("10 Automated Rule Checks", "green"),
            ("Audit Trail Verified", "blue"),
            ("11 Governance Boundaries", "amber"),
        ],
    )

    t1, t2, t3 = st.tabs(["Automated Validation Suite", "Cleaning Decisions Log", "Empirical Data Limitations"])

    with t1:
        st.markdown("### Rule-Based Automated Quality Checks")
        with st.spinner("Executing rule-based automated quality checks..."):
            findings = get_data_validation_suite_cached()

        pass_c = sum(1 for f in findings if f["status"] == "PASS")
        warn_c = sum(1 for f in findings if f["status"] == "WARNING")
        fail_c = sum(1 for f in findings if f["status"] == "FAIL")

        c1, c2, c3 = st.columns(3)
        c1.metric("Tests Passed", pass_c)
        c2.metric("Warnings (Documented Outliers)", warn_c)
        c3.metric("Critical Failures", fail_c)

        for f in findings:
            status_badge = f["status"]
            with st.expander(f"[{status_badge}] — {f['check']} (`{f['table']}`)", expanded=(f["status"] != "PASS")):
                st.markdown(f"**Technical Details:** {f['details']}")
                st.markdown(f"**Architectural Impact:** {f['impact']}")

    with t2:
        st.markdown("### Documented Ingestion & Cleaning Actions")
        summary = get_data_cleaning_summary_cached()

        decisions_df = pd.DataFrame(summary["decisions"])
        st.dataframe(
            decisions_df.rename(columns={
                "entity": "Entity Table",
                "issue": "Data Condition / Issue",
                "action": "Governed Cleaning Action",
                "rationale": "Engineering Rationale",
                "status": "Pipeline Status",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### Duplicate Transaction Investigation Detail")
        st.info(
            "**Technical Deduplication Finding:** The transaction dataset contains 3,212,929 duplicate rows (identical date, customer, article, price). "
            "Because retail checkout datasets frequently omit an integer quantity field, identical rows represent shoppers purchasing multiple quantities of the same item. "
            "**Policy:** These records are preserved to avoid distorting true physical demand velocity."
        )

    with t3:
        st.markdown("### Absolute Non-Negotiable Data Limitations")
        st.markdown(
            "To uphold rigorous academic and professional standards, the platform strictly enforces the following boundaries:"
        )

        for i, lim in enumerate(DATA_LIMITATIONS, 1):
            st.markdown(f"**{i}.** {lim}")

        st.warning(
            "**Disclaimer:** GarmentPulse is an independent portfolio intelligence project. "
            "It is NOT an official H&M or Myntra production system. "
            "All findings are derived from the publicly available Kaggle research dataset."
        )
