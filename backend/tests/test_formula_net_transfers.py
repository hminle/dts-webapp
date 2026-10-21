"""Net transfers: total deposits, total withdrawals and their difference.

Exercises ``calculate_daily_net_transfers`` directly, including each fallback it
takes when a statement lacks the pre-aggregated total rows.
"""

from datetime import date

import pandas as pd
import pytest

from app.utils.deposits_withdrawals import calculate_daily_net_transfers
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
