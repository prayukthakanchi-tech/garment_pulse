"""
Unit tests for data ingestion, string identifier preservation, and schema initialization.
"""

from pathlib import Path
import duckdb
import pytest


def test_customer_and_article_ids_stay_string(test_db):
    """Verify customer_id and article_id are never cast to float/int."""
    schema_info = test_db.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'transactions' AND column_name IN ('customer_id', 'article_id')
    """).fetchall()

    dtypes = {row[0]: row[1] for row in schema_info}
    assert "VARCHAR" in dtypes["customer_id"].upper(), f"Expected VARCHAR, got {dtypes['customer_id']}"
    assert "VARCHAR" in dtypes["article_id"].upper(), f"Expected VARCHAR, got {dtypes['article_id']}"


def test_leading_zero_preserved_in_article_id(test_db):
    """Verify article IDs retain their leading zeros (e.g. 0108775015)."""
    arts = test_db.execute("SELECT article_id FROM articles WHERE article_id LIKE '0%'").fetchall()
    assert len(arts) > 0, "Leading zero article IDs were truncated."
    for a in arts:
        assert a[0].startswith("0"), f"Article ID {a[0]} lost leading zero"
        assert len(a[0]) == 10, f"Article ID {a[0]} length != 10"


def test_transaction_row_counts(test_db):
    """Verify mock transactions loaded correctly."""
    cnt = test_db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    assert cnt == 20, f"Expected 20 transactions, got {cnt}"
