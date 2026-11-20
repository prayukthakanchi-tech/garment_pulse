"""
GarmentPulse — Product Lifecycle Intelligence Engine (Module D)
Analyzes article-level performance, velocities, observation windows, and lifecycle stages.
NOTE: First observed purchase != launch date. Last observed != discontinuation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import duckdb
import pandas as pd

from config.settings import (
    ACCELERATION_THRESHOLD,
    DECLINE_THRESHOLD,
    MIN_PRODUCT_PURCHASES,
)


def _is_prod_db(conn: duckdb.DuckDBPyConnection) -> bool:
    try:
        db_list = conn.execute("PRAGMA database_list;").fetchall()
        return any(row[2] and "garmentpulse.duckdb" in str(row[2]).lower() for row in db_list)
    except Exception:
        return False


class ProductIntelligence:
    """Evaluates individual article sales velocity, lifecycle status, and demand trajectories."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def get_product_performance(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "purchase_volume",
        ascending: bool = False,
        department: Optional[str] = None,
        product_group: Optional[str] = None,
        search: Optional[str] = None,
        lifecycle_filter: Optional[str] = None,
    ) -> pd.DataFrame:
        """Paginated, searchable article-level performance table."""
        import os
        parquet_file = "data/processed/agg_article_performance.parquet"
        if _is_prod_db(self.conn) and os.path.exists(parquet_file):
            where_clauses = ["1=1"]
            params = []
            if department:
                where_clauses.append("department_name = ?")
                params.append(department)
            if product_group:
                where_clauses.append("garment_group_name = ?")
                params.append(product_group)
            if search:
                where_clauses.append("(LOWER(prod_name) LIKE ? OR article_id LIKE ?)")
                params.extend([f"%{search.lower()}%", f"%{search}%"])
            if lifecycle_filter and lifecycle_filter != "All":
                where_clauses.append("lifecycle_status = ?")
                params.append(lifecycle_filter)

            where_sql = " AND ".join(where_clauses)
            sort_dir = "ASC" if ascending else "DESC"
            allowed_sorts = {
                "purchase_volume": "total_purchase_lines",
                "unique_customers": "unique_customers",
                "recent_volume": "recent_4wk_volume",
                "growth_rate": "volume_growth_rate",
                "avg_price": "avg_price_index",
            }
            order_col = allowed_sorts.get(sort_by, "total_purchase_lines")

            sql = f"""
            SELECT *
            FROM read_parquet('{parquet_file}')
            WHERE {where_sql}
            ORDER BY {order_col} {sort_dir} NULLS LAST
            LIMIT {limit} OFFSET {offset}
            """
            return self.conn.execute(sql, params).fetchdf()

        where_clauses = ["1=1"]
        params = []

        if department:
            where_clauses.append("a.department_name = ?")
            params.append(department)
        if product_group:
            where_clauses.append("a.product_group_name = ?")
            params.append(product_group)
        if search:
            where_clauses.append("(LOWER(a.prod_name) LIKE ? OR a.article_id LIKE ?)")
            params.extend([f"%{search.lower()}%", f"%{search}%"])

        where_sql = " AND ".join(where_clauses)
        sort_dir = "ASC" if ascending else "DESC"

        allowed_sorts = {
            "purchase_volume": "total_purchase_lines",
            "unique_customers": "unique_customers",
            "recent_volume": "recent_4wk_volume",
            "growth_rate": "volume_growth_rate",
            "avg_price": "avg_price_index",
        }
        order_col = allowed_sorts.get(sort_by, "total_purchase_lines")

        having_clause = ""
        if lifecycle_filter and lifecycle_filter != "All":
            having_clause = f"HAVING lifecycle_status = '{lifecycle_filter}'"

        sql = f"""
        WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
        periods AS (
            SELECT
                max_date,
                max_date - INTERVAL 28 DAYS AS recent_start,
                max_date - INTERVAL 56 DAYS AS prev_start,
                max_date - INTERVAL 56 DAYS AS emerging_cutoff
            FROM bounds
        ),
        article_agg AS (
            SELECT
                t.article_id,
                a.prod_name,
                a.product_type_name,
                a.department_name,
                a.garment_group_name,
                a.colour_group_name,
                MIN(t.t_dat) AS first_observed_purchase,
                MAX(t.t_dat) AS last_observed_purchase,
                COUNT(DISTINCT DATE_TRUNC('week', t.t_dat)) AS active_weeks,
                COUNT(*) AS total_purchase_lines,
                COUNT(DISTINCT t.customer_id) AS unique_customers,
                ROUND(AVG(t.price), 6) AS avg_price_index,
                COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) AS recent_4wk_volume,
                COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END) AS prev_4wk_volume,
                CASE
                    WHEN COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END) > 0 THEN
                        ROUND((COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) - 
                               COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END)) * 1.0 / 
                              COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END), 4)
                    WHEN COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) > 0 THEN 1.0
                    ELSE 0.0
                END AS volume_growth_rate,
                CASE
                    WHEN COUNT(*) < {MIN_PRODUCT_PURCHASES} THEN 'Low Activity'
                    WHEN MIN(t.t_dat) > (SELECT emerging_cutoff FROM periods)
                         AND COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) >= 5 THEN 'Emerging'
                    WHEN COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END) > 0
                         AND ((COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) - 
                               COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END)) * 1.0 / 
                              COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END)) > {ACCELERATION_THRESHOLD}
                         AND COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) >= 5 THEN 'Accelerating'
                    WHEN COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END) > 0
                         AND ((COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) - 
                               COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END)) * 1.0 / 
                              COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END)) < {DECLINE_THRESHOLD} THEN 'Slowing'
                    ELSE 'Stable'
                END AS lifecycle_status
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            CROSS JOIN periods p
            WHERE {where_sql}
            GROUP BY
                t.article_id, a.prod_name, a.product_type_name,
                a.department_name, a.garment_group_name, a.colour_group_name
            {having_clause}
        )
        SELECT *
        FROM article_agg
        ORDER BY {order_col} {sort_dir}
        LIMIT {limit} OFFSET {offset}
        """
        return self.conn.execute(sql, params).fetchdf()

    def get_product_classifications(self) -> pd.DataFrame:
        """Returns distribution counts across lifecycle categories."""
        import os
        parquet_file = "data/processed/agg_article_performance.parquet"
        if _is_prod_db(self.conn) and os.path.exists(parquet_file):
            sql = f"""
            SELECT
                lifecycle_status,
                COUNT(*) AS article_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_pct
            FROM read_parquet('{parquet_file}')
            GROUP BY lifecycle_status
            ORDER BY article_count DESC
            """
            return self.conn.execute(sql).fetchdf()

        sql = f"""
        WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
        periods AS (
            SELECT
                max_date,
                max_date - INTERVAL 28 DAYS AS recent_start,
                max_date - INTERVAL 56 DAYS AS prev_start,
                max_date - INTERVAL 56 DAYS AS emerging_cutoff
            FROM bounds
        ),
        classified AS (
            SELECT
                t.article_id,
                CASE
                    WHEN COUNT(*) < {MIN_PRODUCT_PURCHASES} THEN 'Low Activity'
                    WHEN MIN(t.t_dat) > (SELECT emerging_cutoff FROM periods)
                         AND COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) >= 5 THEN 'Emerging'
                    WHEN COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END) > 0
                         AND ((COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) - 
                               COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END)) * 1.0 / 
                              COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END)) > {ACCELERATION_THRESHOLD}
                         AND COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) >= 5 THEN 'Accelerating'
                    WHEN COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END) > 0
                         AND ((COUNT(CASE WHEN t.t_dat > p.recent_start THEN 1 END) - 
                               COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END)) * 1.0 / 
                              COUNT(CASE WHEN t.t_dat <= p.recent_start AND t.t_dat > p.prev_start THEN 1 END)) < {DECLINE_THRESHOLD} THEN 'Slowing'
                    ELSE 'Stable'
                END AS lifecycle_status
            FROM transactions t
            CROSS JOIN periods p
            GROUP BY t.article_id
        )
        SELECT
            lifecycle_status,
            COUNT(*) AS article_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS share_pct
        FROM classified
        GROUP BY lifecycle_status
        ORDER BY article_count DESC
        """
        return self.conn.execute(sql).fetchdf()

    def get_emerging_products(self, n: int = 15) -> pd.DataFrame:
        """Top emerging articles."""
        return self.get_product_performance(limit=n, lifecycle_filter="Emerging", sort_by="recent_volume")

    def get_accelerating_products(self, n: int = 15) -> pd.DataFrame:
        """Top accelerating articles."""
        return self.get_product_performance(limit=n, lifecycle_filter="Accelerating", sort_by="growth_rate")

    def get_slowing_products(self, n: int = 15) -> pd.DataFrame:
        """Top slowing articles."""
        return self.get_product_performance(limit=n, lifecycle_filter="Slowing", sort_by="growth_rate", ascending=True)

    def get_product_trends(self, article_id: str) -> pd.DataFrame:
        """Weekly purchase history for a specific article."""
        sql = """
        SELECT
            DATE_TRUNC('week', t_dat) AS week_date,
            COUNT(*) AS purchase_volume,
            COUNT(DISTINCT customer_id) AS unique_customers,
            AVG(price) AS avg_price_index
        FROM transactions
        WHERE article_id = ?
        GROUP BY DATE_TRUNC('week', t_dat)
        ORDER BY week_date ASC
        """
        return self.conn.execute(sql, [article_id]).fetchdf()
