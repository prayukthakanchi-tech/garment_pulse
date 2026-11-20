# GarmentPulse — Fashion Category & Customer Decision Intelligence Platform

> **Turning Fashion Demand Signals into Smarter Merchandising Decisions.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-1E3A8A.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.0+-FFF000.svg?logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Polars](https://img.shields.io/badge/Polars-1.x-CD7F32.svg?logo=polars&logoColor=white)](https://pola.rs/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.3+-059669.svg)](https://lightgbm.readthedocs.io/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker Ready](https://img.shields.io/badge/Docker-Containerized-2496ED.svg?logo=docker&logoColor=white)](Dockerfile)
[![Tests](https://img.shields.io/badge/tests-27%2F27%20passed-059669.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![WCAG AA](https://img.shields.io/badge/accessibility-WCAG%20AA-blue.svg)]()
[![License](https://img.shields.io/badge/license-Academic%20Portfolio-lightgrey.svg)]()

---

## 1. Executive Summary & Vision

**GarmentPulse** is an enterprise-grade retail decision-support intelligence platform engineered for fashion category managers, merchandising analysts, demand planners, and customer intelligence teams. It transforms large-scale historical fashion transactions and rich article metadata into actionable commercial priorities.

The platform directly answers six critical merchandising questions:
1. **Demand Expansion:** Which fashion categories demonstrate increasing consumer demand?
2. **Attribute Influence:** Which physical design traits (colour palette, silhouette, garment group) drive sales velocity?
3. **Customer Retention:** Which customers demonstrate repeat-purchase loyalty versus cooling engagement?
4. **Product Lifecycle:** Which individual SKUs are accelerating, emerging, stable, or slowing across their lifecycle?
5. **Assortment Planning:** What category-level demand shifts should merchandising planners investigate before seasonal buys?
6. **Personalized Discovery:** Which products are commercially relevant to an individual customer's historical wardrobe preferences?

*Academic Portfolio Notice:* GarmentPulse is an independent academic research and portfolio project developed with publicly available Kaggle research data. It is **not** an official H&M or Myntra production system.

---

## 2. Dataset Scale & Governance

* **Data Source:** [H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data) (Official Kaggle Research Dataset)
* **Scale & Volume:**
  * `transactions`: **31,788,324** physical purchase records (3.48 GB uncompressed)
  * `articles`: **105,542** unique fashion articles across 25 design attributes
  * `customers`: **1,371,980** customer profiles (1,362,281 purchasing entities)
* **Observation Horizon:** `2018-09-20` to `2020-09-22` (734 calendar days)
* **Licensing Compliance:** Restricted raw and derived competition data are excluded from version control in strict accordance with competition rules.

---

## 3. High-Performance Architecture

GarmentPulse uses a modern columnar data engineering pipeline that achieves **sub-second analytical latencies** across 31.8 million transaction rows without requiring external distributed clusters:

```
+--------------------------------------------------------------------------------------------------+
|                                    DATA INGESTION & STORAGE                                      |
|                                                                                                  |
|   Raw Kaggle CSVs (3.5 GB) ──► Polars Streaming Ingestion ──► Snappy Columnar Parquet (448 MB)   |
|                                                │                                                 |
|                                                ▼                                                 |
|                                 DuckDB Vectorized OLAP Engine                                    |
|                             (Thread-Isolated Connection Pooling)                                 |
+------------------------------------------------+-------------------------------------------------+
                                                 │
                                                 ▼
+--------------------------------------------------------------------------------------------------+
|                                ANALYTICAL ENGINES & PRECOMPUTATION                               |
|                                                                                                  |
|   ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐          |
|   │ Category & Attributes     │ Customer & Cohorts        │ Recommendations & ML      │          |
|   │ - Growth Momentum         │ - 6 RFM Lifecycle Tiers   │ - Hybrid Candidate Graph  │          |
|   │ - HHI Concentration       │ - Monthly Repeat Heatmap  │ - MAP@12 Chrono Split     │          |
|   └─────────────┬─────────────┴─────────────┬─────────────┴─────────────┬─────────────┘          |
|                 │                           │                           │                        |
|                 └───────────────────────────┼───────────────────────────┘                        |
|                                             ▼                                                    |
|                           Demand Forecasting & Opportunity Radar                                 |
|                           - LightGBM & Holt-Winters Walk-Forward                                 |
|                           - 5-Part Structured Action Cards                                       |
|                           - Precomputed Parquet Aggregation Layer                                |
+---------------------------------------------+----------------------------------------------------+
                                              │
                                              ▼
+--------------------------------------------------------------------------------------------------+
|                                 ENTERPRISE SAAS PRESENTATION LAYER                               |
|                                                                                                  |
|                          Streamlit 10-Module Executive Control Center                            |
|                 (Minimalist Typography, WCAG AA Contrast, Thread-Safe Caching)                   |
+--------------------------------------------------------------------------------------------------+
```

---

## 4. The 10 Analytical Modules

| # | Module | Primary Merchandising Objective | Core Methodologies & Algorithms | Output Deliverables |
| :-: | :--- | :--- | :--- | :--- |
| **01** | **Executive Overview** | High-level portfolio health & macro momentum signals | Vectorized KPI aggregation, monthly trajectory series | 4-KPI banner, volume time-series, top department bar |
| **02** | **Category Intelligence** | Assortment velocity & concentration tracking | Herfindahl-Hirschman Index (HHI), PoP momentum, YoY volume shift | Volume treemaps, growth scatter plots, YoY comparison tables |
| **03** | **Fashion Attribute Intelligence** | Design trait influence on consumer purchasing | Cross-attribute co-occurrence, colour palette velocity | Top 12 colour groups, garment group trajectory, attribute heatmap |
| **04** | **Customer Intelligence** | Repeat engagement & retention dynamics | 6-tier RFM lifecycle rules, monthly cohort repeat matrix | Segment donut chart, retention heatmap, new vs returning area |
| **05** | **Product Intelligence** | Individual SKU velocity & lifecycle stages | 5-stage classification (*Emerging, Accelerating, Stable, Slowing, Low*) | Article lifecycle distribution, SKU search table, velocity deep-dive |
| **06** | **Sales Channel Analytics** | Objective channel mix comparison | Channel split index, customer overlap penetration | Channel volume KPIs, monthly channel trajectory, overlap pie chart |
| **07** | **Recommendation Engine** | Customer-specific assortment discovery | Hybrid ensemble (Popularity + Attribute Affinity + Item Co-purchase) | Customer closet history, top 12 recommendation cards, MAP@12 benchmark |
| **08** | **Demand Forecasting** | Forward weekly transaction projections | Seasonal Naive, Moving Average, Holt-Winters, LightGBM walk-forward | Forward projections with 95% confidence intervals, backtest leaderboard |
| **09** | **Category Opportunity Radar** | Merchandising investment prioritization | Multi-criteria scoring, grounded SQL-backed decision assistant | Radar charts, 5-part structured action cards, guarded AI answers |
| **10** | **Data Quality & Governance** | Data integrity verification & limitation boundaries | 15+ automated rule checks, duplicate transaction analysis | Automated validation results, cleaning audit log, 11 data limitations |

---

## 5. Performance Engineering & Benchmark Results

Through thread-isolated connection pooling and precomputed columnar Parquet caching, GarmentPulse eliminated all UI freezes and blank-screen bottlenecks across the 31.8M row dataset:

| Analytical Operation / Module | Initial Cold Latency | Optimized Cold Latency | Cached Session Latency | Measured Speedup Factor |
| :--- | :---: | :---: | :---: | :---: |
| **Page 1: Portfolio Macro KPIs** | `26.410s` | `0.036s` | `< 0.001s` | **731x faster** |
| **Page 3: Colour Palette Performance** | `6.740s` | `0.034s` | `< 0.001s` | **198x faster** |
| **Page 3: Total Page 3 Render** | `16.360s` | `0.291s` | `< 0.002s` | **56x faster (Blank screen eliminated)** |
| **Page 4: Cohort Retention Matrix** | `8.740s` | `0.072s` | `< 0.001s` | **121x faster** |
| **Page 5: Article Performance Query** | `52.220s` | `0.035s` | `< 0.001s` | **1,492x faster** |
| **Page 5: Lifecycle Classifications** | `48.100s` | `0.009s` | `< 0.001s` | **5,344x faster** |
| **Page 8: Forecasting Walk-Forward** | `27.360s` | `2.720s` | `< 0.001s` | **10x faster (No WMIC hang)** |

---

## 6. Machine Learning Rigor & Evaluation Protocols

### A. Recommendation Engine Chronological Validation
* **Strict Temporal Splitting:** Models are trained exclusively on data prior to `2020-09-15` (cutoff) and evaluated on actual ground-truth purchases observed during the subsequent 7-day holdout week. Random train-test splitting is strictly forbidden to prevent temporal leakage.
* **Model Benchmarks:**
  * **Popularity Baseline:** Recommends recent top-volume articles (high baseline precision, lowest catalogue coverage: `0.01%`).
  * **Content-Based Attribute Affinity:** Explores matching styles, colours, and garment cuts (`0.06%` coverage).
  * **Collaborative Filtering:** Co-purchase item graph projection.
  * **GarmentPulse Hybrid:** Blends popularity prior, collaborative affinity, and attribute scoring to optimize precision against diversity.
* **Causal Caveat:** Offline metrics (`MAP@12`, `Recall@12`) reflect ranking correlation with historical logs, not proven incremental sales without live randomized A/B experimentation.

### B. Demand Forecasting Walk-Forward Evaluation
* **Horizon:** 8-week unobserved chronological holdout window.
* **Error Metrics (Tested on `Jersey Basic`):**
  * **LightGBM Walk-forward Regressor:** `WAPE: 21.07%` (MAE: 6,102; RMSE: 9,899) — **Best Performer**
  * **Moving Average (4-wk):** `WAPE: 21.25%` (MAE: 6,153; RMSE: 10,342)
  * **Seasonal Naive:** `WAPE: 28.09%` (MAE: 8,135; RMSE: 13,931)
  * **Holt-Winters Exponential Smoothing:** `WAPE: 28.12%` (MAE: 8,144; RMSE: 11,962)
* **Planning Boundary:** 95% confidence bands rendered. Projections estimate checkout volume lines only; interpreting volume forecasts as raw factory replenishment orders is strictly disclaimed.

---

## 7. Empirical Data Limitations & Governance Guardrails

The application strictly enforces 11 non-negotiable empirical boundaries across all documentation and visualizations:

1. **Normalized Price Values:** Prices are dimensionless numbers ($0.000017$ to $0.591525$). The platform **never** displays currency symbols and **never** calculates gross revenue or Average Order Value (AOV).
2. **Absence of Order Identifiers:** Transactions are discrete line items; baskets represent same-day customer purchases.
3. **Zero Inventory Data:** Product availability, stockout events, warehouse quantities, and safety stocks are missing.
4. **Zero Web Session / Click Data:** Website visits and clicks are not recorded; true conversion rates cannot be calculated.
5. **Zero Cost or Margin Data:** Wholesale costs, gross margins, and profit calculations are never fabricated.
6. **No Return Event Data:** Purchase lines include unreturned items.
7. **No Promotional Identifiers:** Markdown and discount labels are absent.
8. **First Observed Purchase != Launch Date:** Article entry dates represent transaction observation proxies only.
9. **Last Observed Purchase != Discontinuation:** Item absence from recent transactions is not assumed to be factory discontinuation.
10. **Transaction Dates != Order IDs:** Transactions are analyzed chronologically without basket identifiers.
11. **Academic Portfolio Boundary:** Explicitly disclaimed as an independent portfolio project.

---

## 8. Deployment & Quickstart Guide

### Option 1: Native Local Run (Recommended for Development)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/garment_pulse.git
   cd garment_pulse
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS / Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```bash
   python -m streamlit run app.py
   ```
   *Access the platform in your browser at `http://localhost:8501`.*

---

### Option 2: Docker Containerization (Recommended for Production)

The repository includes a production multi-stage `Dockerfile` and `docker-compose.yml`:

```bash
# Build and run with Docker Compose
docker compose up --build -d

# View logs
docker compose logs -f

# Stop container
docker compose down
```
*Healthcheck automatically monitors `http://localhost:8501/_stcore/health`.*

---

### Option 3: Streamlit Community Cloud (One-Click Cloud Hosting)

1. Push this repository to your GitHub account (`master` or `main` branch).
2. Visit [share.streamlit.io](https://share.streamlit.io) and log in with GitHub.
3. Click **"New app"**, select your repository, set the main file path to `app.py`.
4. Click **"Deploy"** — Streamlit Cloud will read `.streamlit/config.toml` and launch automatically.

---

## 9. Automated Testing & Verification Suite

GarmentPulse includes 27 comprehensive automated tests covering unit logic, data concurrency, and end-to-end headless dashboard rendering:

```bash
# Run all unit and integration tests
python -m pytest -v

# Run DuckDB concurrency stress tests
python -m pytest tests/test_duckdb_stress.py -v

# Run headless Streamlit AppTest across all 10 pages
python -m pytest tests/test_dashboard_pages_apptest.py -v
```

**Test Suite Coverage Summary:**
* `tests/test_forecasting.py`: Seasonal naive, moving average, Holt-Winters prediction intervals.
* `tests/test_ingestion.py`: String identifier preservation, leading zeros, table schema DDL.
* `tests/test_metrics.py`: Volume aggregation, HHI concentration, attribute shares, and channel splits.
* `tests/test_recommendations.py`: Discovery exclusion, hybrid scores, chronological validation splits.
* `tests/test_segmentation.py`: RFM segmentation boundaries, cohort M+0 consistency, and retention rates.
* `tests/test_smoke_app.py`: All 10 dashboard module renderers and AI decision assistant.
* `tests/test_data_service.py`: Thread-local connections, cursor lifecycle, and scalar/DataFrame execution.
* `tests/test_duckdb_stress.py`: 10-thread concurrent stress testing, rapid cursor allocation, and zero deadlocks.
* `tests/test_dashboard_pages_apptest.py`: Headless interactive session navigating through all 10 pages sequentially.

---

## 10. Repository Structure

```
garment_pulse/
├── .dockerignore
├── .gitignore
├── .streamlit/
│   └── config.toml                  # Streamlit enterprise production theme & server config
├── Dockerfile                       # Multi-stage production container build
├── docker-compose.yml               # 1-command Docker orchestration
├── README.md                        # Master documentation
├── requirements.txt                 # Pinned dependencies
├── pytest.ini                       # Pytest test configuration
├── app.py                           # Application entrypoint & sidebar router
│
├── config/
│   ├── __init__.py
│   └── settings.py                  # Project paths, taxonomy dictionaries, limitation notices
│
├── dashboard/
│   ├── data_service.py              # Centralized thread-safe caching query layer
│   ├── components/
│   │   ├── charts.py                # Plotly styling themes (Plus Jakarta Sans)
│   │   ├── filters.py               # Standardized sidebar filter controls
│   │   └── metrics.py               # High-contrast KPI cards with delta pill badges
│   ├── pages/
│   │   ├── p01_executive_overview.py
│   │   ├── p02_category_intelligence.py
│   │   ├── p03_attribute_intelligence.py
│   │   ├── p04_customer_intelligence.py
│   │   ├── p05_product_intelligence.py
│   │   ├── p06_channel_analytics.py
│   │   ├── p07_recommendations.py
│   │   ├── p08_forecasting.py
│   │   ├── p09_opportunity_radar.py
│   │   └── p10_data_quality.py
│   └── visualisations/
│       ├── category_charts.py
│       ├── customer_charts.py
│       └── product_charts.py
│
├── src/
│   ├── analytics/
│   │   ├── attribute_intelligence.py
│   │   ├── category_intelligence.py
│   │   ├── channel_intelligence.py
│   │   ├── precompute_aggregations.py  # Fast columnar Parquet pipeline
│   │   └── product_intelligence.py
│   ├── database/
│   │   └── connection.py            # Thread-local DuckDB connection pool
│   ├── forecasting/
│   │   └── demand_forecaster.py     # LightGBM, Holt-Winters, Moving Average backtesting
│   ├── ingestion/
│   │   ├── db_loader.py
│   │   └── parquet_converter.py
│   ├── insights/
│   │   ├── ai_assistant.py          # DuckDB-grounded decision assistant
│   │   └── opportunity_engine.py    # 5-part structured merchandising action cards
│   ├── preprocessing/
│   │   ├── data_profiler.py
│   │   └── data_validator.py
│   ├── recommendations/
│   │   ├── collaborative_recommender.py
│   │   ├── content_recommender.py
│   │   ├── evaluator.py             # Chronological MAP@12 holdout benchmark
│   │   ├── hybrid_recommender.py
│   │   └── popularity_recommender.py
│   └── segmentation/
│       ├── cohort_analysis.py       # 12-month cohort repeat matrix
│       └── customer_intelligence.py # 6-tier RFM customer lifecycle
│
├── tests/
│   ├── conftest.py                  # In-memory mock fashion database fixture
│   ├── test_dashboard_pages_apptest.py
│   ├── test_data_service.py
│   ├── test_duckdb_stress.py
│   ├── test_forecasting.py
│   ├── test_ingestion.py
│   ├── test_metrics.py
│   ├── test_recommendations.py
│   ├── test_segmentation.py
│   └── test_smoke_app.py
│
└── reports/
    ├── dataset_audit.md
    ├── data_quality.md
    ├── methodology.md
    ├── business_insights.md
    └── final_audit/
        └── FINAL_RELEASE_REPORT.md  # 100/100 comprehensive audit release report
```

---

## 11. Author & Contact

**Kanchi Prayuktha**  
*Email:* `prayukthakanchi@gmail.com`  
*Project:* GarmentPulse — Fashion Category & Customer Decision Intelligence Platform  
*License:* Academic Portfolio & Research Use Only (Subject to Kaggle H&M Dataset Competition Terms)
