"""Major categories: which Treasury line items are summed, from which table."""

from datetime import date

import pytest

from app.constants.categories import (
    IRS_REFUND_CATEGORY,
    MAJOR_RECEIPT_CATEGORIES,
    MAJOR_SPENDING_CATEGORIES,
    TBILL_INTEREST_CATEGORY,
)
from app.schemas.treasury import (
    CategoryDailyYoYRequest,
    IrsRefundRequest,
    MajorReceiptCategoriesRequest,
    MajorSpendingCategoriesRequest,
    TBillInterestRequest,
)
from app.services.categories import (
    get_daily_yoy,
    get_irs_tax_refunds,
    get_major_receipts,
    get_major_spending,
    get_tbill_interest,
)
from tests.fixtures import apd_row, catg_row, formula_db, itr_row

CUR, PREV = date(2026, 10, 19), date(2025, 10, 17)
YEARS = {"current_fiscal_year": 2027, "previous_fiscal_year": 2026}
MEDICARE = {
    "HHS - Federal Hospital Insr Trust Fund": (28951, 26849),
    "HHS - Federal Supple Med Insr Trust Fund": (42077, 38413),
    "HHS - Medicare Prescription Drugs": (10505, 6969),
}
OLD_CUSTOMS = "DHS - Customs and Certain Excise Taxes"
NEW_CUSTOMS = "DHS - Customs Duties, Taxes, and Fees"


def _withdrawal(day: date, fy: int, catg: str, fytd: float):
    return catg_row(
        day, fy, transaction_type="Withdrawals", transaction_catg=catg, fytd=fytd
    )


def _deposit(day: date, fy: int, catg: str, fytd: float):
    return catg_row(
        day, fy, transaction_type="Deposits", transaction_catg=catg, fytd=fytd
    )


def _by_name(categories) -> dict:
    return {c.name: c for c in categories}


def test_the_category_groups_match_the_methodology() -> None:
    assert {c.name: c.components for c in MAJOR_SPENDING_CATEGORIES} == {
        "Social Security Benefits": (
            "SSA - Benefits Payments",
            "SSA - Supplemental Security Income",
            "Social Security Admin (SSA) - misc",
        ),
        "Medicare": tuple(MEDICARE),
        "Medicaid": ("HHS - Grants to States for Medicaid",),
        "Interest on Treasury Securities": ("Interest on Treasury Securities",),
    }
    assert {c.name: c.components for c in MAJOR_RECEIPT_CATEGORIES} == {
        "Employment & Withholding Tax": ("Taxes - Withheld Individual/FICA",),
        # Treasury renamed the customs line in November 2025; both names are summed
        # so a fiscal year that spans the rename, and the year before it, compare.
        "Customs & Duties (Tariffs)": (OLD_CUSTOMS, NEW_CUSTOMS),
    }
    assert TBILL_INTEREST_CATEGORY.components == ("Bills (-)", "Bonds and Notes (-)")
    assert set(IRS_REFUND_CATEGORY.components) == {
        "Taxes - Individual Tax Refunds (EFT)",
        "Taxes - Individual Tax Refunds (Checks)",
        "Taxes - Business Tax Refunds (EFT)",
        "Taxes - Business Tax Refunds (Checks)",
    }


def test_spending_sums_withdrawal_line_items_only() -> None:
    rows = [
        _withdrawal(d, fy, catg, v)
        for catg, (cur, prev) in MEDICARE.items()
        for d, fy, v in ((CUR, 2027, cur), (PREV, 2026, prev))
    ]
    # Same name on the deposits side (e.g. a refund) must not be counted.
    rows.append(_deposit(CUR, 2027, "HHS - Medicare Prescription Drugs", 5000))
    conn = formula_db({"deposits_withdrawals": rows})

    result = get_major_spending(conn.cursor(), MajorSpendingCategoriesRequest(**YEARS))
    medicare = _by_name(result.categories)["Medicare"]
    assert (result.current_date, result.previous_date) == ("2026-10-19", "2025-10-17")
    assert medicare.current_fytd == 81533
    assert medicare.previous_fytd == 72231
    assert medicare.yoy_change == 9302
    assert medicare.yoy_percent_change == pytest.approx(12.878, abs=1e-3)
    assert [s.category_name for s in medicare.subcategories] == list(MEDICARE)

    medicaid = _by_name(result.categories)["Medicaid"]
    assert (medicaid.current_fytd, medicaid.yoy_percent_change) == (0, None)


def test_customs_compares_across_the_rename() -> None:
    conn = formula_db(
        {
            "deposits_withdrawals": [
                _deposit(CUR, 2027, NEW_CUSTOMS, 3870),
                _deposit(PREV, 2026, OLD_CUSTOMS, 4715),
            ]
        }
    )
    result = get_major_receipts(conn.cursor(), MajorReceiptCategoriesRequest(**YEARS))
    customs = _by_name(result.categories)["Customs & Duties (Tariffs)"]
    assert (customs.current_fytd, customs.previous_fytd) == (3870, 4715)
    assert customs.yoy_change == -845
    assert customs.yoy_percent_change == pytest.approx(-17.922, abs=1e-3)


