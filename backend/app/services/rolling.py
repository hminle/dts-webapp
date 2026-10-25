"""Rolling averages of daily amounts, counted in statements."""

from __future__ import annotations

from datetime import date, timedelta

import duckdb
from fastapi import HTTPException

from app.constants.categories import CATEGORY_REGISTRY
from app.schemas.treasury import (
    RollingAverageRequest,
    RollingAverageResponse,
    RollingMetric,
    RollingPoint,
)

# About 20 business days a month: the newsletter's monthly projection.
MONTHLY_MULTIPLIER = 20

_UNEMPLOYMENT = CATEGORY_REGISTRY["Unemployment Benefits"]


def _series(metric: RollingMetric) -> tuple[str, list[str]]:
    """One metric's daily series as ``(subquery, params)``."""
    if metric == "total_withdrawals":
        return (
            "SELECT record_date, total_withdrawals_today AS value "
            "FROM daily_net_transfers",
            [],
        )
    placeholders = ", ".join("?" for _ in _UNEMPLOYMENT.components)
    return (
        "SELECT record_date, SUM(transaction_today_amt) AS value "
        "FROM deposits_withdrawals WHERE transaction_type = 'Withdrawals' "
        f"AND transaction_catg IN ({placeholders}) GROUP BY record_date",
        list(_UNEMPLOYMENT.components),
    )


def _rolling_rows(
    cur: duckdb.DuckDBPyConnection,
    metric: RollingMetric,
    window: int,
    start: date,
    end: date,
) -> list[tuple]:
    """``(record_date, value, rolling_average)`` for each statement in the range."""
    subquery, params = _series(metric)
    # A frame clause takes no parameter, so the window size is interpolated.
    # It is safe: callers pass an int validated to 2–60 by RollingAverageRequest.
    window = int(window)
    query = f"""
    WITH series AS ({subquery}),
    w AS (
      SELECT record_date, value,
             AVG(value) OVER win AS avg_w,
             COUNT(*) OVER win AS n_w
      FROM series
      WHERE record_date <= ?
      WINDOW win AS (
        ORDER BY record_date ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW
      )
    )
    SELECT record_date, value, CASE WHEN n_w = {window} THEN avg_w END
    FROM w
    WHERE record_date >= ?
    ORDER BY record_date
    """
    return cur.execute(query, [*params, end, start]).fetchall()


def rolling_on(
    cur: duckdb.DuckDBPyConnection, metric: RollingMetric, window: int, day: str
) -> float | None:
    """The rolling average on ``day``; ``None`` without a full window that day."""
    on = date.fromisoformat(day)
    rows = _rolling_rows(cur, metric, window, on, on)
    if not rows or rows[0][2] is None:
        return None
    return float(rows[0][2])


def get_daily(
    cur: duckdb.DuckDBPyConnection, request: RollingAverageRequest
) -> RollingAverageResponse:
    """Each statement's amount with the mean of the last ``window`` statements.

    Raises:
        ValueError: ``start_date`` is after ``end_date`` (HTTP 400).
        HTTPException: 404 when the range holds no statement.
    """
    end = request.end_date
    if end is None:
        (end,) = cur.execute(
            "SELECT max(record_date) FROM daily_net_transfers"
        ).fetchone()
        if end is None:
            raise HTTPException(status_code=404, detail="No statements loaded")
    start = request.start_date or end - timedelta(days=365)
    if start > end:
        raise ValueError("start_date must be on or before end_date")

    rows = _rolling_rows(cur, request.metric, request.window, start, end)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No statements between {start.isoformat()} and {end.isoformat()}",
        )
    projects = request.metric == "total_withdrawals"
    points = [
        RollingPoint(
            record_date=day.isoformat(),
            value=float(value),
            rolling_average=None if avg is None else float(avg),
            projected_monthly=(
                float(avg) * MONTHLY_MULTIPLIER
                if projects and avg is not None
                else None
            ),
        )
        for day, value, avg in rows
    ]
    return RollingAverageResponse(
        metric=request.metric,
        window=request.window,
        monthly_multiplier=MONTHLY_MULTIPLIER if projects else None,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        points=points,
    )
