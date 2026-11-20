"""
GarmentPulse — Customer Lifecycle Intelligence Engine (Module C)
RFM-inspired measurable customer segmentation and repeat purchase behavior.
NOTE: Normalised purchase-price contribution is NOT Customer Lifetime Value (CLV).
"""

from __future__ import annotations

from typing import Any, Dict
import duckdb
import pandas as pd

from config.settings import (
    FREQUENCY_HIGH,
    FREQUENCY_MEDIUM,
    RECENCY_ACTIVE_DAYS,
    RECENCY_AT_RISK_DAYS,
    RECENCY_COOLING_DAYS,
)


def _is_prod_db(conn: duckdb.DuckDBPyConnection) -> bool:
    try:
        db_list = conn.execute("PRAGMA database_list;").fetchall()
        return any(row[2] and "garmentpulse.duckdb" in str(row[2]).lower() for row in db_list)
    except Exception:
        return False


class CustomerIntelligence:
    """Computes customer activity, RFM-inspired dimensions, and lifecycle segments."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def get_customer_overview(self) -> Dict[str, Any]:
        """High-level customer base statistics."""
        import os
        ov_file = "data/processed/agg_customer_overview.parquet"
        if _is_prod_db(self.conn) and os.path.exists(ov_file):
            return self.conn.execute(f"SELECT * FROM read_parquet('{ov_file}')").fetchdf().to_dict(orient="records")[0]

        sql = """
        WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
        cust_summary AS (
            SELECT
                customer_id,
                MAX(t_dat) AS last_date,
                COUNT(DISTINCT t_dat) AS purchase_days,
                COUNT(*) AS total_lines,
                SUM(price) AS total_price_contrib
            FROM transactions
            GROUP BY customer_id
        )
        SELECT
            COUNT(*) AS total_purchasing_customers,
            COUNT(CASE WHEN cs.last_date > b.max_date - INTERVAL 30 DAYS THEN 1 END) AS active_30d,
            COUNT(CASE WHEN cs.last_date > b.max_date - INTERVAL 90 DAYS THEN 1 END) AS active_90d,
            COUNT(CASE WHEN cs.last_date > b.max_date - INTERVAL 180 DAYS THEN 1 END) AS active_180d,
            ROUND(AVG(cs.purchase_days), 2) AS avg_purchase_days,
            ROUND(AVG(cs.total_lines), 2) AS avg_purchase_lines,
            ROUND(AVG(cs.total_price_contrib), 4) AS avg_price_contribution,
            ROUND(COUNT(CASE WHEN cs.purchase_days > 1 THEN 1 END) * 100.0 / COUNT(*), 2) AS repeat_customer_rate_pct
        FROM cust_summary cs
        CROSS JOIN bounds b
        """
        return self.conn.execute(sql).fetchdf().to_dict(orient="records")[0]

    def get_customer_segments(self) -> pd.DataFrame:
        """Categorizes all active purchasing customers into measurable segments."""
        import os
        seg_file = "data/processed/agg_customer_segments.parquet"
        if _is_prod_db(self.conn) and os.path.exists(seg_file):
            return self.conn.execute(f"SELECT * FROM read_parquet('{seg_file}') ORDER BY customer_count DESC").fetchdf()

        sql = f"""
        WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
        cust_rfm AS (
            SELECT
                t.customer_id,
                MIN(t.t_dat) AS first_date,
                MAX(t.t_dat) AS last_date,
                DATEDIFF('day', MAX(t.t_dat), b.max_date) AS recency_days,
                DATEDIFF('day', MIN(t.t_dat), b.max_date) AS customer_age_days,
                COUNT(DISTINCT t.t_dat) AS purchase_days,
                COUNT(*) AS total_lines,
                SUM(t.price) AS price_contrib
            FROM transactions t
            CROSS JOIN bounds b
            GROUP BY t.customer_id, b.max_date
        ),
        classified AS (
            SELECT
                customer_id,
                recency_days,
                purchase_days,
                total_lines,
                price_contrib,
                CASE
                    WHEN purchase_days >= {FREQUENCY_HIGH} AND recency_days <= {RECENCY_ACTIVE_DAYS} THEN 'Frequent Buyers'
                    WHEN customer_age_days <= {RECENCY_COOLING_DAYS} AND purchase_days >= 2 THEN 'Emerging Customers'
                    WHEN recency_days <= {RECENCY_ACTIVE_DAYS} THEN 'Recently Active'
                    WHEN recency_days BETWEEN {RECENCY_ACTIVE_DAYS + 1} AND {RECENCY_COOLING_DAYS} THEN 'Cooling Customers'
                    WHEN recency_days BETWEEN {RECENCY_COOLING_DAYS + 1} AND {RECENCY_AT_RISK_DAYS} THEN 'At-Risk Customers'
                    ELSE 'Dormant Customers'
                END AS segment
            FROM cust_rfm
        )
        SELECT
            segment,
            COUNT(*) AS customer_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS segment_share_pct,
            ROUND(AVG(recency_days), 1) AS avg_recency_days,
            ROUND(AVG(purchase_days), 1) AS avg_purchase_days,
            ROUND(AVG(total_lines), 1) AS avg_purchase_lines,
            ROUND(AVG(price_contrib), 4) AS avg_price_contribution
        FROM classified
        GROUP BY segment
        ORDER BY customer_count DESC
        """
        return self.conn.execute(sql).fetchdf()

    def get_repeat_purchase_distribution(self) -> pd.DataFrame:
        """Distribution of customer purchase frequency (1 trip vs 2-3 vs 4-9 vs 10+)."""
        sql = """
        WITH cust_freq AS (
            SELECT
                customer_id,
                COUNT(DISTINCT t_dat) AS distinct_dates
            FROM transactions
            GROUP BY customer_id
        )
        SELECT
            CASE
                WHEN distinct_dates = 1 THEN '1 Purchase Date (Single-buyer)'
                WHEN distinct_dates BETWEEN 2 AND 3 THEN '2-3 Purchase Dates (Repeat)'
                WHEN distinct_dates BETWEEN 4 AND 9 THEN '4-9 Purchase Dates (Engaged)'
                ELSE '10+ Purchase Dates (Loyal Power User)'
            END AS frequency_tier,
            COUNT(*) AS customer_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_pct
        FROM cust_freq
        GROUP BY frequency_tier
        ORDER BY MIN(distinct_dates) ASC
        """
        return self.conn.execute(sql).fetchdf()

    def get_customer_activity_trends(self, freq: str = "month") -> pd.DataFrame:
        """Tracks new vs returning customer monthly activity."""
        trunc = "month" if freq == "month" else "week"
        sql = f"""
        WITH first_seen AS (
            SELECT customer_id, DATE_TRUNC('{trunc}', MIN(t_dat)) AS first_period
            FROM transactions
            GROUP BY customer_id
        ),
        activity AS (
            SELECT DISTINCT
                DATE_TRUNC('{trunc}', t.t_dat) AS period_date,
                t.customer_id,
                CASE WHEN DATE_TRUNC('{trunc}', t.t_dat) = fs.first_period THEN 'New' ELSE 'Returning' END AS cust_type
            FROM transactions t
            JOIN first_seen fs ON t.customer_id = fs.customer_id
        )
        SELECT
            period_date,
            COUNT(CASE WHEN cust_type = 'New' THEN 1 END) AS new_customers,
            COUNT(CASE WHEN cust_type = 'Returning' THEN 1 END) AS returning_customers,
            COUNT(*) AS total_active_customers,
            ROUND(COUNT(CASE WHEN cust_type = 'Returning' THEN 1 END) * 100.0 / COUNT(*), 2) AS returning_customer_share_pct
        FROM activity
        GROUP BY period_date
        ORDER BY period_date ASC
        """
        return self.conn.execute(sql).fetchdf()
