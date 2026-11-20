"""
Unit tests for category analytics, concentration HHI, and metrics aggregation.
"""

from src.analytics.category_intelligence import CategoryIntelligence
from src.analytics.attribute_intelligence import AttributeIntelligence
from src.analytics.channel_intelligence import ChannelIntelligence


def test_category_performance_aggregation(test_db):
    """Verify category volume, unique customer counts, and volume shares."""
    ci = CategoryIntelligence(test_db)
    df = ci.get_category_performance(level="department", min_transactions=1)

    assert not df.empty, "Category performance returned empty dataframe."
    assert "Jersey Basic" in df["category_name"].values
    assert df["purchase_volume"].sum() == 20
    assert abs(df["volume_share_pct"].sum() - 100.0) < 0.1, "Volume shares must sum to 100%."


def test_product_concentration_hhi(test_db):
    """Verify Herfindahl-Hirschman Index is computed and positive."""
    ci = CategoryIntelligence(test_db)
    df = ci.get_category_performance(level="department", min_transactions=1)

    assert "hhi_concentration" in df.columns
    for hhi in df["hhi_concentration"]:
        assert hhi > 0, "HHI must be positive."
        assert hhi <= 10000.0, "HHI cannot exceed 10,000."


def test_attribute_colour_performance(test_db):
    """Verify colour group aggregation."""
    ai = AttributeIntelligence(test_db)
    cdf = ai.get_colour_performance(min_transactions=1)

    assert not cdf.empty
    assert "Black" in cdf["colour_group_name"].values
    assert cdf["purchase_volume"].sum() == 20


def test_channel_distribution(test_db):
    """Verify Channel 1 vs Channel 2 volume splits."""
    chi = ChannelIntelligence(test_db)
    ch_df = chi.get_channel_overview()

    assert len(ch_df) == 2, "Expected 2 sales channels."
    assert ch_df["purchase_volume"].sum() == 20
    assert abs(ch_df["volume_share_pct"].sum() - 100.0) < 0.1
