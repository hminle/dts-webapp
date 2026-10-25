"""Rolling averages: the mean of the last N statements, not N calendar days."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.schemas.treasury import RollingAverageRequest
from app.services.rolling import get_daily
from tests.fixtures import dnt_row, dw_row, formula_db

# The 10 statements ending 2025-12-04: weekends and Thanksgiving are skipped.
DATES = [
    date(2025, 11, 20),
    date(2025, 11, 21),
    date(2025, 11, 24),
    date(2025, 11, 25),
    date(2025, 11, 26),
    date(2025, 11, 28),
    date(2025, 12, 1),
    date(2025, 12, 2),
    date(2025, 12, 3),
    date(2025, 12, 4),
]
WITHDRAWALS = [19815, 31192, 16793, 19998, 54507, 13595, 125763, 13764, 44733, 15928]
UNEMPLOYMENT = [78, 63, 193, 241, 353, 56, 212, 269, 164, 107]


def _withdrawals_db():
    return formula_db(
        {
            "daily_net_transfers": [
                dnt_row(
                    d,
                    2026,
                    35 + i,
                    withdrawals_fytd=0,
                    deposits_fytd=0,
                    withdrawals_today=v,
                )
                for i, (d, v) in enumerate(zip(DATES, WITHDRAWALS, strict=True))
            ]
        }
    )


def _request(**kw) -> RollingAverageRequest:
    return RollingAverageRequest(
        start_date=DATES[0], end_date=DATES[-1], **{"metric": "total_withdrawals", **kw}
    )


def test_average_counts_statements_not_days() -> None:
    result = get_daily(_withdrawals_db().cursor(), _request())
    last = result.points[-1]
    assert last.record_date == "2025-12-04"
    assert last.value == 15928
    assert last.rolling_average == pytest.approx(35608.8)
    assert last.projected_monthly == pytest.approx(712176.0)
    assert result.monthly_multiplier == 20


def test_average_is_null_until_the_window_is_full() -> None:
    points = get_daily(_withdrawals_db().cursor(), _request()).points
    assert [p.rolling_average for p in points[:9]] == [None] * 9
    assert [p.projected_monthly for p in points[:9]] == [None] * 9


def test_start_date_after_end_date_is_rejected() -> None:
    with pytest.raises(ValueError, match="on or before end_date"):
        get_daily(
            _withdrawals_db().cursor(),
            RollingAverageRequest(
                metric="total_withdrawals", start_date=DATES[-1], end_date=DATES[0]
            ),
        )


def test_unemployment_sums_its_lines_and_has_no_projection() -> None:
    conn = formula_db(
        {
            "deposits_withdrawals": [
                dw_row(
                    d,
                    2026,
                    account_type="Treasury General Account (TGA)",
                    transaction_type="Withdrawals",
                    transaction_catg="DOL - Unemployment Benefits",
                    today=v,
                )
                for d, v in zip(DATES, UNEMPLOYMENT, strict=True)
            ]
        }
    )
    result = get_daily(conn.cursor(), _request(metric="unemployment_benefits"))
    assert result.points[-1].rolling_average == pytest.approx(173.6)
    assert result.points[-1].projected_monthly is None
    assert result.monthly_multiplier is None


@pytest.mark.parametrize("window", [1, 61])
def test_window_bounds_are_422(client: TestClient, window: int) -> None:
    response = client.get(
        "/api/v1/rolling/daily",
        params={"metric": "total_withdrawals", "window": window},
    )
    assert response.status_code == 422
