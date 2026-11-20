"""
GarmentPulse — Collaborative Recommender (Module F)
Item-based collaborative filtering via co-purchase affinity graph on historical customer baskets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
import duckdb
import pandas as pd


class CollaborativeRecommender:
    """Recommends products frequently co-purchased with customer's historical items."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
        self.date_cutoff: Optional[str] = None
        self.top_items_pool: List[Dict[str, Any]] = []

    def fit(self, date_cutoff: Optional[str] = None, pool_size: int = 200) -> None:
        """Stores date_cutoff and fetches catalog metadata for candidate items."""
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
        LIMIT {pool_size}
        """
        self.top_items_pool = self.conn.execute(sql).fetchdf().to_dict(orient="records")

    def recommend(
        self,
        customer_id: str,
        n: int = 12,
        exclude_purchased: bool = True,
    ) -> List[Dict[str, Any]]:
        """Finds items co-purchased by other customers who bought the same items as target customer."""
        where_cutoff = f"AND t_dat < '{self.date_cutoff}'" if self.date_cutoff else ""

        # Step 1: Get customer's recently purchased items (up to 5 most recent)
        recent_items_sql = f"""
        SELECT article_id
        FROM transactions
        WHERE customer_id = ? {where_cutoff}
        ORDER BY t_dat DESC
        LIMIT 5
        """
        cust_items = [r[0] for r in self.conn.execute(recent_items_sql, [customer_id]).fetchall()]

        if not cust_items:
            # Fallback to top pool if no history
            return [
                {
                    **dict(item),
                    "score": 0.5,
                    "model": "Collaborative (Cold-start fallback)",
                    "reason": "Frequently bought together by community",
                }
                for item in self.top_items_pool[:n]
            ]

        # Step 2: Query items co-purchased by other customers who bought these items
        placeholders = ", ".join(["?"] * len(cust_items))
        where_filter_cutoff = f"AND t2.t_dat < '{self.date_cutoff}'" if self.date_cutoff else ""

        co_purchase_sql = f"""
        SELECT
            t2.article_id,
            a.prod_name,
            a.department_name,
            a.product_type_name,
            a.colour_group_name,
            COUNT(*) AS co_purchase_count,
            ROUND(AVG(t2.price), 6) AS avg_price_index
        FROM transactions t1
        JOIN transactions t2 ON t1.customer_id = t2.customer_id
        JOIN articles a ON t2.article_id = a.article_id
        WHERE t1.article_id IN ({placeholders})
          AND t2.article_id NOT IN ({placeholders})
          {where_filter_cutoff}
        GROUP BY t2.article_id, a.prod_name, a.department_name, a.product_type_name, a.colour_group_name
        ORDER BY co_purchase_count DESC
        LIMIT {n * 2}
        """
        co_items = self.conn.execute(co_purchase_sql, cust_items + cust_items).fetchdf().to_dict(orient="records")

        # Exclude customer's full historical purchases if requested
        history_sql = f"SELECT DISTINCT article_id FROM transactions WHERE customer_id = ? {where_cutoff}"
        purchased = {r[0] for r in self.conn.execute(history_sql, [customer_id]).fetchall()} if exclude_purchased else set()

        recs = []
        max_co = co_items[0]["co_purchase_count"] if co_items else 1
        for item in co_items:
            if item["article_id"] in purchased:
                continue
            rec = dict(item)
            rec["score"] = round(item["co_purchase_count"] / max_co, 4)
            rec["model"] = "Item-Based Collaborative Filtering"
            rec["reason"] = f"Customers with similar taste frequently co-purchased this ({item['co_purchase_count']:,} times)"
            recs.append(rec)
            if len(recs) >= n:
                break

        # If not enough co-purchases, fill from top pool
        if len(recs) < n and self.top_items_pool:
            for item in self.top_items_pool:
                if item["article_id"] not in purchased and item["article_id"] not in {r["article_id"] for r in recs}:
                    recs.append({
                        **dict(item),
                        "score": 0.4,
                        "model": "Collaborative (Popularity backfill)",
                        "reason": "Popular complementary piece across similar shoppers",
                    })
                if len(recs) >= n:
                    break

        return recs
