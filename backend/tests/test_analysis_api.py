import pytest
from fastapi.testclient import TestClient

YEARS = {"current_fiscal_year": 2026, "previous_fiscal_year": 2025}


@pytest.mark.parametrize(
    ("path", "params"),
    [
        (
            "/api/v1/weekly/comparison",
            {"first_fiscal_year": 2026, "second_fiscal_year": 2025},
        ),
        (
            "/api/v1/yoy/category-comparison",
            {
                **YEARS,
                "category_descriptions": [
                    "Public Debt Cash Issues (Table IIIB)",
                    "Public Debt Cash Redemp. (Table IIIB)",
                ],
            },
        ),
        ("/api/v1/yoy/daily-comparison", {**YEARS, "metric": "net_flow"}),
        ("/api/v1/categories/major-spending", YEARS),
        ("/api/v1/categories/major-receipts", YEARS),
        ("/api/v1/categories/other-spending", YEARS),
        ("/api/v1/categories/other-receipts", YEARS),
        ("/api/v1/categories/combined", YEARS),
        ("/api/v1/rolling/daily", {"metric": "total_withdrawals", "window": 2}),
        ("/api/v1/categories/tbill-interest", YEARS),
        ("/api/v1/categories/irs-tax-refunds", YEARS),
        (
            "/api/v1/categories/daily-yoy",
            {**YEARS, "category_name": "Medicare", "category_type": "spending"},
        ),
    ],
)
def test_analysis_routes_answer(client: TestClient, path: str, params: dict) -> None:
    response = client.get(path, params=params)

    assert response.status_code == 200, response.text


def test_category_comparison_reads_repeated_keys(client: TestClient) -> None:
    body = client.get(
        "/api/v1/yoy/category-comparison",
        params={
            **YEARS,
            "category_descriptions": [
                "Public Debt Cash Issues (Table IIIB)",
                "Public Debt Cash Redemp. (Table IIIB)",
            ],
        },
    ).json()

    assert len(body["current_year_data"]) == 2
    assert body["comparison_days"] == 3


def test_weekly_pairs_fridays(client: TestClient) -> None:
    body = client.get(
        "/api/v1/weekly/comparison",
        params={"first_fiscal_year": 2026, "second_fiscal_year": 2025},
    ).json()

    assert [p["record_date"] for p in body["first_year_data"]] == [
        "2025-10-03",
        "2025-10-10",
    ]


@pytest.mark.parametrize(
    ("path", "params"),
    [
        (
            "/api/v1/yoy/daily-comparison",
            {**YEARS, "metric": "net_flow", "comparison_mode": "bogus"},
        ),
        (
            "/api/v1/weekly/comparison",
            {"first_fiscal_year": 2026, "second_fiscal_year": 2026},
        ),
    ],
)
def test_bad_inputs_are_400(client: TestClient, path: str, params: dict) -> None:
    response = client.get(path, params=params)

    assert response.status_code == 400
    assert response.json()["detail"]


def test_cash_balance_without_rows_is_404(client: TestClient) -> None:
    # The seed's operating_cash_balance rows have no account_type, so none is a
    # balance row.
    assert client.get("/api/v1/cash-balance/daily").status_code == 404
