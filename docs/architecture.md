# GarmentPulse — Enterprise System Architecture Document
**Product:** GarmentPulse — Fashion Category & Customer Decision Intelligence Platform  
**Target Environment:** Local Python 3.11+ / Windows / macOS / Linux  
**Repository Working Directory:** `c:\garment_pulse`

---

## 1. High-Level System Architecture Diagram

```
[ Raw H&M Kaggle CSVs ]
  │  transactions_train.csv (3.48 GB, 31.8M rows)
  │  articles.csv (34.5 MB, 105K rows)
  │  customers.csv (197.5 MB, 1.37M rows)
  ▼
[ Polars Ingestion Engine (src/ingestion/) ]
  │  Streaming scan (pl.scan_csv with explicit string schema_overrides)
  │  Strict preservation of leading-zero string IDs (0108775015)
  │  Zero duplicate deletion (preserves multi-unit basket multiplicity)
  ▼
[ Columnar Storage Layer (data/processed/) ]
  │  transactions.parquet (447.8 MB - 87.2% compression ratio)
  │  articles.parquet (3.4 MB)
  │  customers.parquet (88.7 MB)
  ▼
[ Embedded Columnar OLAP Database (database/garmentpulse.duckdb) ]
  │  Vectorized SIMD execution engine
  │  In-memory & disk-backed SQL query execution
  │  sql/schema.sql & analytical SQL views
  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      ANALYTICAL INTELLIGENCE LAYER                     │
├──────────────────────────┬──────────────────────────┬──────────────────┤
│ Category & Attributes    │ Customer & Cohorts       │ Product Velocity │
│ (src/analytics/)         │ (src/segmentation/)      │ (src/analytics/) │
│  - Department rankings   │  - 6 RFM Lifecycle Tiers │  - 5 SKU Stages  │
│  - HHI Concentration     │  - M+N Cohort Heatmap    │  - Accel/Slowing │
│  - Channel 1 vs 2        │  - New vs Returning      │  - Active weeks  │
├──────────────────────────┴──────────────────────────┴──────────────────┤
│                     MACHINE LEARNING & INTELLIGENCE                    │
├──────────────────────────┬──────────────────────────┬──────────────────┤
│ Recommendation Engine    │ Demand Forecasting       │ Opportunity & AI │
│ (src/recommendations/)   │ (src/forecasting/)       │ (src/insights/)  │
│  - Popularity Baseline   │  - Seasonal Naive        │  - Radar Scoring │
│  - Attribute Content     │  - Moving Average        │  - 5-part Cards  │
│  - Item Collaborative    │  - Holt-Winters Exp Sm   │  - Guarded AI    │
│  - Chrono MAP@12 Eval    │  - Walk-forward WAPE     │    Assistant     │
└──────────────────────────┴──────────────────────────┴──────────────────┘
  ▼
[ Executive Streamlit Dashboard (dashboard/ & app.py) ]
  10 Integrated Pages:
  1. Executive Overview          6. Sales Channel Analytics
  2. Category Intelligence       7. Recommendation Engine
  3. Attribute Intelligence      8. Demand Forecasting
  4. Customer Intelligence       9. Category Opportunity Radar
  5. Product Intelligence       10. Data Quality & Governance
```

---

## 2. Technology Stack Selection & Technical Justifications

| Component | Technology | Rationale & Trade-off Consideration |
|---|---|---|
| **Streaming Ingestion** | `Polars 2.x` | Loading 31.8M rows into standard Pandas requires >10 GB RAM and frequently triggers out-of-memory crashes. Polars implements Rust-backed multi-threaded streaming queries with lazy evaluation, scanning the raw 3.48 GB CSV with zero memory spikes. |
| **Storage Format** | `Parquet (Snappy)` | Reduces raw CSV disk footprint from 3.48 GB to 447.8 MB (87.2% reduction). Columnar dictionary encoding drastically accelerates column projection queries. |
| **Analytical Database** | `DuckDB` | Embedded, serverless columnar OLAP database tailored for analytical SQL. Outperforms SQLite by 50x–100x on analytical aggregations; allows sub-second execution of complex CTEs, window functions, and percentiles across 31.8M rows without running a heavyweight PostgreSQL or Snowflake cluster. |
| **Visualisation** | `Plotly` | Generates publication-grade, responsive, interactive SVG/WebGL charts with hover templates, zoom, pan, and custom editorial fashion palettes. |
| **User Interface** | `Streamlit` | Provides clean, multi-page enterprise web dashboard with cached queries (`@st.cache_data`, `@st.cache_resource`) preventing repetitive full-dataset scans during user filter interactions. |
| **Forecasting & ML** | `NumPy`, `Scikit-learn`, `LightGBM` | Self-contained, robust implementations of Holt-Winters exponential smoothing, cosine similarity, TF-IDF, and recursive walk-forward regression with zero external C-library vulnerabilities. |

