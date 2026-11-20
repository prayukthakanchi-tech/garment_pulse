"""
GarmentPulse Configuration Settings
Fashion Category & Customer Decision Intelligence Platform
"""
import os
from pathlib import Path

# ─────────────────────────────────────────────
# Directory Configuration
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"
DATABASE_DIR = PROJECT_ROOT / "database"
SQL_DIR = PROJECT_ROOT / "sql"
REPORTS_DIR = PROJECT_ROOT / "reports"

# ─────────────────────────────────────────────
# Database Configuration
# ─────────────────────────────────────────────
DUCKDB_PATH = DATABASE_DIR / "garmentpulse.duckdb"

# ─────────────────────────────────────────────
# Raw Data Files
# ─────────────────────────────────────────────
TRANSACTIONS_CSV = RAW_DIR / "transactions_train.csv"
ARTICLES_CSV = RAW_DIR / "articles.csv"
CUSTOMERS_CSV = RAW_DIR / "customers.csv"

# ─────────────────────────────────────────────
# Parquet Files (Processed)
# ─────────────────────────────────────────────
TRANSACTIONS_PARQUET = PROCESSED_DIR / "transactions.parquet"
ARTICLES_PARQUET = PROCESSED_DIR / "articles.parquet"
CUSTOMERS_PARQUET = PROCESSED_DIR / "customers.parquet"

# ─────────────────────────────────────────────
# Data Processing Configuration
# ─────────────────────────────────────────────
CSV_BATCH_SIZE = 500_000  # Rows per batch for streaming ingestion
POLARS_STREAMING = True

# ─────────────────────────────────────────────
# Date Configuration
# ─────────────────────────────────────────────
# Will be validated against actual data during audit
EXPECTED_DATE_FORMAT = "%Y-%m-%d"

# ─────────────────────────────────────────────
# Analysis Configuration
# ─────────────────────────────────────────────
# Minimum transactions for a category to appear in growth rankings
MIN_CATEGORY_TRANSACTIONS = 100
# Minimum customers for a category to appear in growth rankings
MIN_CATEGORY_CUSTOMERS = 50
# Minimum weeks of data for trend analysis
MIN_WEEKS_FOR_TREND = 4
# Recent period for momentum calculations (weeks)
RECENT_PERIOD_WEEKS = 4
# Previous period for comparison (weeks)
PREVIOUS_PERIOD_WEEKS = 4

# ─────────────────────────────────────────────
# Customer Segmentation Thresholds
# ─────────────────────────────────────────────
# Recency thresholds (days since last purchase)
RECENCY_ACTIVE_DAYS = 30
RECENCY_COOLING_DAYS = 90
RECENCY_AT_RISK_DAYS = 180
# Frequency thresholds (distinct purchase dates)
FREQUENCY_HIGH = 10
FREQUENCY_MEDIUM = 4

# ─────────────────────────────────────────────
# Product Lifecycle Thresholds
# ─────────────────────────────────────────────
# Minimum purchase lines for product classification
MIN_PRODUCT_PURCHASES = 5
# Growth rate threshold for acceleration
ACCELERATION_THRESHOLD = 0.20
# Decline threshold
DECLINE_THRESHOLD = -0.20

# ─────────────────────────────────────────────
# Recommendation Engine Configuration
# ─────────────────────────────────────────────
TOP_N_RECOMMENDATIONS = 12
VALIDATION_WEEKS = 4  # Last N weeks for validation
MIN_INTERACTIONS_FOR_RECO = 3

# ─────────────────────────────────────────────
# Forecasting Configuration
# ─────────────────────────────────────────────
FORECAST_HORIZON_WEEKS = 8
BACKTEST_FOLDS = 4
MIN_HISTORY_WEEKS = 26  # Minimum weeks needed for forecasting

# ─────────────────────────────────────────────
# Opportunity Scoring Weights
# ─────────────────────────────────────────────
OPPORTUNITY_WEIGHTS = {
    "volume_growth": 0.25,
    "customer_growth": 0.20,
    "repeat_rate": 0.15,
    "category_contribution": 0.15,
    "product_concentration": 0.10,
    "attribute_momentum": 0.15,
}

# ─────────────────────────────────────────────
# AI Insights Configuration
# ─────────────────────────────────────────────
# API key from environment variable (optional)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
AI_INSIGHTS_ENABLED = bool(GEMINI_API_KEY)

# ─────────────────────────────────────────────
# Dashboard Configuration
# ─────────────────────────────────────────────
DASHBOARD_TITLE = "GarmentPulse"
DASHBOARD_SUBTITLE = "Fashion Category & Customer Decision Intelligence"
DASHBOARD_ICON = "GP"
PAGE_ICON = "GP"

# Color palette - Fashion editorial style
COLORS = {
    "primary": "#1a1a2e",
    "secondary": "#16213e",
    "accent": "#e94560",
    "background": "#f8f9fa",
    "surface": "#ffffff",
    "text_primary": "#1a1a2e",
    "text_secondary": "#6c757d",
    "success": "#2d6a4f",
    "warning": "#e9c46a",
    "danger": "#e76f51",
    "info": "#457b9d",
    "chart_palette": [
        "#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51",
        "#606c38", "#283618", "#dda15e", "#bc6c25", "#457b9d",
    ],
}

# ─────────────────────────────────────────────
# Sales Channel Labels
# ─────────────────────────────────────────────
# Until verified from documentation, use neutral labels
CHANNEL_LABELS = {
    1: "Channel 1",
    2: "Channel 2",
}

# ─────────────────────────────────────────────
# Data Limitation Notices
# ─────────────────────────────────────────────
DATA_LIMITATIONS = [
    "Price values are normalised — not actual currency amounts.",
    "No order/invoice identifiers — cannot determine basket composition.",
    "No inventory/stock data — cannot assess product availability.",
    "No cost or margin data — cannot calculate profitability.",
    "No website session/click data — cannot measure conversion.",
    "No return event data — purchase volumes include unreturned items.",
    "No discount labels — cannot assess promotional impact.",
    "First observed purchase ≠ product launch date.",
    "Last observed purchase ≠ product discontinuation.",
    "Transaction dates ≠ order IDs.",
    "Duplicate rows may represent multiple legitimate purchases.",
]
