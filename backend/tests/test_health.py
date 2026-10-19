from fastapi.testclient import TestClient


def test_health_reports_the_data_date(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "data_loaded": True,
        "latest_record_date": "2025-10-10",
    }


def test_health_without_artifact(empty_client: TestClient) -> None:
    response = empty_client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["data_loaded"] is False


def test_health_is_not_cached(client: TestClient) -> None:
    assert "s-maxage" not in client.get("/api/health").headers.get("cache-control", "")
