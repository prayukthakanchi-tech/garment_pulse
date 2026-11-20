"""
GarmentPulse — Popularity Recommender Baseline (Module F)
Recommends top-selling articles from recent training history not yet purchased by customer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
import duckdb
import pandas as pd


class PopularityRecommender:
    """Baseline recommender ranking items by observed purchase volume."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
        self.popular_items: List[Dict[str, Any]] = []
        self.date_cutoff: Optional[str] = None

    def fit(self, date_cutoff: Optional[str] = None, top_k: int = 100) -> None:
        """Computes top items based on transaction volume strictly before date_cutoff."""
        self.date_cutoff = date_cutoff
        where_sql = f"WHERE t.t_dat < '{date_cutoff}'" if date_cutoff else ""

        sql = f"""
        SELECT
            t.article_id,
            a.prod_name,
            a.department_name,
            a.product_type_name,
            a.colour_group_name,
            COUNT(*) AS purchase_volume,
            ROUND(AVG(t.price), 6) AS avg_price_index
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        {where_sql}
        GROUP BY t.article_id, a.prod_name, a.department_name, a.product_type_name, a.colour_group_name
        ORDER BY purchase_volume DESC
        LIMIT {top_k}
        """
        df = self.conn.execute(sql).fetchdf()
        self.popular_items = df.to_dict(orient="records")

    def get_customer_history(self, customer_id: str) -> Set[str]:
        """Returns set of article_ids already purchased by customer before date_cutoff."""
        where_cutoff = f"AND t_dat < '{self.date_cutoff}'" if self.date_cutoff else ""
        sql = f"""
        SELECT DISTINCT article_id
        FROM transactions
        WHERE customer_id = ? {where_cutoff}
        """
        rows = self.conn.execute(sql, [customer_id]).fetchall()
        return {r[0] for r in rows}

    def recommend(
        self,
        customer_id: str,
        n: int = 12,
        exclude_purchased: bool = True,
    ) -> List[Dict[str, Any]]:
        """Return top N popular items for a customer."""
        if not self.popular_items:
            self.fit()

        purchased = self.get_customer_history(customer_id) if exclude_purchased else set()
        recommendations = []

        max_vol = self.popular_items[0]["purchase_volume"] if self.popular_items else 1
        for item in self.popular_items:
            if item["article_id"] in purchased:
                continue
            rec = dict(item)
            rec["score"] = round(item["purchase_volume"] / max_vol, 4)
            rec["model"] = "Popularity Baseline"
            rec["reason"] = f"Top trending item across platform with {item['purchase_volume']:,} historical purchases"
            recommendations.append(rec)
            if len(recommendations) >= n:
                break

        return recommendations
