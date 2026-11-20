# GarmentPulse — Comprehensive Dataset Audit Report
**Source:** H&M Personalized Fashion Recommendations (Kaggle Official Dataset)  
**Audit Executed:** Verified against actual source data files  
**Auditor:** GarmentPulse Data Engineering & Analytics Lead  

---

## 1. Executive Summary & Raw File Manifest

| File Name | File Size on Disk | Record Count | Primary Identifier | Field Count |
|---|---|---|---|---|
| `transactions_train.csv` | 3,326.4 MB | 31,788,324 | `customer_id` + `article_id` + `t_dat` | 5 |
| `articles.csv` | 34.5 MB | 105,542 | `article_id` | 25 |
| `customers.csv` | 197.5 MB | 1,371,980 | `customer_id` | 7 |

---

## 2. Transactions Table Audit (`transactions_train.csv`)

### 2.1 Scope & Volume Metrics
- **Total Observed Purchase Records:** 31,788,324
- **Date Range:** `2018-09-20 00:00:00` to `2020-09-22 00:00:00` (approx. 2 years of weekly fashion demand)
- **Unique Purchasing Customers:** 1,362,281
- **Unique Articles Purchased:** 104,547 (out of 105,542 catalogue items)
- **Catalog Coverage:** 99.06% of catalogue articles observed in transactions

### 2.2 Normalised Purchase-Price Index Distribution
*Note: In compliance with project guidelines, prices are strictly normalised indices (range 0 to 1) and must NOT be interpreted as actual currency.*
- **Mean Price Index:** 0.027829
- **Standard Deviation:** 0.019181
- **Median Price Index:** 0.025407
- **25th Percentile (P25):** 0.015814
- **75th Percentile (P75):** 0.033881
- **Min / Max Observed Index:** 0.000017 / 0.591525

### 2.3 Sales Channel Distribution
*Note: Values are maintained neutrally as Channel 1 and Channel 2 pending verified mapping.*
| Sales Channel ID | Purchase Volume (Lines) | Unique Customers | Volume Share (%) |
|---|---|---|---|
| **Channel 1** | 9,408,462 | 737,118 | 29.6% |
| **Channel 2** | 22,379,862 | 1,108,418 | 70.4% |

### 2.4 Duplicate Transaction Investigation
- **Duplicate Line Count:** 3,212,929 identical records (10.11% of total volume)
- **Distinct Multi-line Baskets:** 2,717,844
- **Analytical Decision:** In retail checkout data lacking item-quantity columns or order UUIDs, multiple identical lines indicate a customer buying multiple units of the same article on the same day. **These rows are deliberately retained** to preserve true physical purchase volume.

### 2.5 Data Quality & Missingness
- Missing `t_dat`: 0
- Missing `customer_id`: 0
- Missing `article_id`: 0
- Missing `price`: 0
- Missing `sales_channel_id`: 0
- *Result:* Zero missing values across all primary transactional fields.

---

## 3. Articles Catalogue Audit (`articles.csv`)

### 3.1 Taxonomy Breakdown
- **Unique Articles (`article_id`):** 105,542
- **Unique Product Codes (`product_code`):** 47,224
- **Unique Product Types:** 131
- **Unique Product Groups:** 19
- **Unique Graphical Appearances:** 30
- **Unique Colour Groups:** 50
- **Unique Perceived Colour Values:** 8
- **Unique Perceived Master Colours:** 20
- **Unique Departments:** 250
- **Unique Index Groups:** 5
- **Unique Sections:** 56
- **Unique Garment Groups:** 21

### 3.2 Top 5 Product Groups by Catalogue Volume
| Product Group | Article Count | Share (%) |
|---|---|---|
| Garment Upper body | 42,741 | 40.5% |
| Garment Lower body | 19,812 | 18.77% |
| Garment Full body | 13,292 | 12.59% |
| Accessories | 11,158 | 10.57% |
| Underwear | 5,490 | 5.2% |

### 3.3 Top 5 Colour Groups
| Colour Group | Article Count | Share (%) |
|---|---|---|
| Black | 22,670 | 21.48% |
| Dark Blue | 12,171 | 11.53% |
| White | 9,542 | 9.04% |
| Light Pink | 5,811 | 5.51% |
| Grey | 4,487 | 4.25% |

### 3.4 Missing Values in Articles
- Missing `detail_desc`: 416 (0.39%)
- All identifier, taxonomy, and colour fields have 100% completeness.

---

## 4. Customers Audit (`customers.csv`)

### 4.1 Profile Metrics
- **Total Customer Profiles:** 1,371,980
- **Unique Customers:** 1,371,980
- **Active Purchasing Penetration:** 99.29% of registered customers have at least one recorded purchase.

### 4.2 Demographics (Age)
- **Mean Age:** 36.4 years (Std: 14.3)
- **Median Age:** 32 years
- **Interquartile Range:** 24 to 49 years
- **Min / Max Age:** 16 / 99
- **Missing Age Values:** 15,861 (1.16%)

### 4.3 Club Membership & Fashion News Engagement
| Club Member Status | Customer Count | Share (%) |
|---|---|---|
| ACTIVE | 1,272,491 | 92.75% |
| PRE-CREATE | 92,960 | 6.78% |
| NULL | 6,062 | 0.44% |
| LEFT CLUB | 467 | 0.03% |

| Fashion News Cadence | Customer Count | Share (%) |
|---|---|---|
| NONE | 877,711 | 63.97% |
| Regularly | 477,416 | 34.8% |
| NULL | 16,009 | 1.17% |
| Monthly | 842 | 0.06% |
| None | 2 | 0.0% |

- Missing `FN` flag: 895,050 (65.24% - treated as False/unsubscribed)
- Missing `Active` flag: 907,576 (66.15% - treated as Inactive)

---

## 5. Non-Negotiable Analytical Boundaries & Disclaimers

In strict adherence to Project Omega specifications, the following empirical limits are codified:

- **LIMITATION:** Price values are normalised — not actual currency amounts.
- **LIMITATION:** No order/invoice identifiers — cannot determine basket composition.
- **LIMITATION:** No inventory/stock data — cannot assess product availability.
- **LIMITATION:** No cost or margin data — cannot calculate profitability.
- **LIMITATION:** No website session/click data — cannot measure conversion.
- **LIMITATION:** No return event data — purchase volumes include unreturned items.
- **LIMITATION:** No discount labels — cannot assess promotional impact.
- **LIMITATION:** First observed purchase ≠ product launch date.
- **LIMITATION:** Last observed purchase ≠ product discontinuation.
- **LIMITATION:** Transaction dates ≠ order IDs.
- **LIMITATION:** Duplicate rows may represent multiple legitimate purchases.

---
*Report auto-generated by GarmentPulse Data Profiler.*
