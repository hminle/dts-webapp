from fastapi.testclient import TestClient


def test_fiscal_years_newest_first(client: TestClient) -> None:
    assert client.get("/api/v1/lookups/fiscal-years").json() == [2026, 2025]


def test_data_sources_include_the_derived_table(client: TestClient) -> None:
    sources = client.get("/api/v1/lookups/data-sources").json()

    assert len(sources) == 10
    assert "daily_net_transfers" in sources


def test_account_types_for_a_table_without_the_column_is_empty(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/lookups/account-types", params={"data_source": "income_tax_refunds"}
    )

    assert response.json() == []


def test_unknown_data_source_is_rejected(client: TestClient) -> None:
    response = client.get(
        "/api/v1/lookups/account-types", params={"data_source": "nonsense"}
    )

    assert response.status_code == 400
    assert "nonsense" in response.json()["detail"]


def test_categories_by_transaction_type(client: TestClient) -> None:
    body = client.get("/api/v1/lookups/categories").json()

    assert body["deposits"] == ["Public Debt Cash Issues (Table IIIB)"]
    assert body["withdrawals"] == ["Public Debt Cash Redemp. (Table IIIB)"]
