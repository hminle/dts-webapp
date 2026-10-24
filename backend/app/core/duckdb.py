"""The serving app's only DuckDB connection: read-only, opened once per process.

Every request takes its own ``cursor()`` (see ``app.api.deps``); cursors share
the database but have independent state, so concurrent requests are safe. No
other module in the serving app may call ``duckdb.connect``. The connection is
locked down (no file or network access, no configuration changes) because
``app.services.sql`` runs agent-written SQL on it.
"""

from functools import lru_cache

import duckdb

from app.core.config import get_settings


class DataUnavailable(RuntimeError):
    """The artifact is missing or unreadable."""


@lru_cache(maxsize=1)
def get_connection() -> duckdb.DuckDBPyConnection:
    settings = get_settings()
    path = settings.duckdb_path
    if not path.exists():
        raise DataUnavailable(f"No data artifact at {path}")
    # The function filesystem is read-only except /tmp; DuckDB may spill there.
    conn = duckdb.connect(
        str(path),
        read_only=True,
        config={
            "temp_directory": "/tmp/duckdb",
            "memory_limit": settings.duckdb_memory_limit,
        },
    )
    # Agent SQL (app.services.sql) runs on this connection, and DuckDB refuses a
    # second connection to the same file with another config. The API itself never
    # reads files or the network, so close both, then lock the settings so a query
    # can't SET them back. Passing these in `config` instead rejects temp_directory.
    conn.execute("SET enable_external_access = false")
    conn.execute("SET lock_configuration = true")
    return conn


def reset_connection_for_tests() -> None:
    """Close the cached connection so the next call reopens ``duckdb_path``."""
    if get_connection.cache_info().currsize:
        get_connection().close()
    get_connection.cache_clear()
