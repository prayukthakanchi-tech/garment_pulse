"""
GarmentPulse — Recommendation Chronological Evaluator (Module F)
Strict chronological backtest evaluating MAP@12, Recall@12, Precision@12, and Coverage.
NO RANDOM TRAIN-TEST SPLITS PERMITTED.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set
import duckdb
import pandas as pd


class RecommendationEvaluator:
    """Evaluates recommendation algorithms using strict chronological holdout splits."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def get_chronological_split(self, holdout_days: int = 28) -> Dict[str, Any]:
        """Identifies cutoff date: train is everything before cutoff, validation is holdout period."""
        max_date = self.conn.execute("SELECT MAX(t_dat) FROM transactions").fetchone()[0]
        cutoff_date = self.conn.execute(
            f"SELECT CAST(MAX(t_dat) - INTERVAL '{holdout_days}' DAY AS VARCHAR) FROM transactions"
        ).fetchone()[0]

        return {
            "max_date": str(max_date),
            "cutoff_date": str(cutoff_date),
            "holdout_days": holdout_days,
        }

    def evaluate_model(
        self,
        recommender,
        sample_customers: int = 100,
        k: int = 12,
        holdout_days: int = 28,
    ) -> Dict[str, Any]:
        """Evaluates a recommender against actual future purchases in the chronological holdout window."""
        split = self.get_chronological_split(holdout_days=holdout_days)
        cutoff = split["cutoff_date"]

        # Fit model strictly on pre-cutoff data
        recommender.fit(date_cutoff=cutoff)

        # Get test customers who purchased in holdout period AND had prior history in training period
        test_cust_sql = f"""
        WITH train_custs AS (
            SELECT DISTINCT customer_id FROM transactions WHERE t_dat < '{cutoff}'
        ),
        val_custs AS (
            SELECT
                t.customer_id,
                LIST(DISTINCT t.article_id) AS actual_purchased
            FROM transactions t
            JOIN train_custs tc ON t.customer_id = tc.customer_id
            WHERE t.t_dat >= '{cutoff}'
            GROUP BY t.customer_id
            HAVING COUNT(DISTINCT t.article_id) >= 1
            LIMIT {sample_customers}
        )
        SELECT * FROM val_custs
        """
        test_cases = self.conn.execute(test_cust_sql).fetchall()

        if not test_cases:
            return {"error": "Insufficient validation test cases."}

        precisions, recalls, aps = [], [], []
        all_recommended_articles: Set[str] = set()

        for row in test_cases:
            cust_id = row[0]
            actual_items = set(row[1])

            recs = recommender.recommend(cust_id, n=k, exclude_purchased=True)
            rec_ids = [item["article_id"] for item in recs]
            all_recommended_articles.update(rec_ids)

            # Precision & Recall @ K
            hits = [1 if item_id in actual_items else 0 for item_id in rec_ids]
            hit_count = sum(hits)

            p_at_k = hit_count / k if k > 0 else 0.0
            r_at_k = hit_count / len(actual_items) if actual_items else 0.0

            # Average Precision @ K (MAP@K component)
            score = 0.0
            num_hits = 0
            for i, hit in enumerate(hits):
                if hit:
                    num_hits += 1
                    score += num_hits / (i + 1)
            ap_at_k = score / min(len(actual_items), k) if actual_items else 0.0

            precisions.append(p_at_k)
            recalls.append(r_at_k)
            aps.append(ap_at_k)

        # Catalog coverage
        total_active_art = self.conn.execute(
            f"SELECT COUNT(DISTINCT article_id) FROM transactions WHERE t_dat < '{cutoff}'"
        ).fetchone()[0]
        coverage_pct = round(len(all_recommended_articles) * 100.0 / total_active_art, 2)

        return {
            "model_evaluated": getattr(recommender, "__class__", type(recommender)).__name__,
            "validation_window": f"{split['cutoff_date']} to {split['max_date']}",
            "customers_evaluated": len(test_cases),
            "k": k,
            "map_at_k": round(sum(aps) / len(aps), 4) if aps else 0.0,
            "recall_at_k": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
            "precision_at_k": round(sum(precisions) / len(precisions), 4) if precisions else 0.0,
            "catalog_coverage_pct": coverage_pct,
            "distinct_articles_recommended": len(all_recommended_articles),
        }

    def compare_all_models(self, sample_customers: int = 50) -> pd.DataFrame:
        """Run chronological backtest comparison across all recommendation approaches."""
        from src.recommendations.popularity_recommender import PopularityRecommender
        from src.recommendations.content_recommender import ContentRecommender
        from src.recommendations.collaborative_recommender import CollaborativeRecommender
        from src.recommendations.hybrid_recommender import HybridRecommender

        models = [
            ("Popularity Baseline", PopularityRecommender(self.conn)),
            ("Content-Based Engine", ContentRecommender(self.conn)),
            ("Collaborative Filtering", CollaborativeRecommender(self.conn)),
            ("GarmentPulse Hybrid", HybridRecommender(self.conn)),
        ]

        rows = []
        for name, m in models:
            metrics = self.evaluate_model(m, sample_customers=sample_customers, k=12)
            rows.append({
                "Model Architecture": name,
                "MAP@12": metrics.get("map_at_k", 0.0),
                "Recall@12": metrics.get("recall_at_k", 0.0),
                "Precision@12": metrics.get("precision_at_k", 0.0),
                "Catalogue Coverage (%)": metrics.get("catalog_coverage_pct", 0.0),
                "Distinct Items Reco'd": metrics.get("distinct_articles_recommended", 0),
            })
        return pd.DataFrame(rows)
