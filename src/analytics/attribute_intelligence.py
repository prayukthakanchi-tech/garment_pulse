"""
GarmentPulse — Fashion Attribute Intelligence Engine (Module B)
Analyzes colours, garment groups, graphical appearances, and cross-attribute trends.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import duckdb
import pandas as pd


class AttributeIntelligence:
    """Engine for fashion design attribute analytics (colours, garment groups, styles)."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def get_colour_performance(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_transactions: int = 500,
    ) -> pd.DataFrame:
        """Colour group performance ranking by volume, customers, and price index."""
        where_clauses = ["t.article_id = a.article_id"]
        if date_from:
            where_clauses.append(f"t.t_dat >= '{date_from}'")
        if date_to:
            where_clauses.append(f"t.t_dat <= '{date_to}'")
        where_sql = " AND ".join(where_clauses)

        sql = f"""
        SELECT
            a.colour_group_name,
            COUNT(*) AS purchase_volume,
            COUNT(DISTINCT t.customer_id) AS unique_customers,
            COUNT(DISTINCT t.article_id) AS active_articles,
            ROUND(AVG(t.price), 6) AS avg_normalised_price,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS volume_share_pct
        FROM transactions t, articles a
        WHERE {where_sql}
        GROUP BY a.colour_group_name
        HAVING COUNT(*) >= {min_transactions}
        ORDER BY purchase_volume DESC
        """
        return self.conn.execute(sql).fetchdf()

    def get_garment_group_trends(self, freq: str = "month") -> pd.DataFrame:
        """Garment group purchase volume trends over time."""
        trunc = "month" if freq == "month" else "week"
        sql = f"""
        SELECT
            DATE_TRUNC('{trunc}', t.t_dat) AS period_date,
            a.garment_group_name,
            COUNT(*) AS purchase_volume
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        GROUP BY DATE_TRUNC('{trunc}', t.t_dat), a.garment_group_name
        ORDER BY period_date ASC, purchase_volume DESC
        """
        return self.conn.execute(sql).fetchdf()

    def get_attribute_growth_rankings(
        self,
        attribute: str = "colour_group_name",
        recent_days: int = 28,
        prev_days: int = 28,
        min_volume: int = 500,
    ) -> pd.DataFrame:
        """Growth rate ranking for any article attribute."""
        valid_cols = {
            "colour_group_name", "garment_group_name", "product_group_name",
            "graphical_appearance_name", "perceived_colour_value_name", "product_type_name"
        }
        if attribute not in valid_cols:
            raise ValueError(f"Attribute must be one of {valid_cols}")

        total_days = recent_days + prev_days
        sql = f"""
        WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
        volumes AS (
            SELECT
                a.{attribute} AS attribute_value,
                COUNT(CASE WHEN t.t_dat > b.max_date - INTERVAL '{recent_days}' DAY THEN 1 END) AS recent_vol,
                COUNT(CASE WHEN t.t_dat <= b.max_date - INTERVAL '{recent_days}' DAY 
                           AND t.t_dat > b.max_date - INTERVAL '{total_days}' DAY THEN 1 END) AS prev_vol
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            CROSS JOIN bounds b
            WHERE t.t_dat > b.max_date - INTERVAL '{total_days}' DAY
            GROUP BY a.{attribute}
            HAVING (COUNT(CASE WHEN t.t_dat > b.max_date - INTERVAL '{recent_days}' DAY THEN 1 END) +
                    COUNT(CASE WHEN t.t_dat <= b.max_date - INTERVAL '{recent_days}' DAY 
                               AND t.t_dat > b.max_date - INTERVAL '{total_days}' DAY THEN 1 END)) >= {min_volume}
        )
        SELECT
            attribute_value,
            recent_vol,
            prev_vol,
            CASE
                WHEN prev_vol > 0 THEN ROUND((recent_vol - prev_vol) * 100.0 / prev_vol, 2)
                ELSE NULL
            END AS growth_pct
        FROM volumes
        ORDER BY growth_pct DESC NULLS LAST
        """
        return self.conn.execute(sql).fetchdf()

    def get_colour_garment_combinations(self, top_n: int = 25) -> pd.DataFrame:
        """Most frequent colour and garment group pairings in actual purchasing."""
        sql = f"""
        SELECT
            a.colour_group_name,
            a.garment_group_name,
            COUNT(*) AS purchase_volume,
            COUNT(DISTINCT t.customer_id) AS unique_customers,
            ROUND(AVG(t.price), 6) AS avg_normalised_price
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        GROUP BY a.colour_group_name, a.garment_group_name
        ORDER BY purchase_volume DESC
        LIMIT {top_n}
        """
        return self.conn.execute(sql).fetchdf()

    def get_department_attribute_heatmap(
        self,
        attribute: str = "colour_group_name",
        top_depts: int = 12,
        top_attrs: int = 12,
    ) -> pd.DataFrame:
        """Cross-tabulation of top departments vs top attributes for heatmap rendering."""
        sql = f"""
        WITH top_d AS (
            SELECT department_name FROM articles a
            JOIN transactions t ON a.article_id = t.article_id
            GROUP BY department_name ORDER BY COUNT(*) DESC LIMIT {top_depts}
        ),
        top_a AS (
            SELECT {attribute} FROM articles a
            JOIN transactions t ON a.article_id = t.article_id
            GROUP BY {attribute} ORDER BY COUNT(*) DESC LIMIT {top_attrs}
        )
        SELECT
            a.department_name,
            a.{attribute} AS attribute_value,
            COUNT(*) AS purchase_volume
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        WHERE a.department_name IN (SELECT department_name FROM top_d)
          AND a.{attribute} IN (SELECT {attribute} FROM top_a)
        GROUP BY a.department_name, a.{attribute}
        ORDER BY a.department_name, purchase_volume DESC
        """
        return self.conn.execute(sql).fetchdf()

    def get_product_type_contribution(self, department: Optional[str] = None, top_n: int = 20) -> pd.DataFrame:
        """Product type breakdown with volume, share, and active article variety."""
        where_clause = f"WHERE a.department_name = '{department}'" if department else ""
        sql = f"""
        SELECT
            a.product_type_name,
            a.product_group_name,
            COUNT(*) AS purchase_volume,
            COUNT(DISTINCT t.customer_id) AS unique_customers,
            COUNT(DISTINCT t.article_id) AS active_articles,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS volume_share_pct
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        {where_clause}
        GROUP BY a.product_type_name, a.product_group_name
        ORDER BY purchase_volume DESC
        LIMIT {top_n}
        """
        return self.conn.execute(sql).fetchdf()