def test_tbill_interest_is_the_two_discount_lines() -> None:
    rows = [
        apd_row(d, fy, adj_type=t, fytd=v)
        for d, fy, t, v in (
            (CUR, 2027, "Bills (-)", 17006),
            (CUR, 2027, "Bonds and Notes (-)", 3745),
            (CUR, 2027, "Bills (+)", 99999),
            (PREV, 2026, "Bills (-)", 13738),
            (PREV, 2026, "Bonds and Notes (-)", 127),
        )
    ]
    conn = formula_db({"adjustment_public_debt": rows})
    result = get_tbill_interest(conn.cursor(), TBillInterestRequest(**YEARS))
    assert result.total_current_fytd == 20751
    assert result.total_previous_fytd == 13865
    assert result.total_yoy_change == 6886
    assert result.total_yoy_percent_change == pytest.approx(49.665, abs=1e-3)
    assert [c.name for c in result.components] == [
        "Bills (-) Discount",
        "Bonds and Notes (-) Discount",
    ]


def test_irs_refunds_come_from_the_refunds_table() -> None:
    table_v = {
        "Taxes - Individual Tax Refunds (EFT)": 4394,
        "Taxes - Individual Tax Refunds (Checks)": 1788,
        "Taxes - Business Tax Refunds (EFT)": 827,
        "Taxes - Business Tax Refunds (Checks)": 3549,
    }
    conn = formula_db(
        {
            "income_tax_refunds": [
                *(
                    itr_row(CUR, 2027, tax_refund_type=k, fytd=v)
                    for k, v in table_v.items()
                ),
                itr_row(
                    PREV,
                    2026,
                    tax_refund_type="Taxes - Individual Tax Refunds (EFT)",
                    fytd=1,
                ),
            ],
            # The Deposits & Withdrawals table also lists refunds, but only the EFT
            # lines (and Puerto Rico); it must not feed this total.
            "deposits_withdrawals": [
                _withdrawal(CUR, 2027, "TREAS - IRS Refunds for Puerto Rico", 63),
                _withdrawal(CUR, 2027, "Taxes - Individual Tax Refunds (EFT)", 4394),
            ],
        }
    )
    result = get_irs_tax_refunds(conn.cursor(), IrsRefundRequest(**YEARS))
    assert result.total_current_fytd == 10558


def test_calendar_mode_card_uses_the_statement_before_a_missing_date() -> None:
    catg = "HHS - Grants to States for Medicaid"
    conn = formula_db(
        {
            "deposits_withdrawals": [
                _withdrawal(CUR, 2027, catg, 43229),
                # 2025-10-19 was a Sunday; the statement before it is 2025-10-17.
                _withdrawal(PREV, 2026, catg, 36641),
            ]
        }
    )
    result = get_major_spending(
        conn.cursor(),
        MajorSpendingCategoriesRequest(**YEARS, comparison_mode="calendar_date"),
    )
    assert result.previous_date == "2025-10-17"
    assert _by_name(result.categories)["Medicaid"].previous_fytd == 36641


def _detail(conn, mode: str):
    return get_daily_yoy(
        conn.cursor(),
        CategoryDailyYoYRequest(
            category_name="Medicare",
            category_type="spending",
            comparison_mode=mode,
            **YEARS,
        ),
    )


def _medicare_days():
    hospital = "HHS - Federal Hospital Insr Trust Fund"
    drugs = "HHS - Medicare Prescription Drugs"
    return formula_db(
        {
            "deposits_withdrawals": [
                _withdrawal(date(2026, 10, 1), 2027, hospital, 10),
                _withdrawal(date(2026, 10, 1), 2027, drugs, 5),
                _withdrawal(date(2026, 10, 5), 2027, hospital, 30),
                _withdrawal(date(2025, 10, 1), 2026, hospital, 8),
                _withdrawal(date(2025, 10, 2), 2026, hospital, 20),
            ]
        }
    )


def test_category_detail_sums_components_per_day_by_fiscal_day() -> None:
    result = _detail(_medicare_days(), "fiscal_day")
    assert [
        (p.day_of_fiscal_year, p.current_fytd, p.previous_fytd, p.previous_date)
        for p in result.data_points
    ] == [(1, 15, 8, "2025-10-01"), (2, 30, 20, "2025-10-02")]
    assert result.data_points[0].yoy_percent_change == pytest.approx(87.5)


def test_category_detail_calendar_mode_compares_a_missing_date_with_zero() -> None:
    # current behavior: unlike the daily comparison chart (which drops the date)
    # and the cards (which use the statement before), the detail chart keeps the
    # current date and treats last year's value as 0 with no percent change.
    result = _detail(_medicare_days(), "calendar_date")
    last = result.data_points[-1]
    assert (last.current_date, last.previous_date, last.previous_fytd) == (
        "2026-10-05",
        None,
        0.0,
    )
    assert last.yoy_percent_change is None
