from datetime import date

import pandas as pd

from app.ingest.populate import compute_daily_records
from tests.fixtures import dw_day, dw_day_without_totals


def _day(n: int) -> pd.DataFrame:
    return dw_day(
        date(2026, 10, n),
        2027,
        deposits=38412,
        withdrawals=41276,
        debt_issues=22905,
        debt_redemptions=19880,
    )


def test_numbers_every_date_and_applies_the_net_flow_formula() -> None:
    records = compute_daily_records(pd.concat([_day(1), _day(2), _day(5)]), 2027)

    assert [r["day_of_fiscal_year"] for r in records] == [1, 2, 3]
    first = records[0]
    assert first["total_deposits_today"] == 38412 - 22905
    assert first["total_withdrawals_today"] == 41276 - 19880
    # net flow = (withdrawals - redemptions) - (deposits - issues) = 5,889
    assert first["net_flow_today"] == 5889
    assert first["net_flow_fytd"] == 588900
    assert first["leading_flow"] == first["total_withdrawals_today"]


def test_a_skipped_date_keeps_its_day_number() -> None:
    frames = [_day(1), dw_day_without_totals(date(2026, 10, 2), 2027), _day(5)]

    records = compute_daily_records(pd.concat(frames), 2027)

    assert [r["record_date"] for r in records] == ["2026-10-01", "2026-10-05"]
    assert [r["day_of_fiscal_year"] for r in records] == [1, 3]


def test_empty_frame_gives_no_rows() -> None:
    assert compute_daily_records(pd.DataFrame(), 2027) == []
