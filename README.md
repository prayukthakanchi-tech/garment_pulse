# GarmentPulse — Fashion Category & Customer Decision Intelligence Platform

> **Turning Fashion Demand Signals into Smarter Merchandising Decisions.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.0+-yellow.svg)](https://duckdb.org/)
[![Polars](https://img.shields.io/badge/Polars-2.x-orange.svg)](https://pola.rs/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-red.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-20%2F20%20passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-Academic%20Portfolio-lightgrey.svg)]()

---

## 1. Product Vision & Overview

**GarmentPulse** is an enterprise-grade retail decision-support intelligence platform built for fashion category managers, merchandising analysts, and customer intelligence teams. It transforms historical fashion transactions and product metadata into actionable commercial priorities.

The platform directly answers six critical merchandising questions:
1. **Which fashion categories demonstrate increasing customer demand?**
2. **Which product design attributes (colours, styles, garment groups) influence purchasing patterns?**
3. **Which customer segments demonstrate repeat-purchase loyalty versus cooling engagement?**
4. **Which individual SKUs are accelerating, emerging, or decelerating across their lifecycle?**
5. **What category demand patterns warrant merchandising investigation before season refresh?**
6. **Which products are commercially relevant to an individual customer's historical closet preferences?**

*Academic Portfolio Notice:* GarmentPulse is an independent academic research and portfolio project based on publicly available Kaggle competition data. It is **not** an official H&M or Myntra internal production system.

---

## 2. Primary Data Source & Licensing

- **Dataset:** [H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data) (Official Kaggle Competition)
- **Scale:**
  - `transactions_train.csv`: **31,788,324** records (3.48 GB uncompressed)
  - `articles.csv`: **105,542** unique fashion articles with 25 metadata attributes
  - `customers.csv`: **1,371,980** customer profiles
- **Observation Window:** `2018-09-20` to `2020-09-22` (~2 years of weekly purchasing events)
- **Compliance:** Raw and derived competition data are excluded from version control in accordance with competition rules.

---

## 3. High-Performance Architecture

```
Raw CSVs (3.5 GB) ──► Polars Streaming Ingestion ──► Snappy Parquet (448 MB)
                              │
                              ▼
            DuckDB Vectorized In-Memory / OLAP Database
                              │
      ┌───────────────────────┼───────────────────────┐
      ▼                       ▼                       ▼
Category & Attributes    Customer & Cohorts      Recommendation Engine
  - Volume, Share, HHI    - 6 RFM Lifecycle       - Hybrid Ensemble
  - Period Momentum       - Monthly Heatmaps      - Chronological MAP@12
      │                       │                       │
      └───────────────────────┼───────────────────────┘
                              ▼
              Demand Forecasting (Holt-Winters & LGBM)
                              ▼
           Commercial Opportunity Radar & Guarded AI
                              ▼
                 10-Page Streamlit Dashboard
```

---

## 4. Platform Modules & Capabilities

- **Module A — Fashion Category Intelligence:** Hierarchical performance across Departments, Sections, Product Groups, Garment Groups, and Product Types. Computes volume shares, period-over-period growth, customer penetration, and Herfindahl-Hirschman Index (HHI) assortment concentration.
- **Module B — Fashion Attribute Intelligence:** Analyzes physical design traits including colour palettes, luminosity, graphical patterns, and cross-attribute combinations.
- **Module C — Customer Lifecycle & Cohorts:** RFM-inspired measurable segmentation classifying all 1.36M purchasing customers into 6 distinct tiers (*Frequent Buyers, Emerging Customers, Recently Active, Cooling, At-Risk, Dormant*), accompanied by a monthly cohort repeat activity heatmap.
- **Module D — Product Lifecycle Intelligence:** Evaluates article velocities, active observation lifespans, and lifecycle transition states (*Emerging, Accelerating, Stable, Slowing, Low Activity*).
- **Module E — Sales Channel Analytics:** Objective, neutral comparative analysis between Channel 1 and Channel 2 volume splits, customer overlap, and category affinities.
- **Module F — Personalised Recommendation Engine:** Hybrid ranking combining community popularity baselines, design attribute content matching, and item-based collaborative filtering, evaluated via strict chronological holdouts (MAP@12, Recall@12, Precision@12, Coverage).
- **Module G — Fashion Demand Forecasting:** Multi-week purchase volume forecasting evaluating Seasonal Naive, Moving Average, Holt-Winters Exponential Smoothing, and LightGBM walk-forward regressions benchmarked with WAPE, MAE, and RMSE.
- **Module H — Commercial Opportunity Engine:** Transparent multi-criteria scoring generating actionable 5-part merchandising decision cards (`OBSERVATION` → `EVIDENCE` → `BUSINESS IMPLICATION` → `RECOMMENDED ACTION` → `LIMITATION`).
- **Module I — Guarded AI Business Assistant:** Natural language decision-support assistant strictly grounded in pre-calculated DuckDB SQL metrics, preventing statistical hallucination.
- **Module J — Executive Dashboard:** 10-page Streamlit application featuring clean editorial fashion typography, responsive Plotly charts, and cached query filters.

---

## 5. Non-Negotiable Data Limitations

To ensure absolute analytical rigor, the platform strictly codifies the following empirical boundaries:
1. **Price Normalisation:** Transaction prices are dimensionless normalised indices ($0.000017$ to $0.591525$). The platform **never** displays them as currency ($/€/£) and **never** calculates gross revenue or Average Order Value (AOV).
2. **Absence of Order Identifiers:** Because shopping cart/basket UUIDs are not provided, transactions cannot be grouped into discrete orders.
3. **Absence of Inventory Snapshots:** Product availability, stockout events, warehouse quantities, and safety stocks are missing. Volume shifts reflect demand pull, not supply constraints.
4. **Absence of Web Impressions:** Website visits and clicks are not recorded; true conversion rates cannot be calculated.
5. **Absence of Return Events & Margins:** Wholesale costs, product returns, and profit margins are absent.

---

## 6. Installation & Quickstart Guide

### 6.1 Prerequisites & Environment Setup
Clone the repository and install dependencies in Python 3.11+:
```bash
git clone https://github.com/your-username/garmentpulse.git
cd garmentpulse
pip install -r requirements.txt
```

### 6.2 Data Ingestion & Database Population
Place the downloaded Kaggle files in `data/raw/` (`transactions_train.csv`, `articles.csv`, `customers.csv`), then run the streaming ingestion pipeline:
```bash
python -c "
from src.ingestion.db_loader import run_full_ingestion
run_full_ingestion()
"
```
*Elapsed time: ~20 seconds to stream, compress, and ingest all 31.8M transactions into DuckDB.*

### 6.3 Run Automated Quality Tests
Verify the complete test suite (20 automated unit and integration tests):
```bash
python -m pytest -v
```

### 6.4 Launch the Interactive Executive Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` to explore all 10 intelligence modules.

---

## 7. Automated Test Verification Results

All 20 test suites pass with 100% success:
- `tests/test_ingestion.py`: String identifier preservation, leading zeros, table schema DDL.
- `tests/test_metrics.py`: Volume aggregation, HHI concentration, attribute shares.
- `tests/test_segmentation.py`: RFM segmentation boundaries, cohort M+0 consistency.
- `tests/test_forecasting.py`: Seasonal naive, moving average, Holt-Winters prediction intervals.
- `tests/test_recommendations.py`: Discovery exclusion, hybrid scores, chronological validation splits.
- `tests/test_smoke_app.py`: All 10 dashboard module renderers and AI decision assistant.

---

## 8. Repository Documentation Index

- [Dataset Audit Report](reports/dataset_audit.md): Empirical volume, taxonomy, and missingness audit of the raw dataset.
- [Data Quality Report](reports/data_quality.md): Automated rule-based validation and cleaning decision logs.
- [Analytics Methodology](reports/methodology.md): Mathematical formulations, scoring formulas, and backtest protocols.
- [Business Insights Report](reports/business_insights.md): Comprehensive executive retail findings and category priorities.
- [System Architecture](docs/architecture.md): Technical architecture, data pipelines, and design trade-offs.
- [Data Dictionary](docs/data_dictionary.md): Field-level definitions, types, domains, and derived metrics glossary.
- [Interview Preparation Guide](docs/interview_preparation.md): Executive talking points, case study frameworks, and 3 resume bullets.
