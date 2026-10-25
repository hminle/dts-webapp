"""Weekly snapshot: one week's statement against the same business day a year ago.

Reads ``daily_net_transfers`` (built at ingestion) plus one category sum, so it
re-implements no net-transfer maths.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

import duckdb
from fastapi import HTTPException

from app.constants.categories import CATEGORY_REGISTRY
from app.schemas.treasury import (
    SnapshotFigure,
    WeeklySnapshotRequest,
    WeeklySnapshotResponse,
)
from app.services.categories import category_fytd
from app.utils.anchor import LOOK_BACK_DAYS, anchor_on_or_before
from app.utils.yoy import nullable_yoy

logger = logging.getLogger(__name__)

WITHHOLDING = CATEGORY_REGISTRY["Employment & Withholding Tax"]

_ROW_COLUMNS = """
    record_date, record_fiscal_year, day_of_fiscal_year,
    total_withdrawals_fytd, total_deposits_fytd, net_flow_fytd,
    total_withdrawals_mtd, net_flow_mtd
"""


@dataclass(frozen=True)
class _Row:
    """The ``daily_net_transfers`` columns the snapshot reads."""

    record_date: str
    fiscal_year: int
    day_of_fiscal_year: int
    withdrawals_fytd: float
    deposits_fytd: float
    net_fytd: float
    withdrawals_mtd: float
    net_mtd: float


def _row(values: tuple | None) -> _Row | None:
    if values is None:
        return None
    day, fy, n, w_fytd, d_fytd, net_fytd, w_mtd, net_mtd = values
    return _Row(
        record_date=day.isoformat(),
        fiscal_year=int(fy),
        day_of_fiscal_year=int(n),
        withdrawals_fytd=float(w_fytd),
        deposits_fytd=float(d_fytd),
        net_fytd=float(net_fytd),
        withdrawals_mtd=float(w_mtd),
        net_mtd=float(net_mtd),
    )


def _latest_on_or_before(cur: duckdb.DuckDBPyConnection, as_of: date | None) -> date:
    """The newest statement date, at or before ``as_of`` when given."""
    if as_of is None:
        (latest,) = cur.execute(
            "SELECT max(record_date) FROM daily_net_transfers"
        ).fetchone()
    else:
        (latest,) = cur.execute(
            "SELECT max(record_date) FROM daily_net_transfers WHERE record_date <= ?",
            [as_of],
        ).fetchone()
    if latest is None:
        where = f" on or before {as_of.isoformat()}" if as_of else ""
        raise HTTPException(status_code=404, detail=f"No statement{where}")
    return latest


def _statement_for_week(cur: duckdb.DuckDBPyConnection, anchor: date) -> _Row | None:
    """The latest statement from ``anchor`` back ``LOOK_BACK_DAYS`` days."""
    return _row(
        cur.execute(
            f"""
            SELECT {_ROW_COLUMNS} FROM daily_net_transfers
            WHERE record_date BETWEEN ? AND ?
            ORDER BY record_date DESC
            LIMIT 1
            """,
            [anchor - timedelta(days=LOOK_BACK_DAYS), anchor],
        ).fetchone()
    )


def _year_before(cur: duckdb.DuckDBPyConnection, row: _Row) -> _Row | None:
    """The previous fiscal year's statement with the same day number."""
    return _row(
        cur.execute(
            f"""
            SELECT {_ROW_COLUMNS} FROM daily_net_transfers
            WHERE record_fiscal_year = ? AND day_of_fiscal_year = ?
            """,
            [row.fiscal_year - 1, row.day_of_fiscal_year],
        ).fetchone()
    )


def _figure(current: float | None, previous: float | None) -> SnapshotFigure:
    change, pct = nullable_yoy(current, previous)
    return SnapshotFigure(
        current=current, previous=previous, change=change, percent_change=pct
    )


def get_weekly(
    cur: duckdb.DuckDBPyConnection, request: WeeklySnapshotRequest
) -> WeeklySnapshotResponse:
    """The latest completed week's statement, against a year earlier.

    The week ends on ``request.anchor_weekday``; after a holiday the closest
    earlier statement within ``LOOK_BACK_DAYS`` stands in. The previous year
    is lined up by ``day_of_fiscal_year``.

    Raises:
        HTTPException: 404 when there is no statement on or before ``as_of``,
            or none in the anchor week.
    """
    latest = _latest_on_or_before(cur, request.as_of)
    anchor = anchor_on_or_before(latest, request.anchor_weekday)
    current = _statement_for_week(cur, anchor)
    if current is None:
        start = anchor - timedelta(days=LOOK_BACK_DAYS)
        raise HTTPException(
            status_code=404,
            detail=f"No statement between {start.isoformat()} and {anchor.isoformat()}",
        )
    previous = _year_before(cur, current)

    def pair(attr: str) -> SnapshotFigure:
        return _figure(
            getattr(current, attr), getattr(previous, attr) if previous else None
        )

    net = pair("net_fytd")
    withholding = _figure(
        category_fytd(cur, WITHHOLDING, current.record_date),
        category_fytd(cur, WITHHOLDING, previous.record_date) if previous else None,
    )

    week_before = _statement_for_week(cur, anchor - timedelta(days=7))
    previous_gap: float | None = None
    gap_change: float | None = None
    reason: str | None = None
    if week_before is None:
        reason = "No statement in the previous week"
    elif week_before.fiscal_year != current.fiscal_year:
        reason = (
            f"Last week was in FY{week_before.fiscal_year}; a gap across "
            "October 1 compares different years"
        )
    else:
        year_before_last_week = _year_before(cur, week_before)
        if year_before_last_week is not None:
            previous_gap = week_before.net_fytd - year_before_last_week.net_fytd
        if previous_gap is None or net.change is None:
            reason = "No aligned previous-year statement"
        else:
            gap_change = net.change - previous_gap

    logger.info(
        "Weekly snapshot (%s): %s day %s vs %s",
        request.anchor_weekday,
        current.record_date,
        current.day_of_fiscal_year,
        previous.record_date if previous else None,
    )
    return WeeklySnapshotResponse(
        anchor_weekday=request.anchor_weekday,
        anchor_date=anchor.isoformat(),
        record_date=current.record_date,
        fiscal_year=current.fiscal_year,
        day_of_fiscal_year=current.day_of_fiscal_year,
        previous_fiscal_year=current.fiscal_year - 1,
        previous_date=previous.record_date if previous else None,
        withdrawals_mtd=current.withdrawals_mtd,
        net_transfers_mtd=current.net_mtd,
        withdrawals_fytd=pair("withdrawals_fytd"),
        deposits_fytd=pair("deposits_fytd"),
        net_transfers_fytd=net,
        withholding_fytd=withholding,
        previous_week_date=week_before.record_date if week_before else None,
        previous_week_net_transfers_gap=previous_gap,
        net_transfers_gap_change=gap_change,
        gap_change_unavailable_reason=reason,
    )
