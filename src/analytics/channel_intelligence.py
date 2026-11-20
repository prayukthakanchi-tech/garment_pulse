"""
GarmentPulse — Sales Channel Intelligence Engine (Module E)
Compares Channel 1 vs Channel 2 behavior without unverified business assumptions.
"""

from __future__ import annotations

from typing import Any, Dict
import duckdb
import pandas as pd

from config.settings import CHANNEL_LABELS


class ChannelIntelligence:
    """Analyzes differences between Sales Channel 1 and Sales Channel 2."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def get_channel_overview(self) -> pd.DataFrame:
        """High-level summary of volume, unique customers, and price distribution by channel."""
        sql = """
        SELECT
            sales_channel_id,
            COUNT(*) AS purchase_volume,
            COUNT(DISTINCT customer_id) AS unique_customers,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS volume_share_pct,
            ROUND(AVG(price), 6) AS avg_normalised_price,
            ROUND(MEDIAN(price), 6) AS median_normalised_price,
            ROUND(STDDEV(price), 6) AS std_normalised_price,
            ROUND(SUM(price), 2) AS total_price_contribution
        FROM transactions
        GROUP BY sales_channel_id
        ORDER BY sales_channel_id
        """
        df = self.conn.execute(sql).fetchdf()
        df["channel_label"] = df["sales_channel_id"].map(lambda x: CHANNEL_LABELS.get(x, f"Channel {x}"))
        return df

    def get_channel_trends(self, freq: str = "month") -> pd.DataFrame:
        """Monthly or weekly purchase volume trajectory per channel."""
        trunc = "month" if freq == "month" else "week"
        sql = f"""
        SELECT
            DATE_TRUNC('{trunc}', t_dat) AS period_date,
            sales_channel_id,
            COUNT(*) AS purchase_volume,
            COUNT(DISTINCT customer_id) AS unique_customers
        FROM transactions
        GROUP BY DATE_TRUNC('{trunc}', t_dat), sales_channel_id
        ORDER BY period_date ASC, sales_channel_id
        """
        df = self.conn.execute(sql).fetchdf()
        df["channel_label"] = df["sales_channel_id"].map(lambda x: CHANNEL_LABELS.get(x, f"Channel {x}"))
        return df

    def get_channel_customer_overlap(self) -> Dict[str, Any]:
        """Calculates exclusive vs cross-channel (omnichannel) purchasing behavior."""
        sql = """
        WITH cust_channels AS (
            SELECT
                customer_id,
                MAX(CASE WHEN sales_channel_id = 1 THEN 1 ELSE 0 END) AS used_ch1,
                MAX(CASE WHEN sales_channel_id = 2 THEN 1 ELSE 0 END) AS used_ch2
            FROM transactions
            GROUP BY customer_id
        )
        SELECT
            COUNT(CASE WHEN used_ch1 = 1 AND used_ch2 = 0 THEN 1 END) AS channel_1_only,
            COUNT(CASE WHEN used_ch1 = 0 AND used_ch2 = 1 THEN 1 END) AS channel_2_only,
            COUNT(CASE WHEN used_ch1 = 1 AND used_ch2 = 1 THEN 1 END) AS both_channels,
            COUNT(*) AS total_active_customers
        FROM cust_channels
        """
        row = self.conn.execute(sql).fetchone()
        tot = row[3] if row and row[3] > 0 else 1
        return {
            "channel_1_only": row[0],
            "channel_2_only": row[1],
            "both_channels": row[2],
            "total_active_customers": row[3],
            "channel_1_only_pct": round(row[0] * 100.0 / tot, 2),
            "channel_2_only_pct": round(row[1] * 100.0 / tot, 2),
            "both_channels_pct": round(row[2] * 100.0 / tot, 2),
        }

    def get_channel_department_contribution(self, top_n: int = 15) -> pd.DataFrame:
        """Compares department volume distribution between Channel 1 and Channel 2."""
        sql = f"""
        WITH top_depts AS (
            SELECT a.department_name
            FROM transactions t JOIN articles a ON t.article_id = a.article_id
            GROUP BY a.department_name ORDER BY COUNT(*) DESC LIMIT {top_n}
        )
        SELECT
            a.department_name,
            t.sales_channel_id,
            COUNT(*) AS purchase_volume,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY t.sales_channel_id), 2) AS dept_share_within_channel_pct
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        WHERE a.department_name IN (SELECT department_name FROM top_depts)
        GROUP BY a.department_name, t.sales_channel_id
        ORDER BY purchase_volume DESC
        """
        df = self.conn.execute(sql).fetchdf()
        df["channel_label"] = df["sales_channel_id"].map(lambda x: CHANNEL_LABELS.get(x, f"Channel {x}"))
        return df

    def get_channel_garment_preferences(self, top_n: int = 15) -> pd.DataFrame:
        """Compares garment groups purchased across channels."""
        sql = f"""
        SELECT
            a.garment_group_name,
            t.sales_channel_id,
            COUNT(*) AS purchase_volume,
            ROUND(AVG(t.price), 6) AS avg_price_index
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        GROUP BY a.garment_group_name, t.sales_channel_id
        ORDER BY purchase_volume DESC
        LIMIT {top_n * 2}
        """
        df = self.conn.execute(sql).fetchdf()
        df["channel_label"] = df["sales_channel_id"].map(lambda x: CHANNEL_LABELS.get(x, f"Channel {x}"))
        return df
