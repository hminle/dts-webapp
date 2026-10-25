"""Weekly snapshot: one week's statement against the same fiscal day a year ago."""

from datetime import date

import pytest
from fastapi import HTTPException

from app.schemas.treasury import WeeklySnapshotRequest
from app.services.snapshot import get_weekly
from tests.fixtures import catg_row, dnt_row, formula_db

WITHHELD = "Taxes - Withheld Individual/FICA"


def _withheld(day: date, fy: int, fytd: float):
    return catg_row(
        day, fy, transaction_type="Deposits", transaction_catg=WITHHELD, fytd=fytd
    )


def _db(rows, withholding=()):
    return formula_db(
        {"daily_net_transfers": list(rows), "deposits_withdrawals": list(withholding)}
    )


def _snapshot(conn, as_of: date | None = None, anchor: str = "thursday"):
    return get_weekly(
        conn.cursor(), WeeklySnapshotRequest(anchor_weekday=anchor, as_of=as_of)
    )


def _dec_4_rows():
    return [
        dnt_row(
            date(2025, 12, 4),
            2026,
            44,
            withdrawals_fytd=1432895,
            deposits_fytd=957420,
            withdrawals_mtd=200188,
            net_mtd=120817,
        ),
        dnt_row(
            date(2024, 12, 4), 2025, 44, withdrawals_fytd=1404753, deposits_fytd=817202
        ),
    ]


def _nov_26_rows():
    return [
        dnt_row(
            date(2025, 11, 26), 2026, 39, withdrawals_fytd=1219111, deposits_fytd=855661
        ),
        dnt_row(
            date(2024, 11, 26), 2025, 39, withdrawals_fytd=1162688, deposits_fytd=709659
        ),
    ]


def test_thursday_snapshot_pairs_the_same_fiscal_day() -> None:
    conn = _db(
        _dec_4_rows(),
        [
            _withheld(date(2025, 12, 4), 2026, 591734),
            _withheld(date(2024, 12, 4), 2025, 568727),
        ],
    )
    s = _snapshot(conn)
    assert (s.anchor_date, s.record_date, s.previous_date) == (
        "2025-12-04",
        "2025-12-04",
        "2024-12-04",
    )
    assert (s.fiscal_year, s.previous_fiscal_year, s.day_of_fiscal_year) == (
        2026,
        2025,
        44,
    )
    assert (s.withdrawals_mtd, s.net_transfers_mtd) == (200188, 120817)
    assert (s.withdrawals_fytd.change, s.deposits_fytd.change) == (28142, 140218)
    assert s.net_transfers_fytd.current == 475475
    assert s.net_transfers_fytd.previous == 587551
    assert s.net_transfers_fytd.change == -112076
    assert s.net_transfers_fytd.percent_change == pytest.approx(-19.075, abs=1e-3)
    assert s.withholding_fytd.change == 23007
    assert s.withholding_fytd.percent_change == pytest.approx(4.045, abs=1e-3)


def test_a_holiday_anchor_uses_the_closest_earlier_statement() -> None:
    # Thursday 2025-11-27 was Thanksgiving: no statement. The Friday after it
    # makes the week complete, so its Thursday is the anchor.
    rows = [
        *_nov_26_rows(),
        dnt_row(date(2025, 11, 28), 2026, 40, withdrawals_fytd=1, deposits_fytd=0),
    ]
    conn = _db(rows)
    s = _snapshot(conn, as_of=date(2025, 11, 28))
    assert (s.anchor_date, s.record_date) == ("2025-11-27", "2025-11-26")
    assert s.day_of_fiscal_year == 39


def test_a_wednesday_latest_reads_last_weeks_thursday() -> None:
    rows = [
        *_dec_4_rows(),
        dnt_row(date(2025, 12, 10), 2026, 48, withdrawals_fytd=1, deposits_fytd=0),
    ]
    s = _snapshot(_db(rows))
    assert (s.anchor_date, s.record_date) == ("2025-12-04", "2025-12-04")


def test_friday_anchor() -> None:
    rows = [
        *_dec_4_rows(),
        dnt_row(date(2025, 12, 5), 2026, 45, withdrawals_fytd=10, deposits_fytd=4),
    ]
    s = _snapshot(_db(rows), anchor="friday")
    assert (s.anchor_weekday, s.anchor_date, s.record_date) == (
        "friday",
        "2025-12-05",
        "2025-12-05",
    )


def test_gap_change_widens() -> None:
    s = _snapshot(_db([*_dec_4_rows(), *_nov_26_rows()]))
    assert s.previous_week_date == "2025-11-26"
    assert s.previous_week_net_transfers_gap == -89579
    assert s.net_transfers_gap_change == -22497
    assert s.gap_change_unavailable_reason is None


def test_gap_change_is_null_across_october_1() -> None:
    rows = [
        dnt_row(date(2025, 10, 2), 2026, 2, withdrawals_fytd=3, deposits_fytd=1),
        dnt_row(date(2024, 10, 2), 2025, 2, withdrawals_fytd=2, deposits_fytd=1),
        dnt_row(date(2025, 9, 25), 2025, 248, withdrawals_fytd=9, deposits_fytd=1),
    ]
    s = _snapshot(_db(rows))
    assert s.previous_week_date == "2025-09-25"
    assert s.net_transfers_gap_change is None
    assert s.gap_change_unavailable_reason == (
        "Last week was in FY2025; a gap across October 1 compares different years"
    )


def test_missing_previous_year_day_is_null() -> None:
    rows = [dnt_row(date(2025, 12, 4), 2026, 44, withdrawals_fytd=5, deposits_fytd=2)]
    s = _snapshot(_db(rows))
    assert s.previous_date is None
    assert s.net_transfers_fytd.current == 3
    assert s.net_transfers_fytd.previous is None
    assert s.net_transfers_fytd.change is None
    assert s.withholding_fytd.previous is None
    assert s.gap_change_unavailable_reason == "No statement in the previous week"


def test_no_statement_is_404() -> None:
    with pytest.raises(HTTPException) as empty:
        _snapshot(formula_db({}))
    assert empty.value.status_code == 404

    with pytest.raises(HTTPException) as early:
        _snapshot(_db(_dec_4_rows()), as_of=date(2024, 1, 1))
    assert early.value.detail == "No statement on or before 2024-01-01"
