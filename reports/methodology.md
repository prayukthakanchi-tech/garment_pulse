# GarmentPulse — Technical Analytics Methodology Report
**Platform:** GarmentPulse — Fashion Category & Customer Decision Intelligence Platform  
**Architecture:** Polars (Streaming Ingestion) → Parquet → DuckDB (Columnar OLAP) → Python ML → Streamlit

---

## 1. Data Engineering Architecture

The transaction dataset comprises **31,788,324 records (3.48 GB uncompressed CSV)**. Loading this full dataset into Pandas requires excessive memory and risks memory exhaustion.

GarmentPulse implements a high-performance streaming OLAP pipeline:
1. **Streaming Ingestion (Polars 2.x):** Uses `pl.scan_csv` with explicit schema overrides (`t_dat` as String, `customer_id` as String, `article_id` as String, `price` as Float64, `sales_channel_id` as Int32). All IDs are strictly kept as strings to preserve leading zeros (e.g. `0108775015`).
2. **Columnar Parquet Conversion:** Stream-sinks CSV data directly to snappy-compressed Parquet files via `lf.sink_parquet()`. Transactions compress from 3,488 MB to 447.8 MB (87.2% compression ratio) while preserving zero-copy columnar scanning.
3. **DuckDB Embedded OLAP Engine:** Connects directly to persistent database file `garmentpulse.duckdb`. DuckDB queries Parquet with vectorized SIMD execution, completing aggregations over 31.8M rows in sub-second to single-digit second latencies.
4. **Duplicate Row Retention Protocol:** Identical transaction rows (same `t_dat`, `customer_id`, `article_id`, `price`) represent multi-unit checkouts (basket multiplicity). Because the source dataset contains no `quantity` column, duplicate records are intentionally preserved to maintain true physical purchasing volume.

---

## 2. Category Intelligence & Concentration Methodology

### 2.1 Category Demand Momentum
Calculated by comparing transaction volume across two consecutive 4-week observation windows:
$$\text{Volume Growth Rate} = \frac{V_{\text{recent}} - V_{\text{previous}}}{V_{\text{previous}}}$$
$$\text{Customer Growth Rate} = \frac{C_{\text{recent}} - C_{\text{previous}}}{C_{\text{previous}}}$$
A minimum threshold of $V_{\text{recent}} + V_{\text{previous}} \ge 100$ transactions is enforced to eliminate low-sample volatility.

### 2.2 Product Demand Concentration (HHI)
To assess whether a category's demand relies on a wide variety of articles or a tiny handful of viral items, GarmentPulse adapts the **Herfindahl-Hirschman Index (HHI)** at the article level within each category:
$$\text{HHI} = \sum_{i=1}^{N} s_i^2$$
where $s_i$ is article $i$'s percentage share of category purchase volume ($0 \le s_i \le 100$).
- $\text{HHI} < 1,500$: Broad Assortment / Low Concentration (demand spread across many SKUs)
- $1,500 \le \text{HHI} \le 2,500$: Moderate Concentration
- $\text{HHI} > 2,500$: High Concentration (demand heavily concentrated in a few SKUs; high single-SKU vulnerability)

---

## 3. Customer Lifecycle & Cohort Methodology

### 3.1 RFM-Inspired Segmentation Rules
- **Reference Date ($T_{\text{max}}$):** The maximum transaction date observed in the dataset (2020-09-22).
- **Recency ($R$):** Days elapsed since customer's last recorded purchase date: $R = T_{\text{max}} - T_{\text{last}}$.
- **Customer Age ($A$):** Days elapsed since customer's first observed purchase: $A = T_{\text{max}} - T_{\text{first}}$.
- **Frequency ($F$):** Distinct calendar dates on which the customer made a purchase.

| Segment Tier | Mathematical Rule Condition |
|---|---|
| **Frequent Buyers** | $F \ge 10 \text{ days} \land R \le 30 \text{ days}$ |
| **Emerging Customers** | $A \le 90 \text{ days} \land F \ge 2 \text{ trips}$ |
| **Recently Active** | $R \le 30 \text{ days}$ |
| **Cooling Customers** | $31 \text{ days} \le R \le 90 \text{ days}$ |
| **At-Risk Customers** | $91 \text{ days} \le R \le 180 \text{ days}$ |
| **Dormant Customers** | $R > 180 \text{ days}$ |

### 3.2 Monthly Cohort Repeat Purchasing Matrix
Cohorts are defined by customer's calendar month of first observed purchase.
For cohort $C_m$ and subsequent month period $k \ge 0$:
$$\text{Repeat Activity Rate}_{m, k} = \frac{|U_{m, k}|}{|C_m|} \times 100\%$$
where $|C_m|$ is the initial acquisition cohort size, and $|U_{m, k}|$ is the number of cohort customers with recorded checkout activity in month $m + k$.
*Explicit Caveat:* This metric captures physical transaction repeat activity, not web browsing or platform session retention.

