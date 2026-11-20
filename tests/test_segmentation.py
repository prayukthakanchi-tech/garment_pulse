"""
Unit tests for customer lifecycle segmentation and cohort analysis calculations.
"""

from src.segmentation.customer_intelligence import CustomerIntelligence
from src.segmentation.cohort_analysis import CohortAnalysis


def test_customer_segmentation_rules(test_db):
    """Verify customers are classified into correct lifecycle segments."""
    ci = CustomerIntelligence(test_db)
    seg_df = ci.get_customer_segments()

    assert not seg_df.empty, "Segment dataframe is empty."
    total_assigned = seg_df["customer_count"].sum()
    assert total_assigned == 6, f"Expected 6 customers segmented, got {total_assigned}."

    # Verify individual segment assignments
    segments = set(seg_df["segment"].values)
    assert "Frequent Buyers" in segments, "cust_active_01 should be Frequent Buyer."
    assert "Emerging Customers" in segments, "cust_emerging should be Emerging Customer."
    assert "Dormant Customers" in segments, "cust_dormant should be Dormant."


def test_cohort_month_zero_is_100_percent(test_db):
    """Verify that in period 0 (acquisition month), active customer percentage is 100%."""
    ca = CohortAnalysis(test_db)
    raw_cohort = ca.get_monthly_cohort_data(max_period=6)

    assert not raw_cohort.empty
    m0_rows = raw_cohort[raw_cohort["period_number"] == 0]
    for _, row in m0_rows.iterrows():
        assert row["repeat_activity_rate_pct"] == 100.0, f"Period 0 must be 100%, got {row['repeat_activity_rate_pct']}"


def test_retention_percentages_within_valid_bounds(test_db):
    """Verify repeat activity rate % is strictly between 0 and 100%."""
    ca = CohortAnalysis(test_db)
    raw_cohort = ca.get_monthly_cohort_data(max_period=6)

    for rate in raw_cohort["repeat_activity_rate_pct"]:
        assert 0.0 <= rate <= 100.0, f"Rate {rate} out of valid bounds [0, 100]."
