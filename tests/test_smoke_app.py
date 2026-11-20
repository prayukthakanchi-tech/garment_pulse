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
