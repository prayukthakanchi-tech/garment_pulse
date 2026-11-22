"""
GarmentPulse — Safe Database Connection & Concurrency Manager
Provides isolated, thread-local DuckDB connections and managed query execution.
Prevents ResourceInUseException and database locking during multi-threaded Streamlit reruns.
"""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Any, List, Optional, Tuple, Union
import duckdb
import pandas as pd

from config.settings import DUCKDB_PATH

# Thread-local storage to guarantee isolated connection per worker thread
_thread_local = threading.local()


def get_db_connection(db_path: Optional[Union[str, Path]] = None) -> duckdb.DuckDBPyConnection:
    """Returns a thread-local read-only DuckDB connection.
    
    Each thread gets its own independent connection handle, ensuring
    concurrent queries from multiple users or Streamlit reruns never collide.
    """
    path = Path(db_path) if db_path else DUCKDB_PATH
    if not path.exists():
        cloud_fallback = Path("data/garmentpulse_cloud.duckdb")
        if cloud_fallback.exists():
            path = cloud_fallback
        else:
            raise FileNotFoundError(f"Database file not found at: {path}")

    # Check if this thread already has an active connection
    conn = getattr(_thread_local, "conn", None)
    if conn is None:
        _thread_local.conn = duckdb.connect(str(path), read_only=True)
        conn = _thread_local.conn
    return conn


def get_cursor(db_path: Optional[Union[str, Path]] = None) -> duckdb.DuckDBPyConnection:
    """Returns an isolated cursor from the current thread's connection."""
    conn = get_db_connection(db_path)
    return conn.cursor()


def execute_query(
    sql: str,
    params: Optional[Union[List[Any], Tuple[Any, ...]]] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Execute SQL query safely and fetch complete DataFrame before closing cursor.
    
    Guarantees no dangling cursor handles or unfinished execution locks.
    """
    cur = get_cursor(db_path)
    try:
        if params is not None:
            df = cur.execute(sql, params).fetchdf()
        else:
            df = cur.execute(sql).fetchdf()
        return df
    finally:
        try:
            cur.close()
        except Exception:
            pass


def execute_scalar(
    sql: str,
    params: Optional[Union[List[Any], Tuple[Any, ...]]] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> Any:
    """Execute SQL query and fetch single scalar value safely."""
    cur = get_cursor(db_path)
    try:
        if params is not None:
            res = cur.execute(sql, params).fetchone()
        else:
            res = cur.execute(sql).fetchone()
        return res[0] if res is not None else None
    finally:
        try:
            cur.close()
        except Exception:
            pass
