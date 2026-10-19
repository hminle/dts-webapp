"""The serving app's only DuckDB connection: read-only, opened once per process.

Every request takes its own ``cursor()`` (see ``app.api.deps``); cursors share
the database but have independent state, so concurrent requests are safe. No
other module in the serving app may call ``duckdb.connect``.
"""

from functools import lru_cache

import duckdb

from app.core.config import get_settings


class DataUnavailable(RuntimeError):
    """The artifact is missing or unreadable."""


@lru_cache(maxsize=1)
def get_connection() -> duckdb.DuckDBPyConnection:
    path = get_settings().duckdb_path
    if not path.exists():
        raise DataUnavailable(f"No data artifact at {path}")
    # The function filesystem is read-only except /tmp; DuckDB may spill there.
    return duckdb.connect(
        str(path), read_only=True, config={"temp_directory": "/tmp/duckdb"}
    )


def reset_connection_for_tests() -> None:
    """Close the cached connection so the next call reopens ``duckdb_path``."""
    if get_connection.cache_info().currsize:
        get_connection().close()
    get_connection.cache_clear()
