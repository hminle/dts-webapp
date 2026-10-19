from datetime import date
from typing import Any

import pandas as pd
import pytest
import requests

from app.constants.endpoints import ENDPOINTS
from app.core.config import Settings
from app.ingest.treasury_client import TreasuryAPIError, TreasuryClient


class FakeResponse:
    def __init__(self, body: Any, status: int = 200) -> None:
        self._body, self.status_code = body, status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Server Error")

    def json(self) -> Any:
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


def _client(monkeypatch: pytest.MonkeyPatch, responses: list[FakeResponse]):
    client = TreasuryClient(
        ENDPOINTS["deposits_withdrawals"], Settings(api_throttle_time=0)
    )
    calls: list[dict[str, Any]] = []

    def fake_get(url: str, params: dict[str, Any], timeout: Any) -> FakeResponse:
        calls.append(params)
        return responses[len(calls) - 1]

    monkeypatch.setattr(client._session, "get", fake_get)
    return client, calls


def _row(day: str, amount: str) -> dict[str, str]:
    return {
        "record_date": day,
        "account_type": "Treasury General Account Total Deposits",
        "transaction_today_amt": amount,
        "record_fiscal_year": "2026",
    }


def test_concatenates_pages_and_types_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    client, calls = _client(
        monkeypatch,
        [
            FakeResponse(
                {"data": [_row("2026-10-16", "38412")], "meta": {"total-pages": 2}}
            ),
            FakeResponse(
                {"data": [_row("2026-10-15", "null")], "meta": {"total-pages": 2}}
            ),
        ],
    )

    df = client.fetch_range(date(2026, 10, 1), date(2026, 10, 16))

    assert [c["page[number]"] for c in calls] == [1, 2]
    assert calls[0]["filter"] == "record_date:gte:2026-10-01,record_date:lte:2026-10-16"
    assert len(df) == 2
    assert df["transaction_today_amt"].iloc[0] == 38412.0
    assert pd.isna(df["transaction_today_amt"].iloc[1])
    assert pd.api.types.is_datetime64_any_dtype(df["record_date"])


def test_server_error_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = _client(monkeypatch, [FakeResponse({"error": "down"}, status=500)])

    with pytest.raises(TreasuryAPIError, match="deposits_withdrawals page 1"):
        client.fetch_after(date(2026, 10, 15), date(2026, 10, 16))


def test_failure_on_a_later_page_raises_instead_of_returning_partial_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = _client(
        monkeypatch,
        [
            FakeResponse(
                {"data": [_row("2026-10-16", "1")], "meta": {"total-pages": 2}}
            ),
            FakeResponse(ValueError("bad json")),
        ],
    )

    with pytest.raises(TreasuryAPIError, match="page 2"):
        client.fetch_range(date(2026, 10, 1), date(2026, 10, 16))


def test_body_without_data_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = _client(monkeypatch, [FakeResponse({"meta": {}})])

    with pytest.raises(TreasuryAPIError, match="no 'data' key"):
        client.fetch_range(date(2026, 10, 1), date(2026, 10, 16))


def test_zero_rows_is_an_empty_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = _client(
        monkeypatch, [FakeResponse({"data": [], "meta": {"total-pages": 0}})]
    )

    assert client.fetch_after(date(2026, 10, 16), date(2026, 10, 18)).empty
