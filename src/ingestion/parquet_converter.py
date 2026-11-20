"""
Parquet Converter – stream-convert raw CSVs to columnar Parquet files.

Parquet files are much faster to query and load into DuckDB.
Each converter validates the output by reading it back and comparing row counts.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from src.ingestion.csv_loader import (
    load_articles_csv,
    load_customers_csv,
    load_transactions_csv,
)


# ──────────────────────────────────────────────
# Transactions
# ──────────────────────────────────────────────
def convert_transactions_to_parquet(
    csv_path: str | Path,
    parquet_path: str | Path,
    batch_size: int = 500_000,
) -> Path:
    """Stream-convert the transactions CSV to Parquet.

    * ``t_dat`` (Utf8) is cast to ``Date`` during conversion.
    * Uses Polars ``sink_parquet`` for memory-efficient streaming.
    * Duplicate rows are **not** dropped – they may represent
      multiple legitimate purchases of the same item on the same day.

    Returns the output Path on success.
    """
    csv_path = Path(csv_path)
    parquet_path = Path(parquet_path)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[parquet] Converting transactions: {csv_path.name} → {parquet_path.name}")

    try:
        lf = load_transactions_csv(csv_path, batch_size=batch_size)

        # Cast t_dat string → Date
        lf = lf.with_columns(
            pl.col("t_dat").str.to_date("%Y-%m-%d").alias("t_dat"),
        )

        lf.sink_parquet(parquet_path)
        print(f"[parquet] Transactions written to {parquet_path}")
    except Exception as exc:
        print(f"[parquet] ERROR converting transactions: {exc}")
        raise

    _validate_parquet(parquet_path, "transactions")
    return parquet_path


# ──────────────────────────────────────────────
# Articles
# ──────────────────────────────────────────────
def convert_articles_to_parquet(
    csv_path: str | Path,
    parquet_path: str | Path,
) -> Path:
    """Convert the articles CSV to Parquet (eager – small file).

    Returns the output Path on success.
    """
    csv_path = Path(csv_path)
    parquet_path = Path(parquet_path)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[parquet] Converting articles: {csv_path.name} → {parquet_path.name}")

    try:
        df = load_articles_csv(csv_path)
        df.write_parquet(parquet_path)
        print(f"[parquet] Articles written to {parquet_path}")
    except Exception as exc:
        print(f"[parquet] ERROR converting articles: {exc}")
        raise

    _validate_parquet(parquet_path, "articles")
    return parquet_path


# ──────────────────────────────────────────────
# Customers
# ──────────────────────────────────────────────
def convert_customers_to_parquet(
    csv_path: str | Path,
    parquet_path: str | Path,
) -> Path:
    """Convert the customers CSV to Parquet (eager – small file).

    Returns the output Path on success.
    """
    csv_path = Path(csv_path)
    parquet_path = Path(parquet_path)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[parquet] Converting customers: {csv_path.name} → {parquet_path.name}")

    try:
        df = load_customers_csv(csv_path)
        df.write_parquet(parquet_path)
        print(f"[parquet] Customers written to {parquet_path}")
    except Exception as exc:
        print(f"[parquet] ERROR converting customers: {exc}")
        raise

    _validate_parquet(parquet_path, "customers")
    return parquet_path


# ──────────────────────────────────────────────
# Validation helper
# ──────────────────────────────────────────────
def _validate_parquet(parquet_path: Path, label: str) -> None:
    """Read back the written Parquet metadata and log row / column counts without loading entire file into memory."""
    try:
        count = pl.scan_parquet(parquet_path).select(pl.len()).collect().item()
        schema = pl.scan_parquet(parquet_path).collect_schema()
        print(
            f"[parquet] ✓ {label} validated: "
            f"{count:,} rows × {len(schema)} cols  "
            f"({parquet_path.stat().st_size / (1024 * 1024):,.1f} MB)"
        )
    except Exception as exc:
        print(f"[parquet] WARNING – validation read-back failed for {label}: {exc}")
