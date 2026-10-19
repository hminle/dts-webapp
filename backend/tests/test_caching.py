from fastapi.testclient import TestClient

from app.api.caching import DATA_CACHE_CONTROL
from app.main import app


def test_data_routes_are_publicly_cacheable(client: TestClient) -> None:
    response = client.get("/api/v1/lookups/fiscal-years")

    assert response.headers["cache-control"] == DATA_CACHE_CONTROL
    assert "set-cookie" not in response.headers


def test_every_data_route_is_get_only() -> None:
    # A CDN never caches POST; keep the whole data API on GET.
    for path, operations in app.openapi()["paths"].items():
        if path.startswith("/api/v1/"):
            assert set(operations) == {"get"}, path


def test_missing_artifact_is_503_for_data(empty_client: TestClient) -> None:
    response = empty_client.get("/api/v1/meta/stats")

    assert response.status_code == 503
    assert response.json() == {"detail": "Data is not loaded yet"}
