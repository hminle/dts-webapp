from fastapi.testclient import TestClient


def _page(client: TestClient, page: int, **params: object) -> dict:
    response = client.get(
        "/api/v1/data", params={"page": page, "page_size": 7, **params}
    )
    assert response.status_code == 200
    return response.json()


def test_pages_cover_every_row_exactly_once(client: TestClient) -> None:
    first = _page(client, 1)
    rows = list(first["items"])
    for page in range(2, first["pages"] + 1):
        body = _page(client, page)
        assert body["total"] == first["total"]
        assert body["items"][0]["record_date"] <= rows[-1]["record_date"]
        rows.extend(body["items"])

    keys = [(r["data_source"], r["id"]) for r in rows]
    assert len(rows) == first["total"]
    assert len(set(keys)) == len(keys)


def test_data_source_filter(client: TestClient) -> None:
    body = _page(client, 1, data_source="deposits_withdrawals", fiscal_year=2026)

    assert body["total"] == 12
    assert {r["data_source"] for r in body["items"]} == {"deposits_withdrawals"}


def test_account_type_filter_only_narrows_tables_that_have_the_column(
    client: TestClient,
) -> None:
    narrowed = _page(
        client,
        1,
        data_source="deposits_withdrawals",
        account_type="Treasury General Account Total Deposits",
    )
    unaffected = _page(
        client,
        1,
        data_source="income_tax_refunds",
        account_type="Treasury General Account Total Deposits",
    )

    assert narrowed["total"] == 6
    assert unaffected["total"] == 6


def test_date_with_no_rows_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/data/date/1999-01-01")

    assert response.status_code == 404


def test_rows_for_a_date_follow_table_order(client: TestClient) -> None:
    rows = client.get("/api/v1/data/date/2025-10-10").json()

    assert rows[0]["data_source"] == "operating_cash_balance"
    assert {r["data_source"] for r in rows} >= {"deposits_withdrawals"}


def test_unknown_data_source_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/data", params={"data_source": "nonsense"})

    assert response.status_code == 400
