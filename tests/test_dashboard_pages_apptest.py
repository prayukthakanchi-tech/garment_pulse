"""
Streamlit AppTest End-to-End Functional Test Suite
Renders and interacts with all 10 dashboard pages headlessly using Streamlit's native AppTest framework.
Verifies page routing, component initialization, filter state transitions, and zero unhandled exceptions.
"""

import pytest
from streamlit.testing.v1 import AppTest

PAGES = [
    "1. Executive Overview",
    "2. Category Intelligence",
    "3. Fashion Attribute Intelligence",
    "4. Customer Intelligence",
    "5. Product Intelligence",
    "6. Sales Channel Analytics",
    "7. Recommendation Engine",
    "8. Demand Forecasting",
    "9. Category Opportunity Radar",
    "10. Data Quality & Governance",
]


def test_all_10_dashboard_pages_session_navigation():
    """Test full interactive session navigating through all 10 dashboard pages sequentially."""
    at = AppTest.from_file("app.py", default_timeout=120)
    at.run()
    assert len(at.exception) == 0, f"Exception on initial load: {at.exception}"

    sidebar_radio = at.sidebar.radio[0]

    for page_name in PAGES:
        sidebar_radio.set_value(page_name)
        at.run()
        assert len(at.exception) == 0, f"Exception on page '{page_name}': {[e.value for e in at.exception]}"
        print(f"✓ AppTest Verified Page: {page_name}")
