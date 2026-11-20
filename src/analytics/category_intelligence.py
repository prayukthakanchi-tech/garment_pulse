"""
GarmentPulse — Category Intelligence Engine (Module A)
Evaluates fashion category performance, momentum, concentration, and growth.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import duckdb
import pandas as pd

from config.settings import (
    MIN_CATEGORY_CUSTOMERS,
    MIN_CATEGORY_TRANSACTIONS,
    PREVIOUS_PERIOD_WEEKS,
    RECENT_PERIOD_WEEKS,
)


class CategoryIntelligence:
    """Engine for fashion category analytics across hierarchical levels."""

    VALID_LEVELS = {
        "department": "department_name",
        "department_name": "department_name",
        "section": "section_name",
        "section_name": "section_name",
        "product_group": "product_group_name",
        "product_group_name": "product_group_name",
        "garment_group": "garment_group_name",
        "garment_group_name": "garment_group_name",
        "product_type": "product_type_name",
        "product_type_name": "product_type_name",
    }

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def _resolve_level(self, level: str) -> str:
        col = self.VALID_LEVELS.get(level.lower().strip())
        if not col:
            raise ValueError(f"Invalid category level '{level}'. Must be one of {list(self.VALID_LEVELS.keys())}")
        return col

    def get_category_performance(
        self,
        level: str = "department",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_transactions: int = MIN_CATEGORY_TRANSACTIONS,
    ) -> pd.DataFrame:
        """Calculate volume, unique customers, product breadth, volume share, avg price, concentration."""
        col = self._resolve_level(level)

        where_clauses = ["t.article_id = a.article_id"]
        if date_from:
            where_clauses.append(f"t.t_dat >= '{date_from}'")
        if date_to:
            where_clauses.append(f"t.t_dat <= '{date_to}'")
        where_sql = " AND ".join(where_clauses)

        sql = f"""
        WITH category_totals AS (
            SELECT
                a.{col} AS category_name,
                COUNT(*) AS purchase_volume,
                COUNT(DISTINCT t.customer_id) AS unique_customers,
                COUNT(DISTINCT t.article_id) AS active_articles,
                AVG(t.price) AS avg_normalised_price,
                SUM(t.price) AS price_index_contribution
            FROM transactions t, articles a
            WHERE {where_sql}
            GROUP BY a.{col}
            HAVING COUNT(*) >= {min_transactions}
        ),
        article_shares AS (
            SELECT
                a.{col} AS category_name,
                t.article_id,
                COUNT(*) AS art_vol,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY a.{col}) AS art_share_pct
            FROM transactions t, articles a
            WHERE {where_sql}
            GROUP BY a.{col}, t.article_id
        ),
        concentration AS (
            SELECT
                category_name,
                ROUND(SUM(art_share_pct * art_share_pct), 1) AS hhi_concentration
            FROM article_shares
            GROUP BY category_name
        )
        SELECT
            ct.category_name,
            ct.purchase_volume,
            ct.unique_customers,
            ct.active_articles,
            ROUND(ct.avg_normalised_price, 6) AS avg_normalised_price,
            ROUND(ct.price_index_contribution, 4) AS price_index_contribution,
            ROUND(ct.purchase_volume * 100.0 / SUM(ct.purchase_volume) OVER (), 2) AS volume_share_pct,
            COALESCE(conc.hhi_concentration, 0.0) AS hhi_concentration,
            CASE
                WHEN conc.hhi_concentration > 2500 THEN 'High Concentration'
                WHEN conc.hhi_concentration > 1500 THEN 'Moderate Concentration'
                ELSE 'Broad Assortment'
            END AS concentration_tier
        FROM category_totals ct
        LEFT JOIN concentration conc ON ct.category_name = conc.category_name
        ORDER BY ct.purchase_volume DESC
        """
        return self.conn.execute(sql).fetchdf()

    def get_category_growth(
        self,
        level: str = "department",
        recent_weeks: int = RECENT_PERIOD_WEEKS,
        prev_weeks: int = PREVIOUS_PERIOD_WEEKS,
        min_transactions: int = MIN_CATEGORY_TRANSACTIONS,
    ) -> pd.DataFrame:
        """Calculate period-over-period purchase volume growth and customer momentum."""
        col = self._resolve_level(level)
        recent_days = recent_weeks * 7
        total_days = (recent_weeks + prev_weeks) * 7

        sql = f"""
        WITH bounds AS (
            SELECT MAX(t_dat) AS max_date FROM transactions
        ),
        period_tx AS (
            SELECT
                a.{col} AS category_name,
                COUNT(CASE WHEN t.t_dat > b.max_date - INTERVAL '{recent_days}' DAY THEN 1 END) AS recent_volume,
                COUNT(CASE WHEN t.t_dat <= b.max_date - INTERVAL '{recent_days}' DAY 
                           AND t.t_dat > b.max_date - INTERVAL '{total_days}' DAY THEN 1 END) AS prev_volume,
                COUNT(DISTINCT CASE WHEN t.t_dat > b.max_date - INTERVAL '{recent_days}' DAY THEN t.customer_id END) AS recent_customers,
                COUNT(DISTINCT CASE WHEN t.t_dat <= b.max_date - INTERVAL '{recent_days}' DAY 
                                    AND t.t_dat > b.max_date - INTERVAL '{total_days}' DAY THEN t.customer_id END) AS prev_customers
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            CROSS JOIN bounds b
            WHERE t.t_dat > b.max_date - INTERVAL '{total_days}' DAY
            GROUP BY a.{col}
            HAVING (COUNT(CASE WHEN t.t_dat > b.max_date - INTERVAL '{recent_days}' DAY THEN 1 END) +
                    COUNT(CASE WHEN t.t_dat <= b.max_date - INTERVAL '{recent_days}' DAY 
                               AND t.t_dat > b.max_date - INTERVAL '{total_days}' DAY THEN 1 END)) >= {min_transactions}
        )
        SELECT
            category_name,
            recent_volume,
            prev_volume,
            recent_customers,
            prev_customers,
            CASE 
                WHEN prev_volume > 0 THEN ROUND((recent_volume - prev_volume) * 100.0 / prev_volume, 2)
                ELSE NULL
            END AS volume_growth_pct,
            CASE
                WHEN prev_customers > 0 THEN ROUND((recent_customers - prev_customers) * 100.0 / prev_customers, 2)
                ELSE NULL
            END AS customer_growth_pct,
            CASE
                WHEN prev_volume > 0 AND ((recent_volume - prev_volume) * 1.0 / prev_volume) >= 0.15 THEN 'Accelerating Demand'
                WHEN prev_volume > 0 AND ((recent_volume - prev_volume) * 1.0 / prev_volume) <= -0.15 THEN 'Declining Demand'
                ELSE 'Stable Velocity'
            END AS momentum_signal
        FROM period_tx
        ORDER BY volume_growth_pct DESC NULLS LAST
        """
        return self.conn.execute(sql).fetchdf()

    def get_category_trends(
        self,
        category_name: str,
        level: str = "department",
        freq: str = "week",
    ) -> pd.DataFrame:
        """Return weekly or monthly time series for a specified category."""
        col = self._resolve_level(level)
        trunc_unit = "week" if freq == "week" else "month"

        sql = f"""
        SELECT
            DATE_TRUNC('{trunc_unit}', t.t_dat) AS period_date,
            COUNT(*) AS purchase_volume,
            COUNT(DISTINCT t.customer_id) AS unique_customers,
            COUNT(DISTINCT t.article_id) AS active_articles,
            AVG(t.price) AS avg_normalised_price
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        WHERE a.{col} = ?
        GROUP BY DATE_TRUNC('{trunc_unit}', t.t_dat)
        ORDER BY period_date ASC
        """
        return self.conn.execute(sql, [category_name]).fetchdf()

    def get_top_growing_categories(self, level: str = "department", n: int = 10) -> pd.DataFrame:
        """Top growing categories with minimum volume filter."""
        df = self.get_category_growth(level=level)
        return df.dropna(subset=["volume_growth_pct"]).head(n)

    def get_declining_categories(self, level: str = "department", n: int = 10) -> pd.DataFrame:
        """Top declining categories with minimum volume filter."""
        df = self.get_category_growth(level=level)
        return df.dropna(subset=["volume_growth_pct"]).tail(n).iloc[::-1]

    def get_yoy_comparison(self, level: str = "department") -> pd.DataFrame:
        """Compare same calendar month across available years."""
        col = self._resolve_level(level)
        sql = f"""
        WITH monthly AS (
            SELECT
                a.{col} AS category_name,
                YEAR(t.t_dat) AS yr,
                MONTH(t.t_dat) AS mo,
                COUNT(*) AS volume
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            GROUP BY a.{col}, YEAR(t.t_dat), MONTH(t.t_dat)
        )
        SELECT
            m19.category_name,
            m19.mo AS calendar_month,
            m18.volume AS volume_2018,
            m19.volume AS volume_2019,
            m20.volume AS volume_2020,
            CASE
                WHEN m18.volume > 0 THEN ROUND((m19.volume - m18.volume) * 100.0 / m18.volume, 2)
                ELSE NULL
            END AS yoy_growth_2019_vs_2018_pct
        FROM (SELECT * FROM monthly WHERE yr = 2019) m19
        LEFT JOIN (SELECT * FROM monthly WHERE yr = 2018) m18 
            ON m19.category_name = m18.category_name AND m19.mo = m18.mo
        LEFT JOIN (SELECT * FROM monthly WHERE yr = 2020) m20 
            ON m19.category_name = m20.category_name AND m19.mo = m20.mo
        WHERE COALESCE(m18.volume, 0) + m19.volume >= 1000
        ORDER BY yoy_growth_2019_vs_2018_pct DESC NULLS LAST
        """
        return self.conn.execute(sql).fetchdf()