---

## 3. Directory & Package Structure

```
c:\garment_pulse\
├── app.py                         # Streamlit application entry point & page router
├── requirements.txt               # Pinned production dependencies
├── pytest.ini                     # Pytest discovery configuration
├── README.md                      # Comprehensive project documentation
├── .gitignore                     # Git ignore rules protecting raw Kaggle files
│
├── config/
│   ├── __init__.py
│   └── settings.py                # Centralized directory paths, colors, thresholds
│
├── data/
│   ├── raw/                       # Raw Kaggle CSVs (transactions_train, articles, customers)
│   ├── staging/                   # Intermediate ETL validation artifacts
│   ├── processed/                 # Compressed columnar Parquet files
│   └── exports/                   # Analytical output exports
│
├── database/
│   └── garmentpulse.duckdb        # Persistent DuckDB embedded columnar database
│
├── sql/
│   ├── schema.sql                 # DDL: tables, constraints, analytical views
│   ├── category_analytics.sql     # Category volume, share, HHI, and momentum queries
│   ├── customer_analytics.sql     # Customer RFM and lifecycle segmentation queries
│   ├── product_analytics.sql      # SKU lifecycle stage and observation window queries
│   └── cohort_analysis.sql        # Monthly cohort acquisition and repeat activity queries
│
├── src/
│   ├── ingestion/
│   │   ├── csv_loader.py          # Lazy streaming CSV ingestion
│   │   ├── parquet_converter.py   # Memory-efficient Parquet converter
│   │   └── db_loader.py           # DuckDB database initialiser & loader
│   ├── preprocessing/
│   │   ├── data_profiler.py       # Empirical statistics and audit report generator
│   │   ├── data_validator.py      # Rule-based validation test suite
│   │   └── data_cleaner.py        # Governed cleaning action logger
│   ├── analytics/
│   │   ├── category_intelligence.py   # Module A: Category performance engine
│   │   ├── attribute_intelligence.py  # Module B: Fashion attributes engine
│   │   ├── channel_intelligence.py    # Module E: Sales channels engine
│   │   └── product_intelligence.py    # Module D: SKU lifecycle engine
│   ├── segmentation/
│   │   ├── customer_intelligence.py   # Module C: RFM customer segmentation
│   │   └── cohort_analysis.py         # Module C: Monthly cohort retention
│   ├── recommendations/
│   │   ├── popularity_recommender.py  # Popularity baseline
│   │   ├── content_recommender.py     # Attribute-based content matching
│   │   ├── collaborative_recommender.py # Item-based co-purchase collaborative filtering
│   │   ├── hybrid_recommender.py      # Weighted ensemble recommender
│   │   └── evaluator.py               # Chronological holdout evaluator (MAP@12)
│   ├── forecasting/
│   │   └── demand_forecaster.py       # Module G: SN, MA, Holt-Winters, LightGBM
│   └── insights/
│       ├── opportunity_engine.py      # Module H: Multi-factor opportunity scoring
│       └── ai_assistant.py            # Module I: Guarded AI decision-support assistant
│
├── dashboard/
│   ├── components/                # Metric cards, chart styling, cached filters
│   ├── visualisations/            # Specialised Plotly chart generators
│   └── pages/                     # 10 dedicated interactive dashboard pages
│
├── reports/
│   ├── dataset_audit.md           # Empirical source file audit
│   ├── data_quality.md            # Automated validation results & cleaning log
│   ├── methodology.md             # Formal analytical formulas & protocols
│   └── business_insights.md       # Empirical merchandising findings
│
├── tests/                         # Pytest test suite (20 automated unit/smoke tests)
│   ├── conftest.py                # In-memory DuckDB mock fixtures
│   ├── test_ingestion.py
│   ├── test_metrics.py
│   ├── test_segmentation.py
│   ├── test_forecasting.py
│   ├── test_recommendations.py
│   └── test_smoke_app.py
│
└── docs/
    ├── architecture.md            # System architecture document
    ├── data_dictionary.md         # Data dictionary & glossary
    └── interview_preparation.md   # Executive talking points & resume bullets
```
