"""
DuckDB Loader – load Parquet files into DuckDB and orchestrate the full pipeline.

Pipeline:  CSV (raw) → Parquet (processed) → DuckDB (analytical database)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb

from config.settings import (
    ARTICLES_CSV,
    ARTICLES_PARQUET,
    CUSTOMERS_CSV,
    CUSTOMERS_PARQUET,
    DUCKDB_PATH,
    PROCESSED_DIR,
    RAW_DIR,
    SQL_DIR,
    TRANSACTIONS_CSV,
    TRANSACTIONS_PARQUET,
)
from src.ingestion.parquet_converter import (
    convert_articles_to_parquet,
    convert_customers_to_parquet,
    convert_transactions_to_parquet,
)


# Module-level connection cache
_connection: Optional[duckdb.DuckDBPyConnection] = None


# ──────────────────────────────────────────────
# Database initialisation
# ──────────────────────────────────────────────
def init_database(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Create / connect to the DuckDB database and execute ``schema.sql``.

    Parameters
    ----------
    db_path : str | Path | None
        Database file path.  Defaults to ``config.settings.DUCKDB_PATH``.

    Returns
    -------
    duckdb.DuckDBPyConnection
    """
    db_path = Path(db_path) if db_path else DUCKDB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[db_loader] Connecting to DuckDB: {db_path}")
    conn = duckdb.connect(str(db_path))

    schema_file = SQL_DIR / "schema.sql"
    if schema_file.exists():
        print(f"[db_loader] Executing schema: {schema_file}")
        sql = schema_file.read_text(encoding="utf-8")
        conn.execute(sql)
        print("[db_loader] Schema applied successfully.")
    else:
        print(
            f"[db_loader] WARNING – schema file not found: {schema_file}. "
            "Tables must be created manually or by a later migration."
        )

    return conn


# ──────────────────────────────────────────────
# Load a single Parquet file into a DuckDB table
# ──────────────────────────────────────────────
def load_parquet_to_duckdb(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    parquet_path: str | Path,
) -> int:
    """Load a Parquet file into a DuckDB table.

    Uses ``INSERT INTO … SELECT * FROM read_parquet(…)`` so that the
    table schema (from schema.sql) governs column types.

    Parameters
    ----------
    conn : duckdb.DuckDBPyConnection
    table_name : str
        Target table (must already exist).
    parquet_path : str | Path
        Path to the ``.parquet`` file.

    Returns
    -------
    int
        Number of rows loaded.
    """
    parquet_path = Path(parquet_path)
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    print(f"[db_loader] Loading {parquet_path.name} → {table_name}")

    # Escape the path for SQL (forward-slashes work on all platforms in DuckDB)
    safe_path = str(parquet_path).replace("\\", "/")

    conn.execute(
        f"INSERT INTO {table_name} BY NAME SELECT * FROM read_parquet('{safe_path}')"
    )

    row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"[db_loader] ✓ {table_name}: {row_count:,} rows loaded")
    return row_count


# ──────────────────────────────────────────────
# Full ingestion orchestrator
# ──────────────────────────────────────────────
def run_full_ingestion(
    db_path: str | Path | None = None,
    raw_dir: str | Path | None = None,
    processed_dir: str | Path | None = None,
) -> duckdb.DuckDBPyConnection:
    """Orchestrate the complete CSV → Parquet → DuckDB pipeline.

    1. Convert each CSV to Parquet (skip if Parquet already exists).
    2. Initialise / connect to DuckDB (applies schema.sql).
    3. Load each Parquet file into its DuckDB table.

    Parameters
    ----------
    db_path : str | Path | None
        DuckDB file.  Defaults to ``config.settings.DUCKDB_PATH``.
    raw_dir : str | Path | None
        Directory containing raw CSVs.  Defaults to ``config.settings.RAW_DIR``.
    processed_dir : str | Path | None
        Directory for Parquet outputs.  Defaults to ``config.settings.PROCESSED_DIR``.

    Returns
    -------
    duckdb.DuckDBPyConnection
        Open connection to the loaded database.
    """
    db_path = Path(db_path) if db_path else DUCKDB_PATH
    raw_dir = Path(raw_dir) if raw_dir else RAW_DIR
    processed_dir = Path(processed_dir) if processed_dir else PROCESSED_DIR

    # Resolve file paths (use settings defaults if raw_dir matches)
    if raw_dir == RAW_DIR:
        txn_csv, art_csv, cust_csv = TRANSACTIONS_CSV, ARTICLES_CSV, CUSTOMERS_CSV
    else:
        txn_csv = raw_dir / "transactions_train.csv"
        art_csv = raw_dir / "articles.csv"
        cust_csv = raw_dir / "customers.csv"

    if processed_dir == PROCESSED_DIR:
        txn_pq, art_pq, cust_pq = (
            TRANSACTIONS_PARQUET,
            ARTICLES_PARQUET,
            CUSTOMERS_PARQUET,
        )
    else:
        txn_pq = processed_dir / "transactions.parquet"
        art_pq = processed_dir / "articles.parquet"
        cust_pq = processed_dir / "customers.parquet"

    # ── Step 1: CSV → Parquet ──────────────────
    print("\n" + "=" * 60)
    print("STEP 1 / 2 — CSV → Parquet conversion")
    print("=" * 60)

    _convert_if_needed(txn_csv, txn_pq, "transactions", convert_transactions_to_parquet)
    _convert_if_needed(art_csv, art_pq, "articles", convert_articles_to_parquet)
    _convert_if_needed(cust_csv, cust_pq, "customers", convert_customers_to_parquet)

    # ── Step 2: Parquet → DuckDB ───────────────
    print("\n" + "=" * 60)
    print("STEP 2 / 2 — Parquet → DuckDB ingestion")
    print("=" * 60)

    conn = init_database(db_path)

    load_parquet_to_duckdb(conn, "transactions", txn_pq)
    load_parquet_to_duckdb(conn, "articles", art_pq)
    load_parquet_to_duckdb(conn, "customers", cust_pq)

    print("\n[db_loader] ✓ Full ingestion complete.")
    return conn


# ──────────────────────────────────────────────
# Reusable connection accessor
# ──────────────────────────────────────────────
def get_connection(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Return a reusable DuckDB connection (cached at module level).

    Parameters
    ----------
    db_path : str | Path | None
        Database file.  Defaults to ``config.settings.DUCKDB_PATH``.

    Returns
    -------
    duckdb.DuckDBPyConnection
    """
    global _connection
    if _connection is None:
        db_path = Path(db_path) if db_path else DUCKDB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[db_loader] Opening reusable connection: {db_path}")
        _connection = duckdb.connect(str(db_path))
    return _connection


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────
def _convert_if_needed(csv_path: Path, parquet_path: Path, label: str, converter) -> None:
    """Run *converter* only when the Parquet file does not already exist."""
    if parquet_path.exists():
        size_mb = parquet_path.stat().st_size / (1024 * 1024)
        print(f"[db_loader] Skipping {label} conversion – Parquet already exists ({size_mb:,.1f} MB)")
        return

    if not csv_path.exists():
        print(f"[db_loader] WARNING – CSV not found, cannot convert {label}: {csv_path}")
        return

    converter(csv_path, parquet_path)
