"""Year over year: difference, percent change, and how two years are lined up."""

from datetime import date

import pytest

from app.ingest.populate import populate_fiscal_years
from app.schemas.treasury import YoYDailyComparisonRequest
from app.services.yoy import get_daily_comparison
from app.utils.yoy import (
    FYTDSource,
    fetch_component_fytd,
    fetch_components_daily,
    find_aligned_previous_date,
    yoy_change,
)
from tests.fixtures import catg_row, dw_day, formula_db

SOURCE = FYTDSource(
    table="deposits_withdrawals",
    fytd_column="transaction_fytd_amt",
    key_column="transaction_catg",
)
WITHDRAWALS_ONLY = FYTDSource(
    table="deposits_withdrawals",
    fytd_column="transaction_fytd_amt",
    key_column="transaction_catg",
    extra_filters={"transaction_type": "Withdrawals"},
)

# FY2026 has 3 statements, FY2027 has 4. 2025-10-04/05 is a weekend, so the
# MM-DD 10-05 and 10-06 of FY2027 have no counterpart.
PREV_DAYS = [date(2025, 10, 1), date(2025, 10, 2), date(2025, 10, 3)]
CUR_DAYS = [date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 5), date(2026, 10, 6)]


def _two_years(prev_net: list[float], cur_net: list[float]):
    """An artifact whose FYTD net transfers are ``net × 100`` per day."""
    frames = [
        dw_day(d, fy, deposits=0, withdrawals=n, debt_issues=0, debt_redemptions=0)
        for fy, days, nets in ((2026, PREV_DAYS, prev_net), (2027, CUR_DAYS, cur_net))
        for d, n in zip(days, nets, strict=True)
    ]
    conn = formula_db({"deposits_withdrawals": frames})
    populate_fiscal_years(conn, [2026, 2027])
    return conn


@pytest.mark.parametrize(
    ("current", "previous", "delta", "pct"),
    [
        (108932, 94000, 14932, 15.885),
        (-30, -50, 20, 40.0),
        (30, -50, 80, 160.0),
        (5, 0, 5, None),
        (0, 0, 0, None),
    ],
    ids=["growth", "negative-base-improves", "sign-flip", "zero-base", "both-zero"],
)
def test_yoy_change_divides_by_the_size_of_last_year(
    current: float, previous: float, delta: float, pct: float | None
) -> None:
    got_delta, got_pct = yoy_change(current, previous)
    assert got_delta == delta
    assert got_pct == (None if pct is None else pytest.approx(pct, abs=1e-3))


class TestFindAlignedPreviousDate:
    @pytest.fixture
    def conn(self):
        return _two_years([1, 2, 3], [1, 2, 3, 4])

    def _find(self, conn, current: str, mode: str) -> str | None:
        return find_aligned_previous_date(
            conn,
            source=SOURCE,
            current_date=current,
            current_fy=2027,
            previous_fy=2026,
            mode=mode,
        )

    def test_fiscal_day_pairs_day_n_with_day_n(self, conn) -> None:
        assert self._find(conn, "2026-10-02", "fiscal_day") == "2025-10-02"

    def test_fiscal_day_past_last_years_end_uses_its_latest(self, conn) -> None:
        assert self._find(conn, "2026-10-06", "fiscal_day") == "2025-10-03"

    def test_fiscal_day_before_any_statement_uses_last_years_latest(self, conn) -> None:
        assert self._find(conn, "2026-09-30", "fiscal_day") == "2025-10-03"

    def test_calendar_date_uses_the_same_month_and_day(self, conn) -> None:
        assert self._find(conn, "2026-10-02", "calendar_date") == "2025-10-02"

    def test_calendar_date_on_a_weekend_uses_the_statement_before(self, conn) -> None:
        # 2025-10-05 is a Sunday.
        assert self._find(conn, "2026-10-05", "calendar_date") == "2025-10-03"

    def test_calendar_date_with_nothing_earlier_uses_last_years_latest(self) -> None:
        conn = formula_db(
            {
                "deposits_withdrawals": [
                    dw_day(
                        d,
                        fy,
                        deposits=1,
                        withdrawals=1,
                        debt_issues=0,
                        debt_redemptions=0,
                    )
                    for d, fy in ((date(2025, 10, 3), 2026), (date(2026, 10, 1), 2027))
                ]
            }
        )
        assert self._find(conn, "2026-10-01", "calendar_date") == "2025-10-03"


def test_component_fytd_honours_the_transaction_type_filter() -> None:
    catg = "Interest on Treasury Securities"
    d = date(2026, 10, 19)
    conn = formula_db(
        {
            "deposits_withdrawals": [
                catg_row(
                    d,
                    2027,
                    transaction_type="Withdrawals",
                    transaction_catg=catg,
                    fytd=11626,
                ),
                catg_row(
                    d,
                    2027,
                    transaction_type="Deposits",
                    transaction_catg=catg,
                    fytd=999,
                ),
            ]
        }
    )
    assert fetch_component_fytd(conn, WITHDRAWALS_ONLY, "2026-10-19", catg) == 11626
    assert fetch_component_fytd(conn, WITHDRAWALS_ONLY, "2026-10-19", "absent") == 0.0


def test_components_daily_sums_keys_per_date_in_order() -> None:
    a, b = "SSA - Benefits Payments", "SSA - Supplemental Security Income"
    d1, d2 = date(2026, 10, 2), date(2026, 10, 1)
    conn = formula_db(
        {
            "deposits_withdrawals": [
                catg_row(
                    day,
                    2027,
                    transaction_type="Withdrawals",
                    transaction_catg=k,
                    fytd=v,
                )
                for day, k, v in ((d1, a, 10), (d1, b, 5), (d2, a, 4), (d2, b, 1))
            ]
        }
    )
    assert fetch_components_daily(conn, WITHDRAWALS_ONLY, 2027, (a, b)) == [
        ("2026-10-01", 5.0),
        ("2026-10-02", 15.0),
    ]
    assert fetch_components_daily(conn, WITHDRAWALS_ONLY, 2027, ()) == []


def _daily(conn, mode: str):
    return get_daily_comparison(
        conn.cursor(),
        YoYDailyComparisonRequest(
            current_fiscal_year=2027,
            previous_fiscal_year=2026,
            metric="net_flow",
            comparison_mode=mode,
        ),
    )


def test_daily_fiscal_day_stops_at_the_shorter_year() -> None:
    result = _daily(_two_years([0, 2, 3], [1, 2, 3, 4]), "fiscal_day")
    assert [p.day_of_fiscal_year for p in result.data_points] == [1, 2, 3]
    first = result.data_points[0]
    # FYTD net transfers are net × 100 (dw_day); last year's day 1 was zero.
    assert (first.current_value, first.previous_value) == (100, 0)
    assert first.difference == 100
    assert first.percent_change is None
    third = result.data_points[2]
    assert (third.current_date, third.previous_date) == ("2026-10-05", "2025-10-03")


def test_daily_calendar_date_keeps_only_dates_both_years_have() -> None:
    result = _daily(_two_years([1, 2, 3], [1, 2, 3, 4]), "calendar_date")
    assert [(p.current_date, p.previous_date) for p in result.data_points] == [
        ("2026-10-01", "2025-10-01"),
        ("2026-10-02", "2025-10-02"),
    ]
