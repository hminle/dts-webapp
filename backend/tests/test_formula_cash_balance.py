"""TGA closing balance: one series across the three rows it has lived on."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.schemas.treasury import CashBalanceRequest
from app.services.cash_balance import get_daily
from tests.fixtures import formula_db, ocb_row

CLOSING = "Treasury General Account (TGA) Closing Balance"


def _range(start: date, end: date) -> CashBalanceRequest:
    return CashBalanceRequest(start_date=start, end_date=end)


def test_each_era_reads_its_own_column() -> None:
    conn = formula_db(
        {
            "operating_cash_balance": [
                ocb_row(
                    date(2021, 9, 30),
                    2021,
                    account_type="Federal Reserve Account",
                    open_today=1,
                    close_today=215160,
                ),
                ocb_row(
                    date(2022, 4, 15),
                    2022,
                    account_type="Treasury General Account (TGA)",
                    open_today=1,
                    close_today=578473,
                ),
                # Since 2022-04-18 the closing row carries the amount as "open".
                ocb_row(
                    date(2026, 8, 27), 2026, account_type=CLOSING, open_today=950804
                ),
            ]
        }
    )
    result = get_daily(conn.cursor(), _range(date(2021, 1, 1), date(2026, 12, 31)))
    assert [p.closing_balance for p in result.points] == [215160, 578473, 950804]


def test_other_rows_are_ignored() -> None:
    day = date(2026, 8, 27)
    conn = formula_db(
        {
            "operating_cash_balance": [
                ocb_row(day, 2026, account_type=CLOSING, open_today=950804),
                ocb_row(
                    day,
                    2026,
                    account_type="Treasury General Account (TGA) Opening Balance",
                    open_today=1,
                ),
                ocb_row(
                    day,
                    2026,
                    account_type="Short-Term Cash Investments (Table V)",
                    open_today=2,
                    close_today=2,
                ),
            ]
        }
    )
    result = get_daily(conn.cursor(), _range(day, day))
    assert [(p.record_date, p.closing_balance) for p in result.points] == [
        ("2026-08-27", 950804)
    ]


def test_a_null_balance_raises() -> None:
    day = date(2026, 8, 27)
    conn = formula_db(
        {"operating_cash_balance": [ocb_row(day, 2026, account_type=CLOSING)]}
    )
    with pytest.raises(RuntimeError, match="No TGA closing balance on 2026-08-27"):
        get_daily(conn.cursor(), _range(day, day))


def test_default_range_is_a_year() -> None:
    conn = formula_db(
        {
            "operating_cash_balance": [
                ocb_row(d, 2026, account_type=CLOSING, open_today=v)
                for d, v in (
                    (date(2025, 8, 26), 1),
                    (date(2025, 8, 27), 2),
                    (date(2026, 8, 27), 3),
                )
            ]
        }
    )
    result = get_daily(conn.cursor(), CashBalanceRequest())
    assert (result.start_date, result.end_date) == ("2025-08-27", "2026-08-27")
    assert [p.closing_balance for p in result.points] == [2, 3]


def test_start_after_end_is_400(client: TestClient) -> None:
    response = client.get(
        "/api/v1/cash-balance/daily",
        params={"start_date": "2025-10-10", "end_date": "2025-10-01"},
    )
    assert response.status_code == 400
