"""Combined figures: signed sums of registry categories."""

from datetime import date

import pytest

from app.constants.categories import COMBINED_CATEGORIES
from app.schemas.treasury import MajorSpendingCategoriesRequest
from app.services.categories import get_combined
from tests.fixtures import apd_row, catg_row, formula_db

CUR, PREV = date(2025, 12, 4), date(2024, 12, 4)
YEARS = {"current_fiscal_year": 2026, "previous_fiscal_year": 2025}


def _line(day: date, fy: int, side: str, catg: str, fytd: float):
    return catg_row(day, fy, transaction_type=side, transaction_catg=catg, fytd=fytd)


def _by_name(result) -> dict:
    return {c.name: c for c in result.categories}


def _interest_rows(previous_day: date = PREV, previous_fy: int = 2025):
    interest = "Interest on Treasury Securities"
    return {
        "deposits_withdrawals": [
            _line(CUR, 2026, "Withdrawals", interest, 141720),
            _line(previous_day, previous_fy, "Withdrawals", interest, 120038),
        ],
        "adjustment_public_debt": [
            apd_row(CUR, 2026, adj_type="Bills (-)", fytd=49128),
            apd_row(CUR, 2026, adj_type="Bonds and Notes (-)", fytd=1749),
            apd_row(previous_day, previous_fy, adj_type="Bills (-)", fytd=53521),
            apd_row(
                previous_day, previous_fy, adj_type="Bonds and Notes (-)", fytd=4122
            ),
        ],
    }


def test_interest_income_adds_tbill_interest() -> None:
    conn = formula_db(_interest_rows())
    result = get_combined(conn.cursor(), MajorSpendingCategoriesRequest(**YEARS))
    income = _by_name(result)["Interest Income Transfers"]
    assert (income.current_fytd, income.previous_fytd) == (192597, 177681)
    assert income.yoy_change == 14916
    assert income.yoy_percent_change == pytest.approx(8.395, abs=1e-3)
    assert [(t.category_name, t.sign, t.current_fytd) for t in income.terms] == [
        ("Interest on Treasury Securities", 1, 141720),
        ("T-Bill Interest", 1, 50877),
    ]


def test_net_customs_subtracts_cbp_payments() -> None:
    cbp = "DHS - Customs & Border Protection (CBP)"
    conn = formula_db(
        {
            "deposits_withdrawals": [
                _line(
                    CUR,
                    2026,
                    "Deposits",
                    "DHS - Customs Duties, Taxes, and Fees",
                    68584,
                ),
                _line(CUR, 2026, "Withdrawals", cbp, 3180),
                _line(
                    PREV,
                    2025,
                    "Deposits",
                    "DHS - Customs and Certain Excise Taxes",
                    17730,
                ),
                _line(PREV, 2025, "Withdrawals", cbp, 1807),
            ]
        }
    )
    result = get_combined(conn.cursor(), MajorSpendingCategoriesRequest(**YEARS))
    customs = _by_name(result)["Net Customs Receipts"]
    assert (customs.current_fytd, customs.previous_fytd) == (65404, 15923)
    assert customs.yoy_change == 49481
    assert customs.yoy_percent_change == pytest.approx(310.752, abs=1e-3)


def test_combined_is_null_before_its_latest_term() -> None:
    # Interest on Treasury Securities goes back to 2005, but T-bill interest has
    # its own lines only from 2022-09-12.
    conn = formula_db(_interest_rows(previous_day=date(2022, 9, 9), previous_fy=2022))
    result = get_combined(
        conn.cursor(),
        MajorSpendingCategoriesRequest(
            current_fiscal_year=2026, previous_fiscal_year=2022
        ),
    )
    income = _by_name(result)["Interest Income Transfers"]
    assert income.current_fytd == 192597
    assert income.previous_fytd is None
    assert income.yoy_change is None
    assert income.terms[0].previous_fytd == 120038
    assert income.terms[1].previous_fytd is None


def test_combined_available_from() -> None:
    assert {c.name: c.available_from.isoformat() for c in COMBINED_CATEGORIES} == {
        "Interest Income Transfers": "2022-09-12",
        "Net Customs Receipts": "2020-05-11",
    }
