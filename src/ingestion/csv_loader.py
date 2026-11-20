"""
CSV Loader – read raw H&M CSVs with Polars.

All identifiers (customer_id, article_id) are kept as strings throughout
to prevent silent float conversion of leading-zero hex IDs.
"""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl


# ──────────────────────────────────────────────
# Transactions  (lazy – may be ~31 M rows)
# ──────────────────────────────────────────────
def load_transactions_csv(
    path: str | Path,
    batch_size: int = 500_000,
) -> pl.LazyFrame:
    """Lazily scan the transactions CSV.

    Parameters
    ----------
    path : str | Path
        Path to ``transactions_train.csv``.
    batch_size : int, optional
        Hint for downstream streaming operations (default 500 000).

    Returns
    -------
    pl.LazyFrame
        Lazy frame with columns:
        t_dat (Utf8), customer_id (Utf8), article_id (Utf8),
        price (Float64), sales_channel_id (Int32).
    """
    path = Path(path)
    _log_file_info(path)

    dtypes = {
        "t_dat": pl.Utf8,
        "customer_id": pl.Utf8,
        "article_id": pl.Utf8,
        "price": pl.Float64,
        "sales_channel_id": pl.Int32,
    }

    try:
        lf = pl.scan_csv(
            path,
            schema_overrides=dtypes,
            encoding="utf8-lossy",
            n_rows=None,
        )
    except Exception as exc:
        print(f"[csv_loader] ERROR scanning {path.name}: {exc}")
        raise

    # Log estimated row count (schema-only fetch – no full scan)
    try:
        schema = lf.collect_schema()
        print(f"[csv_loader] Transactions schema: {schema}")
    except Exception:
        pass

    return lf


# ──────────────────────────────────────────────
# Articles  (eager – typically ~105 k rows)
# ──────────────────────────────────────────────
def load_articles_csv(path: str | Path) -> pl.DataFrame:
    """Eagerly read the articles CSV.

    Parameters
    ----------
    path : str | Path
        Path to ``articles.csv``.

    Returns
    -------
    pl.DataFrame
    """
    path = Path(path)
    _log_file_info(path)

    try:
        df = pl.read_csv(
            path,
            schema_overrides={
                "article_id": pl.Utf8,
                "product_code": pl.Utf8,
                "prod_name": pl.Utf8,
                "product_type_no": pl.Int64,
                "product_type_name": pl.Utf8,
                "product_group_name": pl.Utf8,
                "graphical_appearance_no": pl.Int64,
                "graphical_appearance_name": pl.Utf8,
                "colour_group_code": pl.Int64,
                "colour_group_name": pl.Utf8,
                "perceived_colour_value_id": pl.Int64,
                "perceived_colour_value_name": pl.Utf8,
                "perceived_colour_master_id": pl.Int64,
                "perceived_colour_master_name": pl.Utf8,
                "department_no": pl.Int64,
                "department_name": pl.Utf8,
                "index_code": pl.Utf8,
                "index_name": pl.Utf8,
                "index_group_no": pl.Int64,
                "index_group_name": pl.Utf8,
                "section_no": pl.Int64,
                "section_name": pl.Utf8,
                "garment_group_no": pl.Int64,
                "garment_group_name": pl.Utf8,
                "detail_desc": pl.Utf8,
            },
            encoding="utf8-lossy",
            infer_schema_length=10_000,
        )
    except Exception as exc:
        print(f"[csv_loader] ERROR reading {path.name}: {exc}")
        raise

    print(f"[csv_loader] Articles loaded: {df.shape[0]:,} rows × {df.shape[1]} cols")
    return df


# ──────────────────────────────────────────────
# Customers  (eager – typically ~1.37 M rows)
# ──────────────────────────────────────────────
def load_customers_csv(path: str | Path) -> pl.DataFrame:
    """Eagerly read the customers CSV.

    ``age`` is loaded as Float64 because it contains nulls.

    Parameters
    ----------
    path : str | Path
        Path to ``customers.csv``.

    Returns
    -------
    pl.DataFrame
    """
    path = Path(path)
    _log_file_info(path)

    try:
        df = pl.read_csv(
            path,
            schema_overrides={
                "customer_id": pl.Utf8,
                "FN": pl.Float64,
                "Active": pl.Float64,
                "club_member_status": pl.Utf8,
                "fashion_news_frequency": pl.Utf8,
                "age": pl.Float64,
                "postal_code": pl.Utf8,
            },
            encoding="utf8-lossy",
            infer_schema_length=10_000,
        )
    except Exception as exc:
        print(f"[csv_loader] ERROR reading {path.name}: {exc}")
        raise

    print(f"[csv_loader] Customers loaded: {df.shape[0]:,} rows × {df.shape[1]} cols")
    return df


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def _log_file_info(path: Path) -> None:
    """Print the file name and human-readable size."""
    if path.exists():
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"[csv_loader] File: {path.name}  ({size_mb:,.1f} MB)")
    else:
        print(f"[csv_loader] WARNING – file not found: {path}")
