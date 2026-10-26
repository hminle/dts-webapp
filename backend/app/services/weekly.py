"""Weekly net-transfer comparison of two fiscal years, read on an anchor weekday.

Ported from the reference ``api/treasury/weekly.py``; only the HTTP layer moved
to ``app/api/routers/weekly.py``.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import duckdb

from app.schemas.treasury import (
    WeeklyComparisonRequest,
    WeeklyComparisonResponse,
    WeeklyDataPoint,
)
from app.utils.anchor import LOOK_BACK_DAYS, anchor_days
from app.utils.deposits_withdrawals import net_transfer_series

logger = logging.getLogger(__name__)


def _fiscal_year_dates(fiscal_year: int) -> tuple[datetime, datetime]:
    """Return ``(start, end)`` datetimes for ``fiscal_year``, clipped to today."""
    start = datetime(fiscal_year - 1, 10, 1)
    end = datetime(fiscal_year, 9, 30)
    today = datetime.now()
    return start, min(end, today)


def _build_weekly_points(
    by_date: dict[str, dict[str, Any]],
    anchors: list[datetime],
    *,
    max_days_back: int = LOOK_BACK_DAYS,
) -> list[WeeklyDataPoint]:
    """One ``WeeklyDataPoint`` per anchor day, with up to ``max_days_back`` look-back.

    ``by_date`` maps ``YYYY-MM-DD`` to :func:`net_transfer_series` metrics. A
    day without metrics is skipped and the next earlier day tried, mirroring
    the legacy behavior.
    """
    points: list[WeeklyDataPoint] = []
    for week_num, anchor in enumerate(anchors, start=1):
        for offset in range(max_days_back + 1):
            check_date = anchor - timedelta(days=offset)
            metrics = by_date.get(check_date.strftime("%Y-%m-%d"))
            if metrics is None:
                continue
            points.append(
                WeeklyDataPoint(
                    week_number=week_num,
                    record_date=metrics["date"],
                    net_transfer_today=metrics["net_flow_today"],
                    net_transfer_mtd=metrics["net_flow_mtd"],
                    net_transfer_fytd=metrics["net_flow_fytd"],
                    total_deposits=metrics["total_deposits_today"],
                    total_withdrawals=metrics["total_withdrawals_today"],
                )
            )
            break
    return points


def get_comparison(
    cur: duckdb.DuckDBPyConnection, request: WeeklyComparisonRequest
) -> WeeklyComparisonResponse:
    """Weekly net-transfer comparison between two fiscal years.

    Picks each anchor weekday (Friday by default, or Thursday), or the
    closest earlier day with data, and runs
    the shared ``net_transfer_series`` math on that day's
    rows. The second year is truncated to the first year's last week
    number so the side-by-side comparison stays apples-to-apples.
    """
    if request.first_fiscal_year == request.second_fiscal_year:
        raise ValueError("First and second fiscal years must be different")

    first_start, first_end = _fiscal_year_dates(request.first_fiscal_year)
    second_start, second_end = _fiscal_year_dates(request.second_fiscal_year)

    logger.info(
        "Fetching data for FY %s and FY %s",
        request.first_fiscal_year,
        request.second_fiscal_year,
    )

    query = """
    SELECT * FROM deposits_withdrawals
    WHERE (
        (record_date >= ? AND record_date <= ?)
        OR
        (record_date >= ? AND record_date <= ?)
    )
    ORDER BY record_date
    """
    df = cur.execute(
        query,
        (
            first_start.strftime("%Y-%m-%d"),
            first_end.strftime("%Y-%m-%d"),
            second_start.strftime("%Y-%m-%d"),
            second_end.strftime("%Y-%m-%d"),
        ),
    ).df()

    if df.empty:
        logger.warning("No data found in deposits_withdrawals table")
        return WeeklyComparisonResponse(
            first_fiscal_year=request.first_fiscal_year,
            second_fiscal_year=request.second_fiscal_year,
            first_year_data=[],
            second_year_data=[],
            comparison_weeks=0,
        )

    logger.info(f"Retrieved {len(df)} records from deposits_withdrawals table")

    by_date = {m["date"]: m for m in net_transfer_series(df)}

    weekday = request.anchor_weekday
    first_anchors = anchor_days(first_start, first_end, weekday)
    second_anchors = anchor_days(second_start, second_end, weekday)

    logger.info(
        f"Processing {len(first_anchors)} {weekday}s for FY {request.first_fiscal_year}"
    )
    logger.info(
        f"Processing {len(second_anchors)} {weekday}s for FY "
        f"{request.second_fiscal_year}"
    )

    first_year_data = _build_weekly_points(by_date, first_anchors)

    # Cut the second year at the first year's last week number, not its point
    # count: a first-year week with no statement is skipped, so counting points
    # would drop the second year's final week and leave the first year's
    # unpaired.
    comparison_weeks = first_year_data[-1].week_number if first_year_data else 0
    second_year_data = _build_weekly_points(by_date, second_anchors[:comparison_weeks])

    logger.info(
        f"Returning {len(first_year_data)} weeks for FY {request.first_fiscal_year} "
        f"and {len(second_year_data)} weeks for FY {request.second_fiscal_year}"
    )

    return WeeklyComparisonResponse(
        first_fiscal_year=request.first_fiscal_year,
        second_fiscal_year=request.second_fiscal_year,
        first_year_data=first_year_data,
        second_year_data=second_year_data,
        comparison_weeks=comparison_weeks,
    )
