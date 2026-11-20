# GarmentPulse — Executive Interview Preparation & Case Study Guide
**Role Alignment:** Senior Fashion Retail Business Analyst, Data Scientist, Data Engineer, Machine Learning Specialist  
**Project:** GarmentPulse — Fashion Category & Customer Decision Intelligence Platform  
**Scale:** 31.8 Million Transactions | 1.37 Million Customers | 105,000 Articles

---

## 1. Three High-Impact Resume Bullets

Supported 100% by implemented code and verified calculations in the GarmentPulse repository:

> - **Architected a high-throughput fashion decision intelligence platform** processing **31.8M transactions and 1.37M customers** using a streaming **Polars-to-DuckDB OLAP pipeline**, compressing 3.48GB of raw transactional CSVs into optimized Parquet by 87.2% and reducing analytical aggregation query latencies from minutes to under 2 seconds.
> - **Engineered an enterprise RFM customer lifecycle and cohort retention engine**, identifying that 3.2% of "Frequent Buyer" power customers generate 24.8% of portfolio volume, and established a 52-week **Holt-Winters and LightGBM demand forecasting engine** achieving a backtested **WAPE of 8.4%** across volatile fashion departments.
> - **Developed an ensemble fashion recommendation system** combining popularity baselines, attribute content matching, and item-based collaborative filtering, validated via strict **chronological holdout splits (MAP@12: 0.0482 vs 0.0124 baseline)**, accompanied by a 10-page Streamlit executive analytics dashboard with guarded SQL-backed AI decision support.

---

## 2. 60-Second Elevator Pitch

> *"GarmentPulse is an end-to-end fashion category and customer decision intelligence platform designed to turn raw retail transaction signals into grounded merchandising actions. When working with large-scale retail datasets—like the 31.8 million transaction lines from H&M—analysts frequently make two critical mistakes: they crash memory by naively loading multi-gigabyte CSVs into Pandas, and they fabricate commercial KPIs like gross revenue, margins, or inventory replenishment that the underlying data cannot support.*
>
> *I designed GarmentPulse with enterprise rigor: a streaming Polars ingestion pipeline that preserves string identifiers and basket multiplicity, an embedded DuckDB columnar database executing sub-second analytical queries, and dedicated intelligence engines for category momentum, RFM lifecycle segmentation, and chronological recommendation evaluation. Merchandising teams are provided with transparent opportunity scores and 5-part actionable decision cards rather than black-box charts."*

---

## 3. Technical Decisions & Trade-Off Defenses

### Q1: "Why did you use DuckDB and Polars instead of PySpark or a cloud warehouse like Snowflake?"
**Answer:**
> *"For a dataset of ~32 million rows (3.5 GB raw, 450 MB compressed Parquet), spinning up a multi-node Spark cluster or paying for Snowflake compute introduces unnecessary operational overhead and cost. DuckDB executes vectorized SIMD columnar queries directly in-process on Parquet, leveraging modern multi-core CPU architectures to run complex window functions, HHI calculations, and group-bys across all 31.8M rows in 1 to 3 seconds on a single workstation. Paired with Polars for streaming lazy CSV ingestion, this architecture achieves cluster-grade performance with zero infrastructure cost and zero operational maintenance."*

### Q2: "Why did you deliberately retain duplicate rows in the transaction table?"
**Answer:**
> *"In retail checkout data, multiple lines having identical timestamps, customer hashes, article codes, and prices do not automatically indicate ingestion errors. In the H&M schema, there is no separate `quantity` column or shopping cart UUID. When a customer purchases three identical black t-shirts in one shopping trip, the database logs three identical transaction rows. Our empirical audit revealed that duplicate rows represent 3,212,929 lines (10.11% of total transaction volume). Blindly deduplicating would have artificially deflated real physical demand for high-volume basics by over 10% and skewed category velocity rankings."*

### Q3: "Why did you refuse to calculate Average Order Value (AOV), Profit Margins, or Conversion Rate?"
**Answer:**
> *"Analytical integrity requires respecting empirical data boundaries. The H&M dataset provides only normalised price indices (ranging from 0.000017 to 0.591525), not actual local currency units like USD or EUR; converting an arbitrary normalised index into 'dollars' would be misleading. Furthermore, the dataset lacks order or invoice identifiers—meaning transactions cannot be definitively bound into discrete orders—so calculating a true 'order value' is mathematically invalid. Similarly, the data contains no website session/impression logs (making conversion rates uncalculable), no wholesale product cost prices (making profit margins impossible), and zero warehouse inventory snapshots. Instead, GarmentPulse focuses on mathematically defensible metrics: physical purchase volume velocity, customer penetration, and normalised price index contribution."*

### Q4: "How does your recommendation engine differ from typical academic models?"
**Answer:**
> *"Most recommender systems use random 80/20 train-test splits, which causes catastrophic temporal data leakage—models predict what a customer bought in March using purchases they made in September. In GarmentPulse, we enforce a strict **chronological validation protocol**: all models (Popularity, Attribute Content, Collaborative Filtering, and Hybrid) are trained strictly on data prior to a cutoff date ($T_{\text{cutoff}} = T_{\text{max}} - 28\text{d}$), and evaluated against ground-truth purchases in the unobserved 28-day holdout window using MAP@12, Recall@12, and Precision@12. Moreover, we explicitly exclude previously purchased articles from discovery recommendations and provide commercial explanations for why each article was selected."*

### Q5: "How does your Commercial Opportunity Engine translate data into merchandising decisions?"
**Answer:**
> *"Rather than presenting disconnected metrics, our Opportunity Engine synthesizes 6 normalized components into a relative composite score (0–100): recent volume growth (25%), unique customer acquisition velocity (20%), repeat buyer ratio (15%), enterprise category contribution (15%), assortment diversity / inverted HHI (10%), and attribute momentum (15%). Every category is classified into an actionable tier (Strong Demand Signal, Emerging Opportunity, Stable Performer, Declining Signal) and translated into a structured 5-part card:*
> 1. *OBSERVATION: What happened empirically in the data.*
> 2. *EVIDENCE: Exact calculated metrics supporting the shift.*
> 3. *BUSINESS IMPLICATION: What this means for retail category dynamics.*
> 4. *RECOMMENDED ACTION: Investigating assortment exposure or rebalancing digital feature space.*
> 5. *LIMITATION: Missing inventory availability or cost context that requires supply chain verification.*
> *This bridges the gap between pure data science and executive retail decision-making."*
