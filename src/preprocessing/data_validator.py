"""
GarmentPulse — Data Validator
Rule-based data quality validation and reporting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import duckdb

from config.settings import DATA_LIMITATIONS, REPORTS_DIR


class DataValidator:
    """Executes rule-based data quality checks across transactions, articles, and customers."""

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def validate_transactions(self, table_name: str = "transactions") -> List[Dict[str, Any]]:
        """Validate transaction schema, nulls, positive prices, valid channels, and date ranges."""
        findings = []

        # Null checks
        null_res = self.conn.execute(f"""
            SELECT
                SUM(CASE WHEN t_dat IS NULL THEN 1 ELSE 0 END) AS null_dates,
                SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_custs,
                SUM(CASE WHEN article_id IS NULL THEN 1 ELSE 0 END) AS null_arts,
                SUM(CASE WHEN price IS NULL THEN 1 ELSE 0 END) AS null_prices,
                SUM(CASE WHEN sales_channel_id IS NULL THEN 1 ELSE 0 END) AS null_channels
            FROM {table_name}
        """).fetchone()

        findings.append({
            "check": "Transactions Primary Key / Critical Columns Not Null",
            "table": table_name,
            "status": "PASS" if all(x == 0 for x in null_res) else "FAIL",
            "details": f"Nulls found: t_dat={null_res[0]}, customer_id={null_res[1]}, article_id={null_res[2]}, price={null_res[3]}, sales_channel_id={null_res[4]}",
            "impact": "Core identifiers and transaction facts must be 100% complete."
        })

        # Price range check (prices must be strictly > 0 and <= 1.0)
        price_check = self.conn.execute(f"""
            SELECT
                COUNT(CASE WHEN price <= 0 THEN 1 END) AS non_positive_prices,
                COUNT(CASE WHEN price > 1.0 THEN 1 END) AS out_of_bounds_prices
            FROM {table_name}
        """).fetchone()

        findings.append({
            "check": "Price Range Normalisation (0 < price <= 1.0)",
            "table": table_name,
            "status": "PASS" if price_check[0] == 0 and price_check[1] == 0 else "WARNING",
            "details": f"Non-positive prices: {price_check[0]}, Prices > 1.0: {price_check[1]}",
            "impact": "Normalised purchase-price indices must fall within valid positive range."
        })

        # Sales channel check
        channel_check = self.conn.execute(f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE sales_channel_id NOT IN (1, 2)
        """).fetchone()[0]

        findings.append({
            "check": "Valid Sales Channel IDs (1 or 2)",
            "table": table_name,
            "status": "PASS" if channel_check == 0 else "FAIL",
            "details": f"Rows with unknown sales_channel_id: {channel_check}",
            "impact": "Ensure transactions map to known distribution channels."
        })

        # Date validity check
        date_check = self.conn.execute(f"""
            SELECT MIN(t_dat), MAX(t_dat), COUNT(CASE WHEN t_dat > CURRENT_DATE THEN 1 END)
            FROM {table_name}
        """).fetchone()

        findings.append({
            "check": "Temporal Consistency (No Future Dates)",
            "table": table_name,
            "status": "PASS" if date_check[2] == 0 else "FAIL",
            "details": f"Observed span: {date_check[0]} to {date_check[1]}. Future dates: {date_check[2]}",
            "impact": "Transactions must reflect historical observation periods."
        })

        return findings

    def validate_articles(self, table_name: str = "articles") -> List[Dict[str, Any]]:
        """Validate articles catalogue integrity."""
        findings = []

        # Unique PK check
        art_pk = self.conn.execute(f"""
            SELECT COUNT(*), COUNT(DISTINCT article_id)
            FROM {table_name}
        """).fetchone()

        findings.append({
            "check": "Articles Unique Primary Key (`article_id`)",
            "table": table_name,
            "status": "PASS" if art_pk[0] == art_pk[1] else "FAIL",
            "details": f"Total rows: {art_pk[0]:,}, Unique article_ids: {art_pk[1]:,}",
            "impact": "Every article must have a unique identifier without collisions."
        })

        # Leading zeroes preserved (length check)
        len_check = self.conn.execute(f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE LENGTH(article_id) != 10
        """).fetchone()[0]

        findings.append({
            "check": "Article Identifier Formatting (10-digit string with leading zeroes)",
            "table": table_name,
            "status": "PASS" if len_check == 0 else "FAIL",
            "details": f"Articles with length != 10: {len_check}",
            "impact": "Prevents silent integer truncation of leading zeros (e.g. 0108775015)."
        })

        return findings

    def validate_customers(self, table_name: str = "customers") -> List[Dict[str, Any]]:
        """Validate customer records integrity."""
        findings = []

        # Unique PK
        cust_pk = self.conn.execute(f"""
            SELECT COUNT(*), COUNT(DISTINCT customer_id)
            FROM {table_name}
        """).fetchone()

        findings.append({
            "check": "Customers Unique Primary Key (`customer_id`)",
            "table": table_name,
            "status": "PASS" if cust_pk[0] == cust_pk[1] else "FAIL",
            "details": f"Total rows: {cust_pk[0]:,}, Unique customer_ids: {cust_pk[1]:,}",
            "impact": "Customer profile records must be uniquely addressable."
        })

        # Age bounds check
        age_check = self.conn.execute(f"""
            SELECT 
                COUNT(CASE WHEN age < 10 THEN 1 END) AS underage,
                COUNT(CASE WHEN age > 105 THEN 1 END) AS overage,
                COUNT(CASE WHEN age IS NULL THEN 1 END) AS missing_age
            FROM {table_name}
        """).fetchone()

        findings.append({
            "check": "Customer Age Plausibility & Missingness",
            "table": table_name,
            "status": "PASS" if age_check[0] == 0 and age_check[1] == 0 else "WARNING",
            "details": f"Ages < 10: {age_check[0]}, Ages > 105: {age_check[1]}, Missing ages: {age_check[2]:,}",
            "impact": "Demographic analyses must isolate null or extreme outliers."
        })

        return findings

    def validate_referential_integrity(
        self,
        tx_table: str = "transactions",
        art_table: str = "articles",
        cust_table: str = "customers",
    ) -> List[Dict[str, Any]]:
        """Verify foreign key relations between transactions and dimensions."""
        findings = []

        # Missing articles in catalogue
        orphan_arts = self.conn.execute(f"""
            SELECT COUNT(DISTINCT t.article_id)
            FROM {tx_table} t
            LEFT JOIN {art_table} a ON t.article_id = a.article_id
            WHERE a.article_id IS NULL
        """).fetchone()[0]

        findings.append({
            "check": "Referential Integrity: Transactions → Articles",
            "table": tx_table,
            "status": "PASS" if orphan_arts == 0 else "WARNING",
            "details": f"Transactions referencing uncatalogued articles: {orphan_arts}",
            "impact": "Ensures every purchased article can be enriched with category metadata."
        })

        # Missing customers in profiles
        orphan_custs = self.conn.execute(f"""
            SELECT COUNT(DISTINCT t.customer_id)
            FROM {tx_table} t
            LEFT JOIN {cust_table} c ON t.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        """).fetchone()[0]

        findings.append({
            "check": "Referential Integrity: Transactions → Customers",
            "table": tx_table,
            "status": "PASS" if orphan_custs == 0 else "WARNING",
            "details": f"Transactions referencing unregistered customers: {orphan_custs}",
            "impact": "Ensures transaction activity maps back to known customer entities."
        })

        return findings

    def run_all_validations(self) -> List[Dict[str, Any]]:
        """Run all test suites and collect findings."""
        findings = []
        findings.extend(self.validate_transactions())
        findings.extend(self.validate_articles())
        findings.extend(self.validate_customers())
        findings.extend(self.validate_referential_integrity())
        return findings

    def generate_quality_report(self, output_path: str | Path | None = None) -> str:
        """Produce the comprehensive reports/data_quality.md document."""
        findings = self.run_all_validations()

        pass_count = sum(1 for f in findings if f["status"] == "PASS")
        warn_count = sum(1 for f in findings if f["status"] == "WARNING")
        fail_count = sum(1 for f in findings if f["status"] == "FAIL")

        md = f"""# GarmentPulse — Data Quality & Integrity Report
**Target Platform:** GarmentPulse Decision Intelligence Engine  
**Status:** {pass_count} PASS | {warn_count} WARNING | {fail_count} FAIL  

---

## 1. Automated Validation Suite Results

| Validation Check | Target Entity | Status | Technical Details | Architectural Impact |
|---|---|---|---|---|
"""
        for f in findings:
            badge = "🟢 PASS" if f["status"] == "PASS" else ("🟡 WARNING" if f["status"] == "WARNING" else "🔴 FAIL")
            md += f"| {f['check']} | `{f['table']}` | {badge} | {f['details']} | {f['impact']} |\n"

        md += f"""
---

## 2. Duplicate Row Pattern Investigation

### Analysis
In retail transactional databases, multiple lines having identical `t_dat`, `customer_id`, `article_id`, and `price` can represent:
1. Technical ingestion double-posting.
2. Legitimate consumer purchasing of multiple quantities of the same item during a shopping trip.

### Empirical Evidence & Resolution
- **Absence of Quantity Field:** The H&M transaction schema contains no `quantity` or `units` integer column.
- **Absence of Basket/Cart UUID:** Individual line items are recorded flatly per customer per date.
- **Resolution:** As per enterprise data engineering standards, duplicate transaction rows are **intentionally preserved**. Dropping them would artificially deflate product purchase volumes and distort demand momentum calculations.

---

## 3. Data Cleaning Decisions Log

1. **Identifier Preservation:** Both `article_id` and `customer_id` are ingested with explicit string data types (`pl.Utf8` in Polars, `VARCHAR` in DuckDB). This completely prevents truncation of leading zeros in article codes (e.g. `0108775015`).
2. **Missing Demographic Handling:** Customer `age` has ~1.16% missing values. These are preserved as `NULL` during aggregation rather than imputed with arbitrary means to avoid biasing cohort and segmentation analyses.
3. **Engagement Flags:** Nulls in `FN` (Fashion News) and `Active` are interpreted as `0` / inactive in engagement filters, without deleting customer records.
4. **Catalogue Metadata:** Null values in article `detail_desc` are replaced with empty string or product name fallback during natural language and recommendation processing.

---

## 4. Formal Data Limitations

"""
        for lim in DATA_LIMITATIONS:
            md += f"- **LIMITATION:** {lim}\n"

        md += """
---
*Report auto-generated by GarmentPulse Data Validator.*
"""
        out_file = Path(output_path) if output_path else REPORTS_DIR / "data_quality.md"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(md, encoding="utf-8")
        print(f"[validator] ✓ Quality report written to {out_file}")
        return md
