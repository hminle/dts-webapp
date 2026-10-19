"""Fixtures: a small artifact built by the real schema/insert/populate code.

Settings and the cached DuckDB connection are module-level singletons, so every
client fixture points ``APP_DUCKDB_PATH`` at its file and resets both.
"""

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.constants.endpoints import ENDPOINT_TABLES
from app.core.config import get_settings
from app.core.duckdb import reset_connection_for_tests
from app.core.schema import SCHEMA_VERSION, create_schema
from app.ingest.insert import insert_frame
from app.ingest.populate import populate_fiscal_years
from app.main import app
from tests.fixtures import dw_day, endpoint_row

# Two business days a week apart in each FY, plus the first day of the FY, so the
# weekly comparison has two Fridays to pair.
SEED_DAYS: dict[int, list[date]] = {
    2025: [date(2024, 10, 1), date(2024, 10, 4), date(2024, 10, 11)],
    2026: [date(2025, 10, 1), date(2025, 10, 3), date(2025, 10, 10)],
}
BUILD_DATE = "2026-10-16T22:41:00+00:00"


def _seed(path: Path) -> None:
    conn = duckdb.connect(str(path))
    create_schema(conn)
    for fy, days in SEED_DAYS.items():
        for i, day in enumerate(days):
            insert_frame(
                conn,
                dw_day(
                    day,
                    fy,
                    deposits=38000 + 100 * i + fy,
                    withdrawals=41000 + 100 * i,
                    debt_issues=22000,
                    debt_redemptions=19000,
                ),
                "deposits_withdrawals",
            )
            for table in ENDPOINT_TABLES:
                if table != "deposits_withdrawals":
                    insert_frame(conn, endpoint_row(day, fy), table)
    populate_fiscal_years(conn, SEED_DAYS)
    for key, value in {
        "build_date": BUILD_DATE,
        "latest_record_date": "2025-10-10",
        "source": "https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/",
        "schema_version": SCHEMA_VERSION,
    }.items():
        conn.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", [key, value])
    conn.execute("CHECKPOINT")
    conn.close()


@pytest.fixture(scope="session")
def seeded_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("artifact") / "treasury_data.duckdb"
    _seed(path)
    return path


def seeded_row_count() -> int:
    """Endpoint-table rows the seed inserts (dw has 4 rows per day)."""
    days = sum(len(d) for d in SEED_DAYS.values())
    return days * 4 + days * (len(ENDPOINT_TABLES) - 1)


def _client_for(path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("APP_DUCKDB_PATH", str(path))
    get_settings.cache_clear()
    reset_connection_for_tests()
    with TestClient(app) as client:
        yield client
    reset_connection_for_tests()
    get_settings.cache_clear()


@pytest.fixture
def client(seeded_db: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    yield from _client_for(seeded_db, monkeypatch)


@pytest.fixture
def empty_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    yield from _client_for(tmp_path / "missing.duckdb", monkeypatch)
