"""Net transfers: total deposits, total withdrawals and their difference.

Exercises ``calculate_daily_net_transfers`` directly, including each fallback it
takes when a statement lacks the pre-aggregated total rows.
"""

from datetime import date

import pandas as pd
import pytest

from app.utils.deposits_withdrawals import (
    calculate_daily_net_transfers,
    net_transfer_series,
)
from tests.fixtures import dw_day, dw_day_without_totals, dw_row

DAY = date(2026, 10, 19)
FY = 2027
TGA = "Treasury General Account (TGA)"
FRA = "Federal Reserve Account"
ISSUES = "Public Debt Cash Issues (Table IIIB)"
REDEMPTIONS = "Public Debt Cash Redemp. (Table IIIB)"


def _run(*frames: pd.DataFrame) -> dict | None:
    return calculate_daily_net_transfers(
        pd.concat(frames, ignore_index=True), DAY.isoformat()
    )


def test_subtracts_borrowing_from_the_pre_aggregated_totals() -> None:
    # The 2026-10-19 statement.
    m = _run(
        dw_day(
            DAY,
            FY,
            deposits=32776,
            withdrawals=16223,
            debt_issues=1023,
            debt_redemptions=1225,
        )
    )
    assert m["tga_total_deposits_today"] == 32776
    assert m["public_debt_issues_today"] == 1023
    assert m["total_deposits_today"] == 31753
    assert m["tga_total_withdrawals_today"] == 16223
    assert m["public_debt_redemptions_today"] == 1225
    assert m["total_withdrawals_today"] == 14998
    assert m["net_flow_today"] == -16755
    assert m["leading_flow"] == m["total_withdrawals_today"]


def test_mtd_and_fytd_use_the_same_subtractions() -> None:
    # dw_day sets MTD = today × 10 and FYTD = today × 100.
    m = _run(
        dw_day(
            DAY, FY, deposits=500, withdrawals=800, debt_issues=100, debt_redemptions=50
        )
    )
    for period, scale in (("today", 1), ("mtd", 10), ("fytd", 100)):
        assert m[f"total_deposits_{period}"] == 400 * scale
        assert m[f"total_withdrawals_{period}"] == 750 * scale
        assert m[f"net_flow_{period}"] == 350 * scale


def test_without_total_rows_it_sums_the_tga_line_items() -> None:
    m = _run(
        dw_row(DAY, FY, account_type=TGA, transaction_type="Deposits", today=100),
        dw_row(DAY, FY, account_type=TGA, transaction_type="Deposits", today=50),
        dw_row(DAY, FY, account_type=TGA, transaction_type="Withdrawals", today=300),
    )
    assert m["tga_total_deposits_today"] == 150
    assert m["tga_total_withdrawals_today"] == 300
    assert m["net_flow_today"] == 150


def test_line_item_sums_include_the_debt_rows_before_subtracting_them() -> None:
    # The fallback sums every TGA deposit row, the debt-issue row included, and
    # then subtracts debt issues: borrowing cancels out as it should.
    m = _run(
        dw_row(DAY, FY, account_type=TGA, transaction_type="Deposits", today=100),
        dw_row(
            DAY,
            FY,
            account_type=TGA,
            transaction_type="Deposits",
            transaction_catg=ISSUES,
            today=40,
        ),
        dw_row(DAY, FY, account_type=TGA, transaction_type="Withdrawals", today=90),
    )
    assert m["tga_total_deposits_today"] == 140
    assert m["total_deposits_today"] == 100


def test_pre_2015_statements_fall_back_to_the_federal_reserve_account() -> None:
    m = _run(
        dw_row(DAY, FY, account_type=FRA, transaction_type="Deposits", today=70),
        dw_row(DAY, FY, account_type=FRA, transaction_type="Withdrawals", today=95),
        dw_row(
            DAY,
            FY,
            account_type=FRA,
            transaction_type="Deposits",
            transaction_catg=ISSUES,
            today=20,
        ),
        dw_row(
            DAY,
            FY,
            account_type=FRA,
            transaction_type="Withdrawals",
            transaction_catg=REDEMPTIONS,
            today=15,
        ),
    )
    assert m["public_debt_issues_today"] == 20
    assert m["public_debt_redemptions_today"] == 15
    # Sums include the debt rows (90 and 110), which are then subtracted.
    assert m["total_deposits_today"] == 70
    assert m["total_withdrawals_today"] == 95
    assert m["net_flow_today"] == 25


def test_missing_debt_rows_count_as_zero() -> None:
    m = _run(
        dw_row(
            DAY,
            FY,
            account_type="Treasury General Account Total Deposits",
            transaction_type="Deposits",
            today=200,
        ),
        dw_row(
            DAY,
            FY,
            account_type="Treasury General Account Total Withdrawals",
            transaction_type="Withdrawals",
            today=260,
        ),
    )
    assert m["public_debt_issues_today"] == 0
    assert m["public_debt_redemptions_today"] == 0
    assert m["net_flow_today"] == 60


@pytest.mark.parametrize(
    "frame",
    [
        pd.DataFrame(),
        dw_day_without_totals(DAY, FY),
        dw_row(DAY, FY, account_type=TGA, transaction_type="Deposits", today=10),
    ],
    ids=["empty", "no-usable-rows", "deposits-only"],
)
def test_returns_none_when_a_side_is_missing(frame: pd.DataFrame) -> None:
    assert calculate_daily_net_transfers(frame, DAY.isoformat()) is None


