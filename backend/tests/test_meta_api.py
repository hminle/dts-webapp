from fastapi.testclient import TestClient

from tests.conftest import BUILD_DATE, seeded_row_count


def test_stats_cover_the_seeded_artifact(client: TestClient) -> None:
    body = client.get("/api/v1/meta/stats").json()

    assert body["record_count"] == seeded_row_count()
    assert body["earliest_date"] == "2024-10-01"
    assert body["latest_date"] == "2025-10-10"
    assert body["last_updated"] == BUILD_DATE
    assert body["fiscal_years"] == [2026, 2025]


def test_record_counts_by_year_are_newest_first(client: TestClient) -> None:
    body = client.get("/api/v1/meta/record-counts-by-year").json()

    assert list(body) == ["2026", "2025"]
    assert sum(body.values()) == seeded_row_count()


def test_build_info(client: TestClient) -> None:
    body = client.get("/api/v1/meta/build").json()

    assert body["build_date"] == BUILD_DATE
    assert body["latest_record_date"] == "2025-10-10"
    assert set(body) == {"build_date", "latest_record_date", "source", "schema_version"}
