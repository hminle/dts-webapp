"""The Treasury General Account's closing balance, across its storage eras."""

from __future__ import annotations

from datetime import date, timedelta

import duckdb
from fastapi import HTTPException

from app.constants.cash_balance import CLOSING_BALANCE_ROWS
from app.schemas.treasury import (
    CashBalancePoint,
    CashBalanceRequest,
    CashBalanceResponse,
)

# The column names come from CLOSING_BALANCE_ROWS, never from input, so
# interpolating them is safe; the account types are bound as parameters.
_CASE = "\n".join(f"WHEN ? THEN {row.column}" for row in CLOSING_BALANCE_ROWS)
_ACCOUNTS = [row.account_type for row in CLOSING_BALANCE_ROWS]
_QUERY = f"""
SELECT record_date, CASE account_type {_CASE} END AS closing_balance
FROM operating_cash_balance
WHERE account_type IN ({", ".join("?" for _ in CLOSING_BALANCE_ROWS)})
  AND record_date BETWEEN ? AND ?
ORDER BY record_date
"""


def _balances(
    cur: duckdb.DuckDBPyConnection, start: date, end: date
) -> list[tuple[date, float]]:
    """``(record_date, closing_balance)`` for each statement in the range.

    Raises:
        RuntimeError: A balance row has no amount in its era's column, which
            means the Treasury moved the balance again and
            ``CLOSING_BALANCE_ROWS`` needs a new era.
    """
    rows = cur.execute(_QUERY, [*_ACCOUNTS, *_ACCOUNTS, start, end]).fetchall()
    for day, balance in rows:
        if balance is None:
            raise RuntimeError(f"No TGA closing balance on {day.isoformat()}")
    return [(day, float(balance)) for day, balance in rows]


def balance_on(cur: duckdb.DuckDBPyConnection, day: str) -> float | None:
    """The closing balance on ``day``; ``None`` when it has no balance row."""
    on = date.fromisoformat(day)
    rows = _balances(cur, on, on)
    return rows[0][1] if rows else None


def get_daily(
    cur: duckdb.DuckDBPyConnection, request: CashBalanceRequest
) -> CashBalanceResponse:
    """The TGA closing balance on each statement date in the range.

    Raises:
        ValueError: ``start_date`` is after ``end_date`` (HTTP 400).
        HTTPException: 404 when the range holds no balance.
    """
    end = request.end_date
    if end is None:
        (end,) = cur.execute(
            "SELECT max(record_date) FROM operating_cash_balance"
        ).fetchone()
        if end is None:
            raise HTTPException(status_code=404, detail="No statements loaded")
    start = request.start_date or end - timedelta(days=365)
    if start > end:
        raise ValueError("start_date must be on or before end_date")

    rows = _balances(cur, start, end)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No cash balance between {start.isoformat()} and {end.isoformat()}"
            ),
        )
    return CashBalanceResponse(
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        points=[
            CashBalancePoint(record_date=day.isoformat(), closing_balance=balance)
            for day, balance in rows
        ],
    )
