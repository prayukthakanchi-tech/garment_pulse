"""
Tests for database connection manager and data caching service.
"""

import duckdb
import pytest
from src.database.connection import get_db_connection, get_cursor, execute_query, execute_scalar


def test_connection_isolated_cursors(test_db):
    """Verify that multiple cursors can run concurrently without ResourceInUseException."""
    c1 = test_db.cursor()
    c2 = test_db.cursor()

    df1 = c1.execute("SELECT count(*) as cnt FROM transactions").fetchdf()
    df2 = c2.execute("SELECT count(*) as cnt FROM articles").fetchdf()

    assert df1.iloc[0, 0] > 0
    assert df2.iloc[0, 0] > 0

    c1.close()
    c2.close()


def test_execute_query_helper(test_db, monkeypatch):
    """Verify execute_query executes and returns pandas DataFrame cleanly."""
    monkeypatch.setattr("src.database.connection.get_cursor", lambda *args, **kwargs: test_db.cursor())
    
    df = execute_query("SELECT article_id, price FROM transactions LIMIT 5")
    assert len(df) == 5
    assert "article_id" in df.columns
    assert "price" in df.columns


def test_execute_scalar_helper(test_db, monkeypatch):
    """Verify execute_scalar returns scalar directly."""
    monkeypatch.setattr("src.database.connection.get_cursor", lambda *args, **kwargs: test_db.cursor())
    
    total = execute_scalar("SELECT count(*) FROM articles")
    assert total > 0
