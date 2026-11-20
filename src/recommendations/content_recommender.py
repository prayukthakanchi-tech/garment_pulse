"""
GarmentPulse — Content-Based Recommender (Module F)
Matches customer attribute preferences (garment groups, colours, departments) with catalogue items.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Set
import duckdb
import pandas as pd


class ContentRecommender:
    """Recommends products whose attributes match the customer's historical purchase profile."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn
        self.date_cutoff: Optional[str] = None
        self.candidate_items: List[Dict[str, Any]] = []

    def fit(self, date_cutoff: Optional[str] = None, candidate_pool_size: int = 500) -> None:
        """Prepares the active candidate item pool strictly before date_cutoff."""
        self.date_cutoff = date_cutoff
        where_sql = f"WHERE t.t_dat < '{date_cutoff}'" if date_cutoff else ""

        # Pool of active articles with attributes and volume
        sql = f"""
        SELECT
            t.article_id,
            a.prod_name,
            a.department_name,
            a.product_type_name,
            a.garment_group_name,
            a.colour_group_name,
            a.section_name,
            COUNT(*) AS purchase_volume,
            ROUND(AVG(t.price), 6) AS avg_price_index
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        {where_sql}
        GROUP BY
            t.article_id, a.prod_name, a.department_name, a.product_type_name,
            a.garment_group_name, a.colour_group_name, a.section_name
        ORDER BY purchase_volume DESC
        LIMIT {candidate_pool_size}
        """
        self.candidate_items = self.conn.execute(sql).fetchdf().to_dict(orient="records")

    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Extracts customer attribute affinities from purchase history."""
        where_cutoff = f"AND t.t_dat < '{self.date_cutoff}'" if self.date_cutoff else ""
        sql = f"""
        SELECT
            a.department_name,
            a.garment_group_name,
            a.colour_group_name,
            a.product_type_name,
            a.section_name,
            COUNT(*) AS weight
        FROM transactions t
        JOIN articles a ON t.article_id = a.article_id
        WHERE t.customer_id = ? {where_cutoff}
        GROUP BY
            a.department_name, a.garment_group_name, a.colour_group_name,
            a.product_type_name, a.section_name
        """
        rows = self.conn.execute(sql, [customer_id]).fetchall()
        if not rows:
            return {}

        dept_counter = Counter()
        garment_counter = Counter()
        colour_counter = Counter()
        type_counter = Counter()

        for r in rows:
            w = r[5]
            dept_counter[r[0]] += w
            garment_counter[r[1]] += w
            colour_counter[r[2]] += w
            type_counter[r[3]] += w

        total_w = sum(dept_counter.values()) or 1
        return {
            "departments": {k: v / total_w for k, v in dept_counter.items()},
            "garments": {k: v / total_w for k, v in garment_counter.items()},
            "colours": {k: v / total_w for k, v in colour_counter.items()},
            "types": {k: v / total_w for k, v in type_counter.items()},
            "top_dept": dept_counter.most_common(1)[0][0] if dept_counter else None,
            "top_colour": colour_counter.most_common(1)[0][0] if colour_counter else None,
            "top_garment": garment_counter.most_common(1)[0][0] if garment_counter else None,
        }

    def recommend(
        self,
        customer_id: str,
        n: int = 12,
        exclude_purchased: bool = True,
    ) -> List[Dict[str, Any]]:
        """Score candidate items against customer attribute profile."""
        if not self.candidate_items:
            self.fit()

        profile = self.get_customer_profile(customer_id)
        if not profile:
            # Cold start fallback to top candidates
            return [
                {
                    **dict(item),
                    "score": 0.5,
                    "model": "Content-Based (Cold-start fallback)",
                    "reason": "Popular fashion staple across catalogue",
                }
                for item in self.candidate_items[:n]
            ]

        # Get history to exclude
        where_cutoff = f"AND t_dat < '{self.date_cutoff}'" if self.date_cutoff else ""
        sql = f"SELECT DISTINCT article_id FROM transactions WHERE customer_id = ? {where_cutoff}"
        purchased = {r[0] for r in self.conn.execute(sql, [customer_id]).fetchall()} if exclude_purchased else set()

        scored = []
        for item in self.candidate_items:
            if item["article_id"] in purchased:
                continue

            # Multi-attribute similarity weighting
            d_score = profile["departments"].get(item["department_name"], 0.0)
            g_score = profile["garments"].get(item["garment_group_name"], 0.0)
            c_score = profile["colours"].get(item["colour_group_name"], 0.0)
            t_score = profile["types"].get(item["product_type_name"], 0.0)

            # Weighted combination of attribute alignments
            sim = 0.35 * d_score + 0.30 * g_score + 0.20 * c_score + 0.15 * t_score

            matches = []
            if d_score > 0:
                matches.append(item["department_name"])
            if g_score > 0:
                matches.append(item["garment_group_name"])
            if c_score > 0:
                matches.append(item["colour_group_name"])

            rec = dict(item)
            rec["score"] = round(sim, 4)
            rec["model"] = "Content-Based Recommender"
            rec["matching_attributes"] = matches
            rec["reason"] = f"Matches your preferred {', '.join(matches[:2]) if matches else 'style profile'}"
            scored.append(rec)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:n]
