"""
GarmentPulse — Application Smoke Tests
Ensures all dashboard page modules and components import and execute without runtime errors.
"""

import pytest
from dashboard.pages import (
    p01_executive_overview,
    p02_category_intelligence,
    p03_attribute_intelligence,
    p04_customer_intelligence,
    p05_product_intelligence,
    p06_channel_analytics,
    p07_recommendations,
    p08_forecasting,
    p09_opportunity_radar,
    p10_data_quality,
)
from src.insights.ai_assistant import AIBusinessAssistant
from src.insights.opportunity_engine import OpportunityEngine


def test_dashboard_modules_import_cleanly():
    """Verify all 10 dashboard page modules exist and have callable render functions."""
    modules = [
        p01_executive_overview,
        p02_category_intelligence,
        p03_attribute_intelligence,
        p04_customer_intelligence,
        p05_product_intelligence,
        p06_channel_analytics,
        p07_recommendations,
        p08_forecasting,
        p09_opportunity_radar,
        p10_data_quality,
    ]
    for mod in modules:
        assert hasattr(mod, "render"), f"Module {mod.__name__} missing render() function."
        assert callable(mod.render), f"Module {mod.__name__}.render is not callable."


def test_ai_business_assistant_intent_and_response(test_db):
    """Verify AI assistant answers queries grounded in test database."""
    assistant = AIBusinessAssistant(test_db)
    res = assistant.answer_question("Which departments showed the strongest momentum?")

    assert "finding" in res
    assert "supporting_metrics" in res
    assert "business_interpretation" in res
    assert "recommended_action" in res
    assert "limitations" in res


def test_opportunity_engine_card_generation(test_db):
    """Verify 5-part recommendation cards are generated properly."""
    oe = OpportunityEngine(test_db)
    cards = oe.generate_recommendations(level="department", min_volume=1, top_n=2)

    assert len(cards) > 0
    for c in cards:
        assert "observation" in c
        assert "evidence" in c
        assert "business_implication" in c
        assert "recommended_action" in c
        assert "limitation" in c


def test_cohort_heatmap_pandas_compat():
    """Verify plot_cohort_heatmap handles both pandas map and applymap without AttributeError."""
    import pandas as pd
    from dashboard.visualisations.customer_charts import plot_cohort_heatmap

    df = pd.DataFrame(
        [[100.0, 15.5], [100.0, None]],
        index=["2020-01", "2020-02"],
        columns=["M0", "M1"],
    )
    fig = plot_cohort_heatmap(df)
    assert fig is not None
    assert len(fig.data) > 0


def test_channel_department_contribution_columns(test_db):
    """Verify ChannelIntelligence department contribution produces purchase_volume column."""
    from src.analytics.channel_intelligence import ChannelIntelligence

    chi = ChannelIntelligence(test_db)
    df = chi.get_channel_department_contribution(top_n=5)
    assert "department_name" in df.columns
    assert "purchase_volume" in df.columns
    assert "channel_label" in df.columns
