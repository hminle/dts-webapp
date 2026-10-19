from fastapi.testclient import TestClient


def test_fiscal_year_days_are_numbered_in_order(client: TestClient) -> None:
    rows = client.get("/api/v1/net-transfers/fiscal-year/2026").json()

    assert [r["day_of_fiscal_year"] for r in rows] == [1, 2, 3]
    assert [r["record_date"] for r in rows] == [
        "2025-10-01",
        "2025-10-03",
        "2025-10-10",
    ]


def test_one_date(client: TestClient) -> None:
    body = client.get("/api/v1/net-transfers/date/2025-10-03").json()

    # (withdrawals - redemptions) - (deposits - issues), from the seed amounts.
    assert body["net_flow_today"] == (41100 - 19000) - (38100 + 2026 - 22000)


def test_missing_date_explains_itself(client: TestClient) -> None:
    response = client.get("/api/v1/net-transfers/date/2025-10-04")

    assert response.status_code == 404
    assert "not available" in response.json()["detail"]
    assert "population task" not in response.json()["detail"]
