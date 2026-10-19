from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _fresh_settings() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_health_reports_ok(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["data_loaded"], bool)


def test_health_without_artifact(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("APP_DUCKDB_PATH", str(tmp_path / "missing.duckdb"))

    response = client.get("/api/health")

    assert response.json() == {"status": "ok", "data_loaded": False}


def test_health_with_artifact(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    artifact = tmp_path / "present.duckdb"
    artifact.touch()
    monkeypatch.setenv("APP_DUCKDB_PATH", str(artifact))

    assert client.get("/api/health").json()["data_loaded"] is True