@pytest.mark.parametrize(
    ("deposits", "withdrawals", "sign"),
    [(100, 150, 1), (150, 100, -1), (120, 120, 0)],
    ids=["outflow", "inflow", "balanced"],
)
def test_positive_means_more_went_out_than_came_in(
    deposits: float, withdrawals: float, sign: int
) -> None:
    m = _run(
        dw_day(
            DAY,
            FY,
            deposits=deposits,
            withdrawals=withdrawals,
            debt_issues=0,
            debt_redemptions=0,
        )
    )
    net = m["net_flow_today"]
    assert (net > 0) - (net < 0) == sign


OLD_ISSUES = "Public Debt Cash Issues (Table III-B)"
OLD_REDEMPTIONS = "Public Debt Cash Redemp. (Table III-B)"
TTL = "Tax and Loan Note Accounts"


def test_debt_lines_under_their_pre_2022_09_12_names_are_removed() -> None:
    m = _run(
        dw_row(DAY, FY, account_type=TGA, transaction_type="Deposits", today=100),
        dw_row(
            DAY,
            FY,
            account_type=TGA,
            transaction_type="Deposits",
            transaction_catg=OLD_ISSUES,
            today=900,
        ),
        dw_row(DAY, FY, account_type=TGA, transaction_type="Withdrawals", today=60),
        dw_row(
            DAY,
            FY,
            account_type=TGA,
            transaction_type="Withdrawals",
            transaction_catg=OLD_REDEMPTIONS,
            today=800,
        ),
    )
    assert m["public_debt_issues_today"] == 900
    assert m["public_debt_redemptions_today"] == 800
    assert m["total_deposits_today"] == 100
    assert m["total_withdrawals_today"] == 60


def test_before_fy2013_both_accounts_count_and_transfers_between_them_do_not() -> None:
    # Taxes landed in the Tax and Loan Note Accounts and were moved on to the
    # Federal Reserve Account; counting the move would count the taxes twice.
    m = _run(
        dw_row(DAY, FY, account_type=FRA, transaction_type="Deposits", today=70),
        dw_row(
            DAY,
            FY,
            account_type=TTL,
            transaction_type="Deposits",
            transaction_catg="FTD's Received (Table IV)",
            today=30,
        ),
        dw_row(
            DAY,
            FY,
            account_type=FRA,
            transaction_type="Deposits",
            transaction_catg="Transfers from Depositaries",
            today=25,
        ),
        dw_row(
            DAY,
            FY,
            account_type=TTL,
            transaction_type="Withdrawals",
            transaction_catg="Transfers to Federal Reserve Account (Table V)",
            today=25,
        ),
        dw_row(DAY, FY, account_type=FRA, transaction_type="Withdrawals", today=95),
    )
    assert m["total_deposits_today"] == 100
    assert m["total_withdrawals_today"] == 95


def test_withdrawals_misfiled_under_other_withdrawals_still_count() -> None:
    # The 2020-08-14 statement filed nine lines under this account_type.
    m = _run(
        dw_row(DAY, FY, account_type=FRA, transaction_type="Deposits", today=10),
        dw_row(DAY, FY, account_type=FRA, transaction_type="Withdrawals", today=40),
        dw_row(
            DAY,
            FY,
            account_type="Other Withdrawals",
            transaction_type="Withdrawals",
            transaction_catg="Military Active Duty Pay (EFT)",
            today=5,
        ),
    )
    assert m["total_withdrawals_today"] == 45


def _line_item_day(day: date, withdrawals: float, fytd: float) -> pd.DataFrame:
    return pd.concat(
        [
            dw_row(day, FY, account_type=TGA, transaction_type="Deposits", today=0),
            dw_row(
                day,
                FY,
                account_type=TGA,
                transaction_type="Withdrawals",
                today=withdrawals,
                mtd=fytd,
                fytd=fytd,
            ),
        ],
        ignore_index=True,
    )


def test_line_item_days_rebuild_mtd_and_fytd_from_the_daily_amounts() -> None:
    # The FYTD columns (1 each) are what an old statement's printed lines add
    # up to; the series ignores them and sums the days.
    frame = pd.concat(
        [
            _line_item_day(date(2026, 10, 30), 100, fytd=1),
            _line_item_day(date(2026, 11, 2), 40, fytd=1),
            _line_item_day(date(2026, 11, 3), 5, fytd=1),
        ],
        ignore_index=True,
    )
    series = net_transfer_series(frame)
    assert [m["total_withdrawals_fytd"] for m in series] == [100, 140, 145]
    assert [m["total_withdrawals_mtd"] for m in series] == [100, 40, 45]
    assert [m["net_flow_fytd"] for m in series] == [100, 140, 145]


def test_days_with_treasury_totals_keep_the_treasury_columns() -> None:
    series = net_transfer_series(
        pd.concat(
            [
                dw_day(
                    date(2026, 10, 1),
                    FY,
                    deposits=5,
                    withdrawals=8,
                    debt_issues=1,
                    debt_redemptions=2,
                ),
                dw_day(
                    date(2026, 10, 2),
                    FY,
                    deposits=5,
                    withdrawals=8,
                    debt_issues=1,
                    debt_redemptions=2,
                ),
            ],
            ignore_index=True,
        )
    )
    # dw_day's FYTD column is today × 100, not a running sum.
    assert [m["total_withdrawals_fytd"] for m in series] == [600, 600]


def test_a_fiscal_year_boundary_restarts_the_running_sums() -> None:
    frame = pd.concat(
        [
            _line_item_day(date(2026, 9, 30), 100, fytd=1),
            _line_item_day(date(2026, 10, 1), 7, fytd=1),
        ],
        ignore_index=True,
    )
    series = net_transfer_series(frame)
    assert [m["total_withdrawals_fytd"] for m in series] == [100, 7]
