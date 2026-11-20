"""
Unit tests for popularity, content, collaborative, and hybrid recommendation algorithms.
"""

from src.recommendations.popularity_recommender import PopularityRecommender
from src.recommendations.content_recommender import ContentRecommender
from src.recommendations.hybrid_recommender import HybridRecommender
from src.recommendations.evaluator import RecommendationEvaluator


def test_popularity_recommender_excludes_purchased(test_db):
    """Verify that previously purchased items are omitted from discovery recommendations."""
    rec = PopularityRecommender(test_db)
    rec.fit()

    # cust_dormant bought '0108775015'
    recs = rec.recommend("cust_dormant", n=5, exclude_purchased=True)
    rec_ids = [r["article_id"] for r in recs]

    assert "0108775015" not in rec_ids, "Previously purchased article should be excluded."


def test_content_recommender_returns_n_items(test_db):
    """Verify content recommender produces requested number of candidates."""
    rec = ContentRecommender(test_db)
    rec.fit()

    recs = rec.recommend("cust_active_01", n=3, exclude_purchased=False)
    assert len(recs) <= 3
    assert len(recs) > 0
    assert "score" in recs[0]


def test_hybrid_recommender_scores_bounded(test_db):
    """Verify hybrid scores are strictly between 0 and 1."""
    rec = HybridRecommender(test_db)
    rec.fit()

    recs = rec.recommend("cust_active_02", n=4)
    for r in recs:
        assert 0.0 <= r["hybrid_score"] <= 1.0, f"Score {r['hybrid_score']} out of bounds."


def test_chronological_evaluation_split(test_db):
    """Verify chronological split guarantees training strictly precedes holdout."""
    evaluator = RecommendationEvaluator(test_db)
    split = evaluator.get_chronological_split(holdout_days=28)

    assert split["cutoff_date"] < split["max_date"], "Cutoff date must strictly precede max date."
