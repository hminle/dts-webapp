"""Weekly comparison: each fiscal year read on an anchor weekday."""

from datetime import date, datetime

import pandas as pd
import pytest

from app.schemas.treasury import WeeklyComparisonRequest
from app.services.weekly import (
    _build_weekly_points,
    _fiscal_year_dates,
    get_comparison,
)
from app.utils.anchor import anchor_days
from tests.fixtures import dw_day, formula_db


def _day(d: date, fy: int, net: float = 1):
    return dw_day(d, fy, deposits=0, withdrawals=net, debt_issues=0, debt_redemptions=0)


@pytest.mark.parametrize(
    ("weekday", "days", "empty_window"),
    [
        ("friday", [3, 10, 17, 24, 31], (4, 9)),
        ("thursday", [2, 9, 16, 23, 30], (3, 8)),
    ],
)
def test_anchor_days_between_two_dates(
    weekday, days: list[int], empty_window: tuple[int, int]
) -> None:
    anchors = anchor_days(datetime(2025, 10, 1), datetime(2025, 10, 31), weekday)
    assert [a.day for a in anchors] == days
    assert all(isinstance(a, datetime) for a in anchors)
    first, last = empty_window
    assert (
        anchor_days(datetime(2025, 10, first), datetime(2025, 10, last), weekday) == []
    )


def test_fiscal_year_runs_october_to_september_clipped_to_today() -> None:
    start, end = _fiscal_year_dates(2026)
    assert (start, end) == (datetime(2025, 10, 1), datetime(2026, 9, 30))
    _, future_end = _fiscal_year_dates(2100)
    assert future_end <= datetime.now()


def test_a_holiday_friday_uses_the_closest_earlier_statement() -> None:
    df = pd.concat(
        [
            _day(date(2025, 10, 3), 2026, 2),
            _day(date(2025, 10, 9), 2026, 3),
            _day(date(2025, 10, 24), 2026, 4),
        ]
    )
    df["record_date"] = pd.to_datetime(df["record_date"])
    fridays = anchor_days(datetime(2025, 10, 1), datetime(2025, 10, 24), "friday")
    points = _build_weekly_points(df, fridays)
    # Week 2's Friday (Oct 10) had no statement, so Thursday Oct 9 stands in.
    # Week 3 has nothing within 5 days back and is skipped; week 4 keeps its number.
    assert [(p.week_number, p.record_date) for p in points] == [
        (1, "2025-10-03"),
        (2, "2025-10-09"),
        (4, "2025-10-24"),
    ]
    assert points[1].net_transfer_today == 3
    assert points[1].net_transfer_fytd == 300


def test_second_year_is_cut_to_the_first_years_week_count() -> None:
    conn = formula_db(
        {
            "deposits_withdrawals": [
                _day(date(2025, 10, 3), 2026),
                _day(date(2025, 10, 9), 2026),
                *(_day(date(2024, 10, d), 2025) for d in (4, 11, 18)),
            ]
        }
    )
    result = get_comparison(
        conn.cursor(),
        WeeklyComparisonRequest(first_fiscal_year=2026, second_fiscal_year=2025),
    )
    assert result.comparison_weeks == 2
    assert [p.record_date for p in result.first_year_data] == [
        "2025-10-03",
        "2025-10-09",
    ]
    assert [p.record_date for p in result.second_year_data] == [
        "2024-10-04",
        "2024-10-11",
    ]


def test_comparing_a_year_with_itself_is_rejected() -> None:
    conn = formula_db({})
    with pytest.raises(ValueError, match="must be different"):
        get_comparison(
            conn.cursor(),
            WeeklyComparisonRequest(first_fiscal_year=2026, second_fiscal_year=2026),
        )


def test_a_skipped_first_year_week_keeps_the_second_years_matching_week() -> None:
    # The first year has weeks 1, 2 and 4 (week 3 had no statement), so the
    # second year is cut after week 4, not after 3 points, and every first-year
    # week keeps its partner.
    conn = formula_db(
        {
            "deposits_withdrawals": [
                *(_day(date(2025, 10, d), 2026) for d in (3, 10, 24)),
                *(_day(date(2024, 10, d), 2025) for d in (4, 11, 18, 25, 31)),
            ]
        }
    )
    result = get_comparison(
        conn.cursor(),
        WeeklyComparisonRequest(first_fiscal_year=2026, second_fiscal_year=2025),
    )
    assert [p.week_number for p in result.first_year_data] == [1, 2, 4]
    assert [p.week_number for p in result.second_year_data] == [1, 2, 3, 4]
    assert result.comparison_weeks == 4


def test_thursday_anchor_uses_thursdays() -> None:
    conn = formula_db(
        {
            "deposits_withdrawals": [
                *(_day(date(2025, 10, d), 2026) for d in (2, 3, 9, 10)),
                *(_day(date(2024, 10, d), 2025) for d in (3, 4, 10, 11)),
            ]
        }
    )
    result = get_comparison(
        conn.cursor(),
        WeeklyComparisonRequest(
            first_fiscal_year=2026, second_fiscal_year=2025, anchor_weekday="thursday"
        ),
    )
    assert [p.record_date for p in result.first_year_data] == [
        "2025-10-02",
        "2025-10-09",
    ]
    assert [p.record_date for p in result.second_year_data] == [
        "2024-10-03",
        "2024-10-10",
    ]
