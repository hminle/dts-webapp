import hashlib
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from app.constants.endpoints import ENDPOINT_TABLES, EndpointDef
from app.core.config import Settings
from app.ingest.build import MissingArtifact, build
from app.ingest.treasury_client import TreasuryAPIError
from app.ingest.validate import ArtifactInvalid
from tests.fixtures import dw_day, endpoint_row

FY = 2027
DAYS = [date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 5)]
NEXT_DAY = date(2026, 10, 6)


def _universe(days: list[date]) -> dict[str, pd.DataFrame]:
    """What the fake Treasury API holds: rows for every table on every day."""
    frames: dict[str, pd.DataFrame] = {}
    for table in ENDPOINT_TABLES:
        if table == "deposits_withdrawals":
            parts = [
                dw_day(
                    d,
                    FY,
                    deposits=100 + i,
                    withdrawals=150 + i,
                    debt_issues=40,
                    debt_redemptions=30,
                )
                for i, d in enumerate(days)
            ]
        else:
            parts = [endpoint_row(d, FY) for d in days]
        frames[table] = pd.concat(parts, ignore_index=True)
    return frames


class FakeTreasury:
    def __init__(self, data: dict[str, pd.DataFrame], fail_on: str | None = None):
        self.data, self.fail_on = data, fail_on

    def factory(self, endpoint: EndpointDef) -> "FakeTreasury.Client":
        return FakeTreasury.Client(self, endpoint.key)

    class Client:
        def __init__(self, api: "FakeTreasury", key: str) -> None:
            self.api, self.key = api, key

        def _rows(self, keep) -> pd.DataFrame:
            if self.key == self.api.fail_on:
                raise TreasuryAPIError(f"{self.key} page 1: 503")
            df = self.api.data[self.key]
            return df[df["record_date"].map(keep)].reset_index(drop=True)

        def fetch_range(self, start: date, end: date) -> pd.DataFrame:
            return self._rows(lambda d: start <= d <= end)

        def fetch_after(self, latest: date, today: date) -> pd.DataFrame:
            return self._rows(lambda d: latest < d <= today)


def _build(path: Path, api: FakeTreasury, *, full: bool, today: date = DAYS[-1]):
    return build(
        path, full=full, today=today, settings=Settings(), client_factory=api.factory
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def artifact(tmp_path: Path) -> Path:
    path = tmp_path / "treasury_data.duckdb"
    _build(path, FakeTreasury(_universe(DAYS)), full=True)
    return path


def test_full_build_creates_a_complete_artifact(artifact: Path) -> None:
    conn = duckdb.connect(str(artifact), read_only=True)
    for table in ENDPOINT_TABLES:
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] > 0
    days = conn.execute(
        "SELECT day_of_fiscal_year FROM daily_net_transfers ORDER BY record_date"
    ).fetchall()
    meta = dict(conn.execute("SELECT key, value FROM metadata").fetchall())
    conn.close()

    assert [d[0] for d in days] == [1, 2, 3]
    assert meta["latest_record_date"] == "2026-10-05"
    assert {"build_date", "source", "schema_version"} <= meta.keys()
    leftovers = [p.name for p in artifact.parent.iterdir() if p != artifact]
    assert leftovers == []


def test_incremental_build_adds_only_new_days(artifact: Path) -> None:
    api = FakeTreasury(_universe([*DAYS, NEXT_DAY]))

    result = _build(artifact, api, full=False, today=NEXT_DAY)

    assert result.changed is True
    assert result.records_added["deposits_withdrawals"] == 4
    assert result.records_added["operating_cash_balance"] == 1
    assert result.fiscal_years_populated == [FY]
    assert result.latest_record_date == "2026-10-06"
    conn = duckdb.connect(str(artifact), read_only=True)
    (count,) = conn.execute("SELECT COUNT(*) FROM daily_net_transfers").fetchone()
    conn.close()
    assert count == 4


def test_no_new_data_leaves_the_file_untouched(artifact: Path) -> None:
    before = _sha(artifact)

    result = _build(artifact, FakeTreasury(_universe(DAYS)), full=False)

    assert result.changed is False
    assert _sha(artifact) == before


def test_a_failed_fetch_leaves_the_file_untouched(artifact: Path) -> None:
    before = _sha(artifact)
    api = FakeTreasury(_universe([*DAYS, NEXT_DAY]), fail_on="debt_subject_to_limit")

    with pytest.raises(TreasuryAPIError):
        _build(artifact, api, full=False, today=NEXT_DAY)

    assert _sha(artifact) == before
    assert not artifact.with_suffix(".building.duckdb").exists()


def test_a_full_rebuild_that_shrinks_is_rejected(artifact: Path) -> None:
    before = _sha(artifact)

    with pytest.raises(ArtifactInvalid, match="shrank"):
        _build(artifact, FakeTreasury(_universe(DAYS[:2])), full=True)

    assert _sha(artifact) == before


def test_incremental_without_an_artifact_is_refused(tmp_path: Path) -> None:
    with pytest.raises(MissingArtifact):
        _build(tmp_path / "none.duckdb", FakeTreasury(_universe(DAYS)), full=False)
