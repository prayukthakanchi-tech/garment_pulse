# GarmentPulse — Comprehensive Data Dictionary & Metrics Glossary
**Source:** H&M Personalized Fashion Recommendations (Kaggle Research Competition)  
**Entities:** Transactions, Articles Catalogue, Customer Profiles

---

## 1. Entity: `transactions` (`transactions_train.csv`)

| Field Name | Storage Type | Nullable | Description & Domain Constraints | Sample Value |
|---|---|---|---|---|
| `t_dat` | `DATE` | No | Date of the purchase transaction event. Range: `2018-09-20` to `2020-09-22`. | `2019-06-15` |
| `customer_id` | `VARCHAR` | No | 64-character hexadecimal SHA-256 hashed customer identifier. FK → `customers.customer_id`. | `000058a12d...` |
| `article_id` | `VARCHAR` | No | 10-character string article identifier with mandatory leading zeros. FK → `articles.article_id`. | `0108775015` |
| `price` | `DOUBLE` | No | **Dimensionless normalised purchase-price index.** Range: $0.000017$ to $0.591525$. **Must NOT be interpreted or converted to real currency.** | `0.025407` |
| `sales_channel_id` | `INTEGER` | No | Sales channel identifier: `1` (29.6% volume) or `2` (70.4% volume). Neutrally labeled as Channel 1 and Channel 2. | `2` |

*Note on Duplicate Rows:* The dataset contains no line-item quantity column or cart UUID. When a customer purchases multiple units of the same article on the same day, separate identical records are logged. These duplicate lines are preserved to maintain accurate physical unit demand.

---

## 2. Entity: `articles` (`articles.csv`)

| Field Name | Storage Type | Nullable | Description & Domain | Sample Value |
|---|---|---|---|---|
| `article_id` | `VARCHAR` | No | Primary Key. 10-digit unique SKU identifier with leading zero preserved. | `0108775015` |
| `product_code` | `VARCHAR` | No | 7-digit parent product design code. Multiple articles share one product code across colors. | `0108775` |
| `prod_name` | `VARCHAR` | No | Commercial article display title. | `Strap top` |
| `product_type_no` | `INTEGER` | No | Numeric taxonomy code for product type. | `253` |
| `product_type_name` | `VARCHAR` | No | Granular product type classification (131 distinct values). | `Vest top` |
| `product_group_name` | `VARCHAR` | No | High-level product group (19 distinct values). | `Garment Upper body` |
| `graphical_appearance_no` | `INTEGER` | No | Numeric code for visual appearance/pattern. | `1010016` |
| `graphical_appearance_name` | `VARCHAR` | No | Visual appearance label (e.g. Solid, Stripe, All over pattern). | `Solid` |
| `colour_group_code` | `INTEGER` | No | Numeric code for color group. | `9` |
| `colour_group_name` | `VARCHAR` | No | Broad colour name (50 distinct values). | `Black` |
| `perceived_colour_value_id` | `INTEGER` | No | Numeric code for perceived color luminosity. | `4` |
| `perceived_colour_value_name`| `VARCHAR` | No | Luminosity label (e.g. Dark, Light, Medium dusty). | `Dark` |
| `perceived_colour_master_id` | `INTEGER` | No | Numeric code for parent master color. | `5` |
| `perceived_colour_master_name`| `VARCHAR`| No | Master color category (20 distinct values). | `Black` |
| `department_no` | `INTEGER` | No | Numeric department code. | `1676` |
| `department_name` | `VARCHAR` | No | Commercial merchandising department (250 distinct values). | `Jersey Basic` |
| `index_code` | `VARCHAR` | No | High-level division code (e.g. A, B, C, D, F). | `A` |
| `index_name` | `VARCHAR` | No | High-level division name (e.g. Ladieswear, Menswear, Baby). | `Ladieswear` |
| `index_group_no` | `INTEGER` | No | Numeric code for index group. | `1` |
| `index_group_name` | `VARCHAR` | No | Broad business division (5 distinct values). | `Ladieswear` |
| `section_no` | `INTEGER` | No | Commercial section numeric code. | `16` |
| `section_name` | `VARCHAR` | No | Store section label (56 distinct values). | `Womens Everyday Basics` |
| `garment_group_no` | `INTEGER` | No | Manufacturing garment group numeric code. | `1002` |
| `garment_group_name` | `VARCHAR` | No | Production garment group (21 distinct values). | `Jersey Basic` |
| `detail_desc` | `VARCHAR` | Yes | Long free-text product description. Nulls: 416 (0.39%). | `Jersey top with narrow shoulder straps.` |

---

## 3. Entity: `customers` (`customers.csv`)

| Field Name | Storage Type | Nullable | Description & Domain | Sample Value |
|---|---|---|---|---|
| `customer_id` | `VARCHAR` | No | Primary Key. 64-character SHA-256 hashed customer identifier. | `00000dbacae5...` |
| `fn` | `DOUBLE` | Yes | Fashion News newsletter opt-in flag ($1.0$ or NULL). Nulls treated as 0 (unsubscribed). | `1.0` |
| `active` | `DOUBLE` | Yes | Active club member flag ($1.0$ or NULL). Nulls treated as 0 (inactive). | `1.0` |
| `club_member_status` | `VARCHAR` | Yes | Membership tier status: `ACTIVE`, `PRE-CREATE`, `LEFT CLUB`. Nulls: 6,062. | `ACTIVE` |
| `fashion_news_frequency` | `VARCHAR` | Yes | Newsletter delivery cadence: `NONE`, `Regularly`, `Monthly`. Nulls: 16,009. | `Regularly` |
| `age` | `DOUBLE` | Yes | Customer reported age in years. Range: $16$ to $99$. Nulls: 15,861 (1.16%). | `28.0` |
| `postal_code` | `VARCHAR` | No | Hashed postal code string. | `52043ee2162c...` |

---

## 4. Derived Analytical Metrics Glossary

- **Purchase Volume:** Count of physical item transaction checkout lines recorded within a specified timeframe.
- **Normalised Purchase-Price Contribution:** Sum of dimensionless transaction price indices. Explicitly NOT gross revenue.
- **Herfindahl-Hirschman Index (HHI):** Sum of squared article market shares within a category ($0 \le \text{HHI} \le 10,000$). High HHI indicates demand concentrated in few SKUs.
- **Recency ($R$):** Days elapsed between customer's last recorded transaction and dataset reference date ($T_{\text{max}} = 2020-09-22$).
- **Frequency ($F$):** Count of distinct calendar dates on which a customer completed a checkout.
- **Repeat Activity Rate (%):** Percentage of an acquisition cohort active in a subsequent month. Strictly physical repeat transactions, NOT web browsing retention.
- **MAP@12 (Mean Average Precision):** Evaluates ranking quality of recommendation algorithms on historical holdout purchases.
- **WAPE (Weighted Absolute Percentage Error):** Demand forecasting error metric defined as $\frac{\sum |y - \hat{y}|}{\sum y}$.
- **Relative Commercial Opportunity Score (0–100):** Weighted multi-criteria composite heuristic ranking category expansion potential.
