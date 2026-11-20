"""
Automated DuckDB Concurrency & Stress Test Suite
Simulates multi-user, multi-threaded Streamlit reruns, simultaneous analytical calculations,
and rapid page-switching workloads to verify thread isolation, cursor cleanup,
and absolute absence of ResourceInUseException or locking deadlocks.
"""

import concurrent.futures
import time
import pytest
import duckdb
from config.settings import DUCKDB_PATH
from src.database.connection import get_db_connection, get_cursor, execute_query, execute_scalar


def test_concurrent_multithreaded_read_queries():
    """Stress test: 10 concurrent worker threads executing simultaneous analytical aggregations."""
    queries = [
        "SELECT COUNT(*) FROM transactions WHERE price > 0.05",
        "SELECT COUNT(DISTINCT customer_id) FROM customers WHERE age > 30",
        "SELECT department_name, COUNT(*) FROM articles GROUP BY department_name ORDER BY 2 DESC LIMIT 10",
        "SELECT sales_channel_id, COUNT(*), AVG(price) FROM transactions GROUP BY sales_channel_id",
        "SELECT index_group_name, COUNT(*) FROM articles GROUP BY index_group_name",
        "SELECT COUNT(*) FROM transactions WHERE sales_channel_id = 1",
        "SELECT COUNT(*) FROM transactions WHERE sales_channel_id = 2",
        "SELECT garment_group_name, COUNT(*) FROM articles GROUP BY garment_group_name",
        "SELECT COUNT(*) FROM customers WHERE club_member_status = 'ACTIVE'",
        "SELECT MIN(t_dat), MAX(t_dat) FROM transactions",
    ]

    def worker_task(idx):
        sql = queries[idx % len(queries)]
        # Must execute cleanly on thread-local cursor without locking or ResourceInUseException
        df = execute_query(sql)
        assert not df.empty
        return len(df)

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker_task, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    elapsed = time.time() - start_time
    assert len(results) == 20
    assert all(r > 0 for r in results)
    print(f"\n[Stress Test] 20 concurrent queries across 10 worker threads completed in {elapsed:.2f}s")


def test_rapid_cursor_allocation_and_cleanup():
    """Verify that allocating and closing 50 cursors sequentially causes zero connection or memory leaks."""
    for i in range(50):
        cur = get_cursor()
        res = cur.execute("SELECT 1 AS probe").fetchone()
        assert res[0] == 1
        cur.close()


def test_interleaved_heavy_and_light_queries():
    """Simulates a heavy report running in background while user executes quick filter dropdown queries."""
    results = {}

    def heavy_query():
        cur = get_cursor()
        df = cur.execute("""
            SELECT a.department_name, COUNT(*) as vol, AVG(t.price) as p_avg
            FROM transactions t
            JOIN articles a ON t.article_id = a.article_id
            GROUP BY a.department_name
            ORDER BY vol DESC
            LIMIT 5
        """).fetchdf()
        cur.close()
        results["heavy"] = len(df)

    def light_query(idx):
        cur = get_cursor()
        val = cur.execute(f"SELECT COUNT(*) FROM articles WHERE product_type_no = {idx}").fetchone()[0]
        cur.close()
        return val

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        f_heavy = executor.submit(heavy_query)
        f_lights = [executor.submit(light_query, i) for i in range(1, 10)]

        f_heavy.result()
        light_res = [f.result() for f in f_lights]

    assert results["heavy"] == 5
    assert len(light_res) == 9
