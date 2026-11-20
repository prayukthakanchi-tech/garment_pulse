"""
GarmentPulse — Customer Cohort Analysis Engine (Module C)
Tracks monthly customer cohorts and subsequent repeat purchasing activity.
NOTE: This measures transaction repeat activity, NOT website/session retention.
"""

from __future__ import annotations

from typing import Any, Dict
import duckdb
import pandas as pd


def _is_prod_db(conn: duckdb.DuckDBPyConnection) -> bool:
    try:
        db_list = conn.execute("PRAGMA database_list;").fetchall()
        return any(row[2] and "garmentpulse.duckdb" in str(row[2]).lower() for row in db_list)
    except Exception:
        return False


class CohortAnalysis:
    """Analyzes customer acquisition cohorts and subsequent purchasing repeat activity."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def get_monthly_cohort_data(self, max_period: int = 12) -> pd.DataFrame:
        """Computes cohort month, period number (months since acquisition), and repeat activity rate."""
        import os
        coh_file = "data/processed/agg_cohort_retention.parquet"
        if _is_prod_db(self.conn) and os.path.exists(coh_file):
            sql = f"""
            SELECT cohort_month, cohort_size, period_number, active_customers, repeat_activity_rate_pct
            FROM read_parquet('{coh_file}')
            WHERE period_number <= {max_period}
            ORDER BY cohort_month, period_number
            """
            return self.conn.execute(sql).fetchdf()

        sql = f"""
        WITH customer_first_purchase AS (
            SELECT
                customer_id,
                DATE_TRUNC('month', MIN(t_dat)) AS cohort_month
            FROM transactions
            GROUP BY customer_id
        ),
        customer_monthly_activity AS (
            SELECT DISTINCT
                t.customer_id,
                cfp.cohort_month,
                (YEAR(DATE_TRUNC('month', t.t_dat)) - YEAR(cfp.cohort_month)) * 12 +
                (MONTH(DATE_TRUNC('month', t.t_dat)) - MONTH(cfp.cohort_month)) AS period_number
            FROM transactions t
            JOIN customer_first_purchase cfp ON t.customer_id = cfp.customer_id
        ),
        cohort_sizes AS (
            SELECT
                cohort_month,
                COUNT(DISTINCT customer_id) AS cohort_size
            FROM customer_first_purchase
            GROUP BY cohort_month
        )
        SELECT
            STRFTIME(cma.cohort_month, '%Y-%m') AS cohort_month,
            cs.cohort_size,
            cma.period_number,
            COUNT(DISTINCT cma.customer_id) AS active_customers,
            ROUND(COUNT(DISTINCT cma.customer_id) * 100.0 / cs.cohort_size, 2) AS repeat_activity_rate_pct
        FROM customer_monthly_activity cma
        JOIN cohort_sizes cs ON cma.cohort_month = cs.cohort_month
        WHERE cma.period_number <= {max_period}
        GROUP BY cma.cohort_month, cs.cohort_size, cma.period_number
        ORDER BY cma.cohort_month, cma.period_number
        """
        return self.conn.execute(sql).fetchdf()

    def get_cohort_retention_matrix(self, max_period: int = 12) -> pd.DataFrame:
        """Pivots cohort activity into a matrix suitable for heatmap visualization.
        
        Rows: Cohort Months
        Columns: Period 0, Period 1, ..., Period N (Months since first observed purchase)
        Values: % of cohort active in that month
        """
        raw_df = self.get_monthly_cohort_data(max_period=max_period)
        if raw_df.empty:
            return pd.DataFrame()

        pivot_df = raw_df.pivot(
            index="cohort_month",
            columns="period_number",
            values="repeat_activity_rate_pct",
        )
        # Rename columns to Period 0, Period 1, etc.
        pivot_df.columns = [f"M+{col}" for col in pivot_df.columns]
        return pivot_df

    def get_cohort_summary(self) -> pd.DataFrame:
        """Returns cohort sizes and M+1, M+3, M+6, M+12 repeat activity rates."""
        raw = self.get_monthly_cohort_data(max_period=12)
        if raw.empty:
            return pd.DataFrame()

        summary_rows = []
        for cohort, group in raw.groupby("cohort_month"):
            size = group["cohort_size"].iloc[0]
            m1 = group[group["period_number"] == 1]["repeat_activity_rate_pct"].values
            m3 = group[group["period_number"] == 3]["repeat_activity_rate_pct"].values
            m6 = group[group["period_number"] == 6]["repeat_activity_rate_pct"].values
            m12 = group[group["period_number"] == 12]["repeat_activity_rate_pct"].values

            summary_rows.append({
                "cohort_month": cohort,
                "cohort_size": size,
                "m1_repeat_rate_pct": m1[0] if len(m1) > 0 else None,
                "m3_repeat_rate_pct": m3[0] if len(m3) > 0 else None,
                "m6_repeat_rate_pct": m6[0] if len(m6) > 0 else None,
                "m12_repeat_rate_pct": m12[0] if len(m12) > 0 else None,
            })
        return pd.DataFrame(summary_rows)
