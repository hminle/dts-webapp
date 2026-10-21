"""Day of fiscal year: how statement dates are numbered within a fiscal year."""

from datetime import date

import pandas as pd

from app.ingest.populate import compute_daily_records
from app.schemas.treasury import YoYCategoryComparisonRequest
from app.services.yoy import get_category_comparison
from app.utils.yoy import FYTDSource, date_for_fiscal_day, fiscal_day_for_date
from tests.fixtures import catg_row, dw_day, dw_day_without_totals, formula_db

FY = 2027
D1, D2, D3 = date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 5)
SOURCE = FYTDSource(
    table="deposits_withdrawals",
    fytd_column="transaction_fytd_amt",
    key_column="transaction_catg",
)


def _day(d: date) -> pd.DataFrame:
    return dw_day(d, FY, deposits=10, withdrawals=20, debt_issues=0, debt_redemptions=0)


def test_a_day_without_totals_keeps_its_number_but_gets_no_row() -> None:
    fy_df = pd.concat([_day(D1), dw_day_without_totals(D2, FY), _day(D3)])
    records = compute_daily_records(fy_df, FY)
    assert [(r["record_date"], r["day_of_fiscal_year"]) for r in records] == [
        ("2026-10-01", 1),
        ("2026-10-05", 3),
    ]


def test_category_days_are_ranked_among_dates_the_category_appears() -> None:
    # current behavior: DENSE_RANK runs over the selected categories' rows, so
    # a date on which the line item is absent is not counted (D2 here), unlike
    # daily_net_transfers, which counts every statement date.
    catg = "HHS - Grants to States for Medicaid"
    rows = [
        catg_row(d, FY, transaction_type="Withdrawals", transaction_catg=catg, fytd=v)
        for d, v in ((D1, 1.0), (D3, 3.0))
    ]
    conn = formula_db({"deposits_withdrawals": [*rows, _day(D2)]})
    result = get_category_comparison(
        conn.cursor(),
        YoYCategoryComparisonRequest(
            current_fiscal_year=FY,
            previous_fiscal_year=FY - 1,
            category_descriptions=[catg],
        ),
    )
    points = result.current_year_data[0].data_points
    assert [(p.record_date, p.day_of_fiscal_year) for p in points] == [
        ("2026-10-01", 1),
        ("2026-10-05", 2),
    ]


def test_fiscal_day_lookups_are_inverses() -> None:
    conn = formula_db({"deposits_withdrawals": [_day(D1), _day(D2), _day(D3)]})
    assert fiscal_day_for_date(conn, SOURCE, FY, "2026-10-05") == 3
    # A non-statement date counts the statements up to it.
    assert fiscal_day_for_date(conn, SOURCE, FY, "2026-10-04") == 2
    assert fiscal_day_for_date(conn, SOURCE, FY + 1, "2027-10-05") == 0
    assert date_for_fiscal_day(conn, SOURCE, FY, 3) == "2026-10-05"
    assert date_for_fiscal_day(conn, SOURCE, FY, 4) is None
