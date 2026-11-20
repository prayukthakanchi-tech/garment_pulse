"""
GarmentPulse — Data Cleaner
Documented, transparent data cleaning routines and cleaning summary generation.
"""

from __future__ import annotations

from typing import Any, Dict
import duckdb


class DataCleaner:
    """Provides transparent, documented cleaning actions and summarizes cleaning decisions."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def get_cleaning_summary(self) -> Dict[str, Any]:
        """Return full summary of cleaning rules, actions taken, and data quality states."""
        # Query current counts
        tx_stats = self.conn.execute("""
            SELECT
                COUNT(*) AS total_tx,
                COUNT(DISTINCT customer_id) AS unique_cust,
                COUNT(DISTINCT article_id) AS unique_art,
                MIN(t_dat) AS min_date,
                MAX(t_dat) AS max_date
            FROM transactions
        """).fetchdf().to_dict(orient="records")[0]

        art_stats = self.conn.execute("""
            SELECT
                COUNT(*) AS total_articles,
                COUNT(*) - COUNT(detail_desc) AS missing_desc
            FROM articles
        """).fetchdf().to_dict(orient="records")[0]

        cust_stats = self.conn.execute("""
            SELECT
                COUNT(*) AS total_customers,
                COUNT(*) - COUNT(age) AS missing_age,
                COUNT(*) - COUNT(fn) AS missing_fn,
                COUNT(*) - COUNT(active) AS missing_active
            FROM customers
        """).fetchdf().to_dict(orient="records")[0]

        decisions = [
            {
                "entity": "transactions",
                "issue": "Identical rows (duplicate checkouts on same date)",
                "action": "RETAIN ALL ROWS",
                "rationale": "No line-item quantity column exists in H&M transaction data. Duplicate records represent consumer basket multiplicity (purchasing >1 unit). Dropping them distorts demand.",
                "status": "APPLIED",
            },
            {
                "entity": "transactions",
                "issue": "String IDs with leading zeros",
                "action": "EXPLICIT VARCHAR / Utf8 ENFORCEMENT",
                "rationale": "Preserves leading zeros in 10-character article codes (e.g. 0108775015) and 64-character customer hashes, preventing integer conversion bugs.",
                "status": "APPLIED",
            },
            {
                "entity": "articles",
                "issue": "Missing product descriptions (`detail_desc`)",
                "action": "COALESCE WITH PRODUCT NAME",
                "rationale": "Allows NLP/content-based recommenders to fall back to `prod_name` and taxonomy attributes rather than failing on null strings.",
                "status": "APPLIED",
            },
            {
                "entity": "customers",
                "issue": "Missing age values (~1.16% nulls)",
                "action": "ISOLATE AS UNKNOWN / PRESERVE NULL",
                "rationale": "Imputing mean or median age would distort demographic age-bracket penetration metrics. Filtered dynamically in age-specific analytics.",
                "status": "APPLIED",
            },
            {
                "entity": "customers",
                "issue": "Missing FN and Active boolean flags",
                "action": "TREAT NULL AS 0 (INACTIVE/UNSUBSCRIBED)",
                "rationale": "Missing engagement opt-in represents default unengaged status in customer lifecycle classification.",
                "status": "APPLIED",
            },
            {
                "entity": "transactions",
                "issue": "Price field normalization",
                "action": "LABELED AS NORMALISED PURCHASE-PRICE INDEX",
                "rationale": "The raw price is a pre-normalised dimensionless index. Never converted to or displayed as currency ($/€/£).",
                "status": "APPLIED",
            },
        ]

        return {
            "transactions": tx_stats,
            "articles": art_stats,
            "customers": cust_stats,
            "decisions": decisions,
        }
