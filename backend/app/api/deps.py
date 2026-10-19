"""Shared FastAPI dependencies."""

from collections.abc import Iterator
from typing import Annotated

import duckdb
from fastapi import Depends

from app.core.duckdb import get_connection


def get_cursor() -> Iterator[duckdb.DuckDBPyConnection]:
    cursor = get_connection().cursor()
    try:
        yield cursor
    finally:
        cursor.close()


CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_cursor)]
