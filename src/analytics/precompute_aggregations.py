"""
GarmentPulse — Precompute Analytical Aggregations
Generates optimized, compressed Parquet summary datasets directly from DuckDB.
Eliminates 10s-50s cold table scans across 31.8M transactions while preserving 100% exact numerical accuracy.
"""

import sys
import time
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import duckdb
from config.settings import (
    DUCKDB_PATH,
    PROCESSED_DIR,
    ACCELERATION_THRESHOLD,
    DECLINE_THRESHOLD,
    MIN_PRODUCT_PURCHASES,
)


def run_precomputations(db_path: Path = DUCKDB_PATH, out_dir: Path = PROCESSED_DIR) -> None:
    """Precompute reusable analytical summaries from DuckDB to Parquet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path), read_only=True)
    t_start = time.time()
    print("=" * 65)
    print("STARTING ANALYTICAL PRECOMPUTATION PIPELINE")
    print(f"Source Database: {db_path}")
    print(f"Target Directory: {out_dir}")
    print("=" * 65)

    # 1. Macro Portfolio KPIs
    t0 = time.time()
    kpi_file = out_dir / "agg_portfolio_kpis.parquet"
    conn.execute(f"""
        COPY (
            SELECT
                COUNT(*) AS total_volume,
                COUNT(DISTINCT customer_id) AS total_customers,
                COUNT(DISTINCT article_id) AS total_articles,
                ROUND(AVG(price), 6) AS avg_price_index
            FROM transactions
        ) TO '{kpi_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {kpi_file.name} generated in {time.time()-t0:.2f}s")

    # 2. Complete Article Performance & Lifecycle Status (All 105,542 articles)
    t0 = time.time()
    art_file = out_dir / "agg_article_performance.parquet"
    conn.execute(f"""
        COPY (
            WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
            periods AS (
                SELECT
                    max_date,
                    max_date - INTERVAL 28 DAYS AS recent_start,
                    max_date - INTERVAL 56 DAYS AS prev_start,
                    max_date - INTERVAL 56 DAYS AS emerging_cutoff
                FROM bounds
            ),
            txn_art AS (
                SELECT
                    article_id,
                    MIN(t_dat) AS first_observed_purchase,
                    MAX(t_dat) AS last_observed_purchase,
                    COUNT(DISTINCT DATE_TRUNC('week', t_dat)) AS active_weeks,
                    COUNT(*) AS total_purchase_lines,
                    COUNT(DISTINCT customer_id) AS unique_customers,
                    ROUND(AVG(price), 6) AS avg_price_index,
                    COUNT(CASE WHEN t_dat > p.recent_start THEN 1 END) AS recent_4wk_volume,
                    COUNT(CASE WHEN t_dat <= p.recent_start AND t_dat > p.prev_start THEN 1 END) AS prev_4wk_volume
                FROM transactions
                CROSS JOIN periods p
                GROUP BY article_id
            ),
            classified AS (
                SELECT
                    t.*,
                    CASE
                        WHEN t.prev_4wk_volume > 0 THEN
                            ROUND((t.recent_4wk_volume - t.prev_4wk_volume) * 1.0 / t.prev_4wk_volume, 4)
                        WHEN t.recent_4wk_volume > 0 THEN 1.0
                        ELSE 0.0
                    END AS volume_growth_rate,
                    CASE
                        WHEN t.total_purchase_lines < {MIN_PRODUCT_PURCHASES} THEN 'Low Activity'
                        WHEN t.first_observed_purchase > (SELECT emerging_cutoff FROM periods)
                             AND t.recent_4wk_volume >= 5 THEN 'Emerging'
                        WHEN t.prev_4wk_volume > 0
                             AND ((t.recent_4wk_volume - t.prev_4wk_volume) * 1.0 / t.prev_4wk_volume) > {ACCELERATION_THRESHOLD}
                             AND t.recent_4wk_volume >= 5 THEN 'Accelerating'
                        WHEN t.prev_4wk_volume > 0
                             AND ((t.recent_4wk_volume - t.prev_4wk_volume) * 1.0 / t.prev_4wk_volume) < {DECLINE_THRESHOLD} THEN 'Slowing'
                        ELSE 'Stable'
                    END AS lifecycle_status
                FROM txn_art t
            )
            SELECT
                c.article_id,
                a.prod_name,
                a.product_type_name,
                a.department_name,
                a.garment_group_name,
                a.colour_group_name,
                c.first_observed_purchase,
                c.last_observed_purchase,
                c.active_weeks,
                c.total_purchase_lines,
                c.unique_customers,
                c.avg_price_index,
                c.recent_4wk_volume,
                c.prev_4wk_volume,
                c.volume_growth_rate,
                c.lifecycle_status
            FROM classified c
            JOIN articles a ON c.article_id = a.article_id
        ) TO '{art_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {art_file.name} generated in {time.time()-t0:.2f}s")

    # 3. Colour Group Performance
    t0 = time.time()
    col_file = out_dir / "agg_colour_performance.parquet"
    conn.execute(f"""
        COPY (
            SELECT
                a.colour_group_name,
                COUNT(*) AS purchase_volume,
                COUNT(DISTINCT t.customer_id) AS unique_customers,
                COUNT(DISTINCT t.article_id) AS active_articles,
                ROUND(AVG(t.price), 6) AS avg_normalised_price,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS volume_share_pct
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            GROUP BY a.colour_group_name
            ORDER BY purchase_volume DESC
        ) TO '{col_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {col_file.name} generated in {time.time()-t0:.2f}s")

    # 4. Monthly Garment Group Trends
    t0 = time.time()
    gar_file = out_dir / "agg_garment_monthly.parquet"
    conn.execute(f"""
        COPY (
            SELECT
                DATE_TRUNC('month', t.t_dat) AS period_date,
                a.garment_group_name,
                COUNT(*) AS purchase_volume
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            GROUP BY DATE_TRUNC('month', t.t_dat), a.garment_group_name
            ORDER BY period_date ASC, purchase_volume DESC
        ) TO '{gar_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {gar_file.name} generated in {time.time()-t0:.2f}s")

    # 5. Colour & Garment Group Combinations
    t0 = time.time()
    comb_file = out_dir / "agg_colour_garment.parquet"
    conn.execute(f"""
        COPY (
            SELECT
                a.colour_group_name,
                a.garment_group_name,
                COUNT(*) AS purchase_volume,
                COUNT(DISTINCT t.customer_id) AS unique_customers,
                ROUND(AVG(t.price), 6) AS avg_price_index
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            GROUP BY a.colour_group_name, a.garment_group_name
            ORDER BY purchase_volume DESC
            LIMIT 100
        ) TO '{comb_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {comb_file.name} generated in {time.time()-t0:.2f}s")

    # 6. Department vs Colour Cross-Tabulation
    t0 = time.time()
    heat_file = out_dir / "agg_dept_colour.parquet"
    conn.execute(f"""
        COPY (
            WITH top_d AS (
                SELECT a.department_name
                FROM articles a
                JOIN transactions t ON a.article_id = t.article_id
                GROUP BY a.department_name ORDER BY COUNT(*) DESC LIMIT 20
            ),
            top_c AS (
                SELECT a.colour_group_name
                FROM articles a
                JOIN transactions t ON a.article_id = t.article_id
                GROUP BY a.colour_group_name ORDER BY COUNT(*) DESC LIMIT 20
            )
            SELECT
                a.department_name,
                a.colour_group_name AS attribute_value,
                COUNT(*) AS purchase_volume
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            WHERE a.department_name IN (SELECT department_name FROM top_d)
              AND a.colour_group_name IN (SELECT colour_group_name FROM top_c)
            GROUP BY a.department_name, a.colour_group_name
        ) TO '{heat_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {heat_file.name} generated in {time.time()-t0:.2f}s")

    # 7. Customer Overview Metrics
    t0 = time.time()
    cust_file = out_dir / "agg_customer_overview.parquet"
    conn.execute(f"""
        COPY (
            WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
            cust_dates AS (
                SELECT
                    customer_id,
                    MAX(t_dat) AS last_purchase,
                    COUNT(DISTINCT t_dat) AS purchase_days
                FROM transactions
                GROUP BY customer_id
            )
            SELECT
                COUNT(*) AS total_purchasing_customers,
                COUNT(CASE WHEN cd.last_purchase > b.max_date - INTERVAL 30 DAYS THEN 1 END) AS active_30d,
                COUNT(CASE WHEN cd.last_purchase > b.max_date - INTERVAL 90 DAYS THEN 1 END) AS active_90d,
                COUNT(CASE WHEN cd.last_purchase > b.max_date - INTERVAL 180 DAYS THEN 1 END) AS active_180d,
                ROUND(COUNT(CASE WHEN cd.purchase_days > 1 THEN 1 END) * 100.0 / COUNT(*), 2) AS repeat_customer_rate_pct
            FROM cust_dates cd
            CROSS JOIN bounds b
        ) TO '{cust_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {cust_file.name} generated in {time.time()-t0:.2f}s")

    # 8. Customer Segments
    t0 = time.time()
    seg_file = out_dir / "agg_customer_segments.parquet"
    conn.execute(f"""
        COPY (
            WITH bounds AS (SELECT MAX(t_dat) AS max_date FROM transactions),
            cust_features AS (
                SELECT
                    t.customer_id,
                    DATEDIFF('day', MAX(t.t_dat), b.max_date) AS recency_days,
                    DATEDIFF('day', MIN(t.t_dat), b.max_date) AS tenure_days,
                    COUNT(DISTINCT t.t_dat) AS purchase_days,
                    COUNT(*) AS total_lines,
                    SUM(t.price) AS total_price_contrib
                FROM transactions t
                CROSS JOIN bounds b
                GROUP BY t.customer_id, b.max_date
            ),
            segmented AS (
                SELECT
                    *,
                    CASE
                        WHEN purchase_days >= 10 AND recency_days <= 30 THEN 'Frequent Buyers'
                        WHEN tenure_days <= 90 AND purchase_days >= 2 THEN 'Emerging'
                        WHEN recency_days <= 30 THEN 'Recently Active'
                        WHEN recency_days BETWEEN 31 AND 90 THEN 'Cooling'
                        WHEN recency_days BETWEEN 91 AND 180 THEN 'At-Risk'
                        ELSE 'Dormant'
                    END AS segment
                FROM cust_features
            )
            SELECT
                segment,
                COUNT(*) AS customer_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS segment_share_pct,
                ROUND(AVG(recency_days), 1) AS avg_recency_days,
                ROUND(AVG(purchase_days), 1) AS avg_purchase_days,
                ROUND(AVG(total_lines), 1) AS avg_purchase_lines,
                ROUND(AVG(total_price_contrib), 4) AS avg_price_contribution
            FROM segmented
            GROUP BY segment
            ORDER BY customer_count DESC
        ) TO '{seg_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {seg_file.name} generated in {time.time()-t0:.2f}s")

    # 9. Monthly Cohort Matrix
    t0 = time.time()
    coh_file = out_dir / "agg_cohort_retention.parquet"
    conn.execute(f"""
        COPY (
            WITH customer_first_purchase AS (
                SELECT
                    customer_id,
                    DATE_TRUNC('month', MIN(t_dat)) AS cohort_month
                FROM transactions
                GROUP BY customer_id
            ),
            customer_monthly_activity AS (
                SELECT DISTINCT
                    t.customer_id,
                    cfp.cohort_month,
                    (YEAR(DATE_TRUNC('month', t.t_dat)) - YEAR(cfp.cohort_month)) * 12 +
                    (MONTH(DATE_TRUNC('month', t.t_dat)) - MONTH(cfp.cohort_month)) AS period_number
                FROM transactions t
                JOIN customer_first_purchase cfp ON t.customer_id = cfp.customer_id
            ),
            cohort_sizes AS (
                SELECT
                    cohort_month,
                    COUNT(DISTINCT customer_id) AS cohort_size
                FROM customer_first_purchase
                GROUP BY cohort_month
            )
            SELECT
                STRFTIME(cma.cohort_month, '%Y-%m') AS cohort_month,
                cs.cohort_size,
                cma.period_number,
                COUNT(DISTINCT cma.customer_id) AS active_customers,
                ROUND(COUNT(DISTINCT cma.customer_id) * 100.0 / cs.cohort_size, 2) AS repeat_activity_rate_pct
            FROM customer_monthly_activity cma
            JOIN cohort_sizes cs ON cma.cohort_month = cs.cohort_month
            WHERE cma.period_number <= 12
            GROUP BY cma.cohort_month, cs.cohort_size, cma.period_number
            ORDER BY cma.cohort_month, cma.period_number
        ) TO '{coh_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {coh_file.name} generated in {time.time()-t0:.2f}s")

    # 10. Channel Overview & Overlap
    t0 = time.time()
    ch_file = out_dir / "agg_channel_overview.parquet"
    conn.execute(f"""
        COPY (
            SELECT
                sales_channel_id,
                COUNT(*) AS purchase_volume,
                COUNT(DISTINCT customer_id) AS unique_customers,
                COUNT(DISTINCT article_id) AS active_articles,
                ROUND(AVG(price), 6) AS avg_normalised_price,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS volume_share_pct
            FROM transactions
            GROUP BY sales_channel_id
            ORDER BY sales_channel_id
        ) TO '{ch_file.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    print(f"[✓] {ch_file.name} generated in {time.time()-t0:.2f}s")

    conn.close()
    elapsed_total = time.time() - t_start
    print("=" * 65)
    print(f"ANALYTICAL PRECOMPUTATIONS COMPLETED IN {elapsed_total:.2f}s")
    print("=" * 65)


if __name__ == "__main__":
    run_precomputations()
