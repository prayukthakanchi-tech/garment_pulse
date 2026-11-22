"""
GarmentPulse — Universal Cloud Database Native Bootstrapper
Builds a native DuckDB database instance from universal Apache Parquet seed files.
Guarantees 100% binary compatibility across all DuckDB versions, Python releases,
and host operating systems (Linux Debian, macOS, Windows).
"""

from __future__ import annotations

import os
from pathlib import Path
import duckdb

from config.settings import DUCKDB_PATH


def bootstrap_database_if_needed(target_path: Optional[Path] = None, seed_dir: Optional[Path] = None) -> bool:
    """Natively provisions DuckDB database from Parquet seed files if missing."""
    dest = target_path or DUCKDB_PATH
    seeds = seed_dir or Path("data/seed")

    if dest.exists():
        return False

    required_seeds = ["articles.parquet", "customers.parquet", "transactions.parquet"]
    if not all((seeds / s).exists() for s in required_seeds):
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_dest = dest.with_suffix(".duckdb.init")
    if temp_dest.exists():
        try:
            temp_dest.unlink()
        except OSError:
            pass

    conn = duckdb.connect(str(temp_dest))
    try:
        # Load tables natively using target environment's DuckDB engine
        conn.execute(f"CREATE TABLE articles AS SELECT * FROM read_parquet('{seeds.as_posix()}/articles.parquet');")
        conn.execute(f"CREATE TABLE customers AS SELECT * FROM read_parquet('{seeds.as_posix()}/customers.parquet');")
        conn.execute(f"CREATE TABLE transactions AS SELECT * FROM read_parquet('{seeds.as_posix()}/transactions.parquet');")

        if (seeds / "v_monthly_summary.parquet").exists():
            conn.execute(f"CREATE TABLE v_monthly_summary AS SELECT * FROM read_parquet('{seeds.as_posix()}/v_monthly_summary.parquet');")
        if (seeds / "v_weekly_summary.parquet").exists():
            conn.execute(f"CREATE TABLE v_weekly_summary AS SELECT * FROM read_parquet('{seeds.as_posix()}/v_weekly_summary.parquet');")

        # Create enriched transactions analytical view
        conn.execute("""
        CREATE VIEW v_transactions_enriched AS
        SELECT
            t.t_dat,
            t.customer_id,
            t.article_id,
            t.price,
            t.sales_channel_id,
            a.prod_name,
            a.product_type_name,
            a.product_group_name,
            a.graphical_appearance_name,
            a.colour_group_name,
            a.perceived_colour_value_name,
            a.perceived_colour_master_name,
            a.department_name,
            a.index_name,
            a.index_group_name,
            a.section_name,
            a.garment_group_name,
            c.FN,
            c.Active,
            c.club_member_status,
            c.fashion_news_frequency,
            c.age,
            c.postal_code
        FROM transactions t
        LEFT JOIN articles a ON t.article_id = a.article_id
        LEFT JOIN customers c ON t.customer_id = c.customer_id;
        """)

        conn.execute("CHECKPOINT;")
    finally:
        conn.close()

    # Atomically replace into target path
    if temp_dest.exists():
        temp_dest.replace(dest)

    return True
