"""The guard around agent-written SQL: one SELECT, capped, timed, locked down."""

import threading
import time
from collections.abc import Iterator

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.duckdb import get_connection
from app.services import sql as sql_service
from app.services.sql import QueryBusy, QueryRejected, QueryTimeout, run_select


@pytest.fixture
def cur(client: TestClient) -> Iterator[duckdb.DuckDBPyConnection]:
    cursor = get_connection().cursor()
    yield cursor
    cursor.close()


def test_select_returns_columns_and_rows(cur: duckdb.DuckDBPyConnection) -> None:
    result = run_select(
        cur,
        "SELECT record_date, transaction_type FROM deposits_withdrawals "
        "ORDER BY record_date LIMIT 3",
    )
    assert result.row_count == 3
    assert len(result.rows) == 3
    assert [(c.name, c.type) for c in result.columns] == [
        ("record_date", "DATE"),
        ("transaction_type", "VARCHAR"),
    ]
    assert result.truncated is False


def test_row_cap_sets_truncated(cur: duckdb.DuckDBPyConnection) -> None:
    result = run_select(cur, "SELECT * FROM range(10)", max_rows=4)
    assert result.row_count == 4
    assert result.truncated is True


def test_exact_cap_not_truncated(cur: duckdb.DuckDBPyConnection) -> None:
    result = run_select(cur, "SELECT * FROM range(4)", max_rows=4)
    assert result.row_count == 4
    assert result.truncated is False


def test_default_rows_from_settings(cur: duckdb.DuckDBPyConnection) -> None:
    result = run_select(cur, "SELECT * FROM range(500)")
    assert result.row_count == 200
    assert result.truncated is True


@pytest.mark.parametrize("max_rows", [0, 2001])
def test_max_rows_bounds(cur: duckdb.DuckDBPyConnection, max_rows: int) -> None:
    with pytest.raises(QueryRejected, match="max_rows"):
        run_select(cur, "SELECT 1", max_rows=max_rows)


def test_rejects_multiple_statements(cur: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(QueryRejected, match="exactly one"):
        run_select(cur, "SELECT 1; SELECT 2")


@pytest.mark.parametrize("sql", ["", "-- note"])
def test_rejects_empty(cur: duckdb.DuckDBPyConnection, sql: str) -> None:
    with pytest.raises(QueryRejected, match="exactly one"):
        run_select(cur, sql)


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO metadata VALUES ('a', 'b', now())",
        "SET threads = 1",
        "CREATE TABLE x (i INT)",
        "EXPLAIN SELECT 1",
        "CALL pragma_version()",
        "ATTACH 'x.db'",
        "COPY metadata TO 'x.csv'",
    ],
)
def test_rejects_non_select(cur: duckdb.DuckDBPyConnection, sql: str) -> None:
    with pytest.raises(QueryRejected, match="Only SELECT"):
        run_select(cur, sql)


def test_rejects_pivot(cur: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(QueryRejected, match="GROUP BY"):
        run_select(cur, "PIVOT deposits_withdrawals ON transaction_type USING count(*)")


@pytest.mark.parametrize(
    "sql",
    ["DESCRIBE deposits_withdrawals", "SHOW TABLES", "FROM metadata", "VALUES (1)"],
)
def test_allows_select_shapes(cur: duckdb.DuckDBPyConnection, sql: str) -> None:
    assert run_select(cur, sql).row_count >= 1


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM read_csv('/etc/passwd')",
        "SELECT * FROM read_text('/proc/self/environ')",
        "SELECT * FROM 'https://example.com/x.csv'",
    ],
)
def test_file_access_blocked(cur: duckdb.DuckDBPyConnection, sql: str) -> None:
    with pytest.raises(QueryRejected, match="disabled|Permission"):
        run_select(cur, sql)


def test_configuration_locked(cur: duckdb.DuckDBPyConnection) -> None:
    result = run_select(cur, "SELECT current_setting('enable_external_access')")
    assert result.rows == [[False]]
    with pytest.raises(duckdb.InvalidInputException):
        cur.execute("SET enable_external_access = true")


def test_parse_error(cur: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(QueryRejected, match="Could not parse"):
        run_select(cur, "SELEC 1")


def test_timeout_interrupts(
    cur: duckdb.DuckDBPyConnection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "query_timeout_seconds", 0.2)
    start = time.perf_counter()
    with pytest.raises(QueryTimeout, match="0.2s"):
        run_select(cur, "SELECT count(*) FROM range(10000000000) a")
    assert time.perf_counter() - start < 5


def test_busy_when_no_slot(
    cur: duckdb.DuckDBPyConnection, monkeypatch: pytest.MonkeyPatch
) -> None:
    taken = threading.BoundedSemaphore(1)
    taken.acquire()
    monkeypatch.setattr(sql_service, "_slots", lambda: taken)
    with pytest.raises(QueryBusy):
        run_select(cur, "SELECT 1")


def test_api_still_works_after_lockdown(client: TestClient) -> None:
    assert client.get("/api/v1/meta/stats").status_code == 200