---

## 4. Product Lifecycle Classification Protocol

Articles are classified into 5 distinct lifecycle velocity states:
1. **Low Activity:** Lifetime total observed purchases $< 5$ lines.
2. **Emerging:** First observed purchase within recent 8 weeks ($T_{\text{first}} > T_{\text{max}} - 56\text{d}$) AND recent 4-week volume $\ge 5$ units.
3. **Accelerating:** Recent 4-week volume grew $> +20\%$ vs previous 4 weeks AND recent volume $\ge 5$ units.
4. **Slowing:** Recent 4-week volume contracted $< -20\%$ vs previous 4 weeks.
5. **Stable:** All remaining active SKUs operating within $[-20\%, +20\%]$ growth velocity.

*Proxy Notice:* First observed purchase is not a verified factory launch date. Last observed purchase is not verified discontinuation.

---

## 5. Recommendation System & Chronological Validation

### 5.1 Hybrid Scoring Architecture
Combines:
1. **Popularity Baseline ($S_{\text{pop}}$):** Observed purchase volume of candidate article in recent training window.
2. **Attribute Content Matching ($S_{\text{content}}$):** Weighted cosine alignment between customer's attribute affinity vector (departments, garment groups, colours, product types) and candidate article metadata.
3. **Collaborative Filtering ($S_{\text{collab}}$):** Co-purchase frequency on customer historical closet items.
$$\text{Score}_{\text{hybrid}} = 0.20 \cdot S_{\text{pop}} + 0.40 \cdot S_{\text{content}} + 0.40 \cdot S_{\text{collab}}$$

### 5.2 Strict Chronological Validation Protocol
**No random train-test splitting.** All recommendation models are trained on transactions occurring before a fixed cutoff date ($T_{\text{cutoff}} = T_{\text{max}} - 28\text{d}$).
Models are evaluated on actual future customer purchases occurring in the 28-day holdout window.
Evaluated metrics:
- **MAP@12 (Mean Average Precision):** Evaluates ranking position of relevant recommendations.
- **Recall@12:** Proportion of holdout purchases captured in top 12 recommendations.
- **Precision@12:** Proportion of top 12 recommendations that were purchased.
- **Catalogue Coverage:** Percentage of catalogue SKUs recommended at least once across test customers.

---

## 6. Demand Forecasting & Backtesting Protocol

### 6.1 Models Evaluated
1. **Seasonal Naive Baseline:** $y_{t+h} = y_{t+h-52}$ (prior year seasonal anchor).
2. **Moving Average Baseline:** Constant projection of 4-week trailing average.
3. **Holt-Winters Exponential Smoothing:** Multiplicative/additive level, trend, and seasonal index updates with 95% Gaussian prediction intervals.
4. **LightGBM Autoregressive Regression:** Recursive walk-forward regression with lag features ($1, 2, 3, 4, 8, 12$), rolling statistics, and calendar features.

### 6.2 Backtest Error Metrics
Evaluated over an unobserved 8-week holdout window:
$$\text{MAE} = \frac{1}{H} \sum_{h=1}^H |y_h - \hat{y}_h|$$
$$\text{RMSE} = \sqrt{\frac{1}{H} \sum_{h=1}^H (y_h - \hat{y}_h)^2}$$
$$\text{WAPE} = \frac{\sum_{h=1}^H |y_h - \hat{y}_h|}{\sum_{h=1}^H y_h}$$
*Boundary:* Forecasts project physical purchase volumes. They do NOT calculate inventory orders or replenishment safety stocks.

---

## 7. Commercial Opportunity Scoring Formula

The Opportunity Score ($0 \le \text{Score} \le 100$) integrates 6 normalized components:
$$\text{Score} = 100 \times \left[ 0.25 S_{\text{vol}} + 0.20 S_{\text{cust}} + 0.15 S_{\text{repeat}} + 0.15 S_{\text{contrib}} + 0.10 S_{\text{diversity}} + 0.15 S_{\text{momentum}} \right]$$
All component values are min-max scaled $[0, 1]$ across candidate categories.
- $S_{\text{diversity}} = 1 - \text{Norm}(\text{HHI})$: Rewards broad, resilient product demand.
- $S_{\text{momentum}} = \frac{S_{\text{vol}} + S_{\text{cust}}}{2}$: Captures simultaneous customer and unit velocity expansion.

Every classification produces a structured 5-part recommendation:
`OBSERVATION` → `EVIDENCE` → `BUSINESS IMPLICATION` → `RECOMMENDED ACTION` → `LIMITATION`.
