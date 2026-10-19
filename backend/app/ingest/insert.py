"""Insert a DataFrame into an artifact table with the reference's alignment rules."""

from datetime import UTC, datetime

import duckdb
import pandas as pd

from app.constants.endpoints import ALL_TABLES


def utc_now_naive() -> datetime:
    """Current UTC time without tzinfo.

    The schema's columns are plain ``TIMESTAMP``; DuckDB would cast an aware value
    through the session's local time zone, so the stored value would depend on
    the machine that ran ingestion.
    """
    return datetime.now(UTC).replace(tzinfo=None)


def insert_frame(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame, table: str) -> int:
    """Insert ``df`` into ``table`` and return the number of rows inserted.

    Columns are aligned to the table: ``id`` is dropped (the sequence fills it),
    columns the table lacks are dropped, columns the frame lacks become NULL.

    Raises:
        ValueError: If ``table`` is not an artifact table (it is interpolated
            into SQL).
    """
    if table not in ALL_TABLES:
        raise ValueError(f"Not an artifact table: {table!r}")
    if df.empty:
        return 0

    frame = df.copy()
    if "record_date" in frame.columns:
        frame["record_date"] = pd.to_datetime(frame["record_date"])
    now = utc_now_naive()
    for col in ("created_at", "updated_at"):
        if col not in frame.columns:
            frame[col] = now

    columns = [
        row[0] for row in conn.execute(f"DESCRIBE {table}").fetchall() if row[0] != "id"
    ]
    for col in columns:
        if col not in frame.columns:
            frame[col] = None
    frame = frame[columns]

    column_list = ", ".join(columns)
    conn.register("_insert_frame", frame)
    try:
        conn.execute(
            f"INSERT INTO {table} ({column_list}) "
            f"SELECT {column_list} FROM _insert_frame"
        )
    finally:
        conn.unregister("_insert_frame")
    return len(frame)
