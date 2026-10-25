"""The weekly snapshot route against the seeded artifact."""

from fastapi.testclient import TestClient


def test_snapshot_route_answers(client: TestClient) -> None:
    response = client.get(
        "/api/v1/snapshot/weekly", params={"anchor_weekday": "friday"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["record_date"] == "2025-10-10"
    assert body["day_of_fiscal_year"] == 3


def test_snapshot_thursday_has_no_statement_in_the_seed(client: TestClient) -> None:
    # The seed's latest statement is Friday 2025-10-10. Its Thursday (Oct 9) and
    # the 5 days before it have no statement, so there is no week to show.
    response = client.get(
        "/api/v1/snapshot/weekly", params={"anchor_weekday": "thursday"}
    )
    assert response.status_code == 404


def test_bad_anchor_is_422(client: TestClient) -> None:
    response = client.get(
        "/api/v1/snapshot/weekly", params={"anchor_weekday": "monday"}
    )
    assert response.status_code == 422
