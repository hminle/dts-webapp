"""Weekly snapshot: one week's statement against the same fiscal day a year ago."""

from datetime import date

import pytest
from fastapi import HTTPException

from app.schemas.treasury import WeeklySnapshotRequest
from app.services.snapshot import get_weekly
from tests.fixtures import apd_row, catg_row, dnt_row, dw_row, formula_db, ocb_row

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


def test_snapshot_adds_leading_flows_and_combined_figures() -> None:
    # The 10 statements ending 2025-12-04 (Thanksgiving skipped).
    days = [date(2025, 11, d) for d in (20, 21, 24, 25, 26, 28)] + [
        date(2025, 12, d) for d in (1, 2, 3)
    ]
    withdrawals = [19815, 31192, 16793, 19998, 54507, 13595, 125763, 13764, 44733]
    unemployment = [78, 63, 193, 241, 353, 56, 212, 269, 164, 107]
    rows = [
        dnt_row(
            d, 2026, 34 + i, withdrawals_fytd=0, deposits_fytd=0, withdrawals_today=v
        )
        for i, (d, v) in enumerate(zip(days, withdrawals, strict=True))
    ]
    current, previous = _dec_4_rows()
    current["total_withdrawals_today"] = 15928
    rows += [current, previous]

    def line(day, fy, side, catg, fytd):
        return catg_row(
            day, fy, transaction_type=side, transaction_catg=catg, fytd=fytd
        )

    cur_day, prev_day = date(2025, 12, 4), date(2024, 12, 4)
    lines = [
        dw_row(
            d,
            2026,
            account_type="Treasury General Account (TGA)",
            transaction_type="Withdrawals",
            transaction_catg="DOL - Unemployment Benefits",
            today=v,
        )
        for d, v in zip([*days, cur_day], unemployment, strict=True)
    ]
    interest, cbp = (
        "Interest on Treasury Securities",
        ("DHS - Customs & Border Protection (CBP)"),
    )
    lines += [
        line(cur_day, 2026, "Withdrawals", interest, 141720),
        line(prev_day, 2025, "Withdrawals", interest, 120038),
        line(cur_day, 2026, "Deposits", "DHS - Customs Duties, Taxes, and Fees", 68584),
        line(cur_day, 2026, "Withdrawals", cbp, 3180),
        line(
            prev_day, 2025, "Deposits", "DHS - Customs and Certain Excise Taxes", 17730
        ),
        line(prev_day, 2025, "Withdrawals", cbp, 1807),
    ]
    adjustments = [
        apd_row(cur_day, 2026, adj_type="Bills (-)", fytd=49128),
        apd_row(cur_day, 2026, adj_type="Bonds and Notes (-)", fytd=1749),
        apd_row(prev_day, 2025, adj_type="Bills (-)", fytd=53521),
        apd_row(prev_day, 2025, adj_type="Bonds and Notes (-)", fytd=4122),
    ]
    conn = formula_db(
        {
            "daily_net_transfers": rows,
            "deposits_withdrawals": lines,
            "adjustment_public_debt": adjustments,
        }
    )
    s = _snapshot(conn)
    assert s.withdrawals_10d_average == pytest.approx(35608.8)
    assert s.projected_monthly_withdrawals == pytest.approx(712176)
    assert s.unemployment_10d_average == pytest.approx(173.6)
    assert (s.interest_income_fytd.current, s.interest_income_fytd.previous) == (
        192597,
        177681,
    )
    assert s.interest_income_fytd.change == 14916
    assert (s.net_customs_fytd.current, s.net_customs_fytd.change) == (65404, 49481)


def test_snapshot_cash_balance_against_last_week_and_a_year_ago() -> None:
    closing = "Treasury General Account (TGA) Closing Balance"
    conn = formula_db(
        {
            "daily_net_transfers": [*_dec_4_rows(), *_nov_26_rows()],
            "operating_cash_balance": [
                ocb_row(d, fy, account_type=closing, open_today=v)
                for d, fy, v in (
                    (date(2025, 12, 4), 2026, 878666),
                    (date(2025, 11, 26), 2026, 899678),
                    (date(2024, 12, 4), 2025, 815011),
                )
            ],
        }
    )
    cash = _snapshot(conn).cash_balance
    assert (cash.closing, cash.previous_week, cash.year_ago) == (
        878666,
        899678,
        815011,
    )
    assert cash.change_week == -21012
    assert cash.change_year == 63655
    assert cash.percent_change_year == pytest.approx(7.810, abs=1e-3)


def test_snapshot_cash_balance_is_null_without_balance_rows() -> None:
    cash = _snapshot(_db(_dec_4_rows())).cash_balance
    assert cash.closing is None
    assert cash.change_week is None
    assert cash.change_year is None


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
