"""
GarmentPulse — Hybrid Fashion Recommender (Module F)
Combines popularity, attribute content matching, and collaborative co-purchase signals.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import duckdb

from src.recommendations.collaborative_recommender import CollaborativeRecommender
from src.recommendations.content_recommender import ContentRecommender
from src.recommendations.popularity_recommender import PopularityRecommender


class HybridRecommender:
    """Ensemble recommender weighting popularity, attribute content, and collaborative filtering."""

    def __init__(
        self,
        conn: duckdb.DuckDBPyConnection,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.conn = conn
        self.weights = weights or {"popularity": 0.20, "content": 0.40, "collaborative": 0.40}
        self.pop_rec = PopularityRecommender(conn)
        self.cnt_rec = ContentRecommender(conn)
        self.col_rec = CollaborativeRecommender(conn)
        self.date_cutoff: Optional[str] = None

    def fit(self, date_cutoff: Optional[str] = None) -> None:
        """Fit all component recommenders using data strictly before date_cutoff."""
        self.date_cutoff = date_cutoff
        self.pop_rec.fit(date_cutoff=date_cutoff)
        self.cnt_rec.fit(date_cutoff=date_cutoff)
        self.col_rec.fit(date_cutoff=date_cutoff)

    def recommend(
        self,
        customer_id: str,
        n: int = 12,
        exclude_purchased: bool = True,
    ) -> List[Dict[str, Any]]:
        """Compute hybrid ranked recommendations."""
        pop_list = self.pop_rec.recommend(customer_id, n=n * 3, exclude_purchased=exclude_purchased)
        cnt_list = self.cnt_rec.recommend(customer_id, n=n * 3, exclude_purchased=exclude_purchased)
        col_list = self.col_rec.recommend(customer_id, n=n * 3, exclude_purchased=exclude_purchased)

        pop_map = {item["article_id"]: (item["score"], item) for item in pop_list}
        cnt_map = {item["article_id"]: (item["score"], item) for item in cnt_list}
        col_map = {item["article_id"]: (item["score"], item) for item in col_list}

        all_ids = set(pop_map.keys()) | set(cnt_map.keys()) | set(col_map.keys())
        scored_items = []

        w_pop = self.weights.get("popularity", 0.20)
        w_cnt = self.weights.get("content", 0.40)
        w_col = self.weights.get("collaborative", 0.40)

        for art_id in all_ids:
            s_pop = pop_map.get(art_id, (0.0, None))[0]
            s_cnt = cnt_map.get(art_id, (0.0, None))[0]
            s_col = col_map.get(art_id, (0.0, None))[0]

            hybrid_score = round(w_pop * s_pop + w_cnt * s_cnt + w_col * s_col, 4)

            # Metadata fallback from whichever recommender had it
            sample_item = pop_map.get(art_id, (None, None))[1] or cnt_map.get(art_id, (None, None))[1] or col_map.get(art_id, (None, None))[1]
            if not sample_item:
                continue

            # Synthesis of commercial explanation
            reasons = []
            if s_cnt > 0.3:
                reasons.append("matches your garment & colour profile")
            if s_col > 0.3:
                reasons.append("frequently bought with items in your closet")
            if s_pop > 0.3:
                reasons.append("trending across community")
            reason_text = " & ".join(reasons) if reasons else "high overall affinity score"

            scored_items.append({
                "article_id": art_id,
                "prod_name": sample_item.get("prod_name", "Fashion Item"),
                "department_name": sample_item.get("department_name", "Department"),
                "product_type_name": sample_item.get("product_type_name", "Product"),
                "colour_group_name": sample_item.get("colour_group_name", "Colour"),
                "avg_price_index": sample_item.get("avg_price_index", 0.0),
                "hybrid_score": hybrid_score,
                "score_components": {
                    "popularity": s_pop,
                    "content": s_cnt,
                    "collaborative": s_col,
                },
                "model": "GarmentPulse Hybrid Engine",
                "reason": f"Recommended because it {reason_text}",
            })

        scored_items.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return scored_items[:n]
