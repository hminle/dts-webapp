"""Run one agent-written ``SELECT`` with row, time and concurrency limits.

What the SQL can reach is limited by the connection itself (``app.core.duckdb``
disables file and network access and locks the configuration). This module
limits what it can do: one ``SELECT``, a capped row count, a timeout, and a
fixed number of queries at once so agents can't starve the API.
"""

import functools
import threading
import time

import duckdb

from app.core.config import get_settings
from app.schemas.sql import ColumnInfo, QueryResult

# What one PIVOT statement parses into.
_PIVOT_TYPES = [duckdb.StatementType.CREATE, duckdb.StatementType.SELECT]


class QueryRejected(ValueError):
    """The SQL is not exactly one SELECT statement, or failed to parse or run."""


class QueryTimeout(QueryRejected):
    """The query ran longer than ``query_timeout_seconds`` and was interrupted."""


class QueryBusy(QueryRejected):
    """All query slots are in use."""


@functools.cache
def _slots() -> threading.BoundedSemaphore:
    # Built on first use, so tests can change query_concurrency beforehand.
    return threading.BoundedSemaphore(get_settings().query_concurrency)


def run_select(
    cur: duckdb.DuckDBPyConnection, sql: str, max_rows: int | None = None
) -> QueryResult:
    """Run exactly one ``SELECT`` and return at most ``max_rows`` rows.

    Args:
        cur: A cursor on the locked-down connection from ``app.core.duckdb``.
        sql: One SELECT-shaped statement (``DESCRIBE``, ``SHOW``, ``FROM`` and
            ``VALUES`` parse as SELECT too).
        max_rows: Row cap; defaults to ``query_default_rows`` and may not exceed
            ``query_max_rows``.

    Returns:
        The rows, their column names and types, and whether rows were cut off.

    Raises:
        QueryBusy: Every query slot is taken.
        QueryTimeout: The query ran past ``query_timeout_seconds``.
        QueryRejected: The SQL is not one SELECT, failed to parse, or DuckDB
            raised while running it.
    """
    settings = get_settings()
    max_rows = settings.query_default_rows if max_rows is None else max_rows
    if not 1 <= max_rows <= settings.query_max_rows:
        raise QueryRejected(f"max_rows must be between 1 and {settings.query_max_rows}")

    try:
        statements = duckdb.extract_statements(sql)
    except duckdb.Error as exc:
        raise QueryRejected(f"Could not parse SQL: {exc}") from exc
    # Checked before the count, which would otherwise report "got 2".
    if [s.type for s in statements] == _PIVOT_TYPES:
        raise QueryRejected("PIVOT is not supported; use GROUP BY with FILTER or CASE.")
    if len(statements) != 1:
        raise QueryRejected(f"Send exactly one SQL statement; got {len(statements)}.")
    statement = statements[0]
    if statement.type != duckdb.StatementType.SELECT:
        raise QueryRejected(
            f"Only SELECT queries are allowed; got {statement.type.name}."
        )

    slots = _slots()
    if not slots.acquire(blocking=False):
        raise QueryBusy("Another query is running; retry in a few seconds.")
    # One extra row tells a result of exactly max_rows from a cut-off one.
    wrapped = f"SELECT * FROM (\n{statement.query}\n) AS q LIMIT {max_rows + 1}"
    timer = threading.Timer(settings.query_timeout_seconds, cur.interrupt)
    try:
        start = time.perf_counter()
        timer.start()
        cur.execute(wrapped)
        raw = cur.fetchall()
        elapsed_ms = round((time.perf_counter() - start) * 1000)
    # InterruptException subclasses duckdb.Error, so it must be caught first.
    except duckdb.InterruptException as exc:
        raise QueryTimeout(
            f"Query exceeded {settings.query_timeout_seconds:g}s and was stopped. "
            "Aggregate in SQL or filter by fiscal year."
        ) from exc
    except duckdb.Error as exc:
        raise QueryRejected(str(exc)) from exc
    finally:
        timer.cancel()
        slots.release()

    columns = [ColumnInfo(name=d[0], type=str(d[1])) for d in cur.description]
    rows = [list(r) for r in raw[:max_rows]]
    return QueryResult(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=len(raw) > max_rows,
        elapsed_ms=elapsed_ms,
    )
