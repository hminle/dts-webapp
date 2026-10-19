"""Build the Treasury artifact: fetch, populate, validate, then swap into place."""

import logging
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Protocol

import duckdb
import pandas as pd

from app.constants.endpoints import ENDPOINTS, EndpointDef
from app.core.config import Settings
from app.core.schema import SCHEMA_VERSION, create_schema
from app.ingest.insert import insert_frame
from app.ingest.populate import populate_fiscal_years
from app.ingest.validate import Snapshot, snapshot, validate
from app.utils.fiscal import current_fiscal_year

logger = logging.getLogger(__name__)

HISTORY_START = date(2005, 1, 1)
SOURCE = "https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/"


class EndpointFetcher(Protocol):
    def fetch_range(self, start: date, end: date) -> pd.DataFrame: ...

    def fetch_after(self, latest: date, today: date) -> pd.DataFrame: ...


ClientFactory = Callable[[EndpointDef], EndpointFetcher]


class MissingArtifact(RuntimeError):
    """An incremental build was asked for but there is no artifact to extend."""


@dataclass
class BuildResult:
    changed: bool
    records_added: dict[str, int] = field(default_factory=dict)
    fiscal_years_populated: list[int] = field(default_factory=list)
    latest_record_date: str | None = None


def _default_factory(settings: Settings) -> ClientFactory:
    # Imported here so the serving app never imports requests (it is only in the
    # ingest dependency group).
    from app.ingest.treasury_client import TreasuryClient

    return lambda endpoint: TreasuryClient(endpoint, settings)


def _read_snapshot(path: Path) -> Snapshot:
    conn = duckdb.connect(str(path), read_only=True)
    try:
        return snapshot(conn)
    finally:
        conn.close()


def build(
    db_path: Path,
    *,
    full: bool,
    today: date,
    settings: Settings,
    client_factory: ClientFactory | None = None,
) -> BuildResult:
    """Update or rebuild the artifact at ``db_path``.

    The work happens in ``<name>.building.duckdb``; ``db_path`` is replaced only
    after validation passes, so any failure leaves the published file untouched.

    Raises:
        MissingArtifact: Incremental build without an existing artifact.
        TreasuryAPIError: A fetch failed.
        ArtifactInvalid: The result failed validation.
    """
    factory = client_factory or _default_factory(settings)
    tmp = db_path.with_suffix(".building.duckdb")
    wal = Path(f"{tmp}.wal")
    tmp.unlink(missing_ok=True)
    wal.unlink(missing_ok=True)

    previous = _read_snapshot(db_path) if db_path.exists() else None
    if not full and previous is None:
        raise MissingArtifact(f"No artifact at {db_path}; rerun with --full")

    if full:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        shutil.copy2(db_path, tmp)

    conn = duckdb.connect(str(tmp))
    try:
        create_schema(conn)
        result = _fill(conn, full=full, today=today, factory=factory)
        if not result.changed:
            conn.close()
            tmp.unlink(missing_ok=True)
            return result
        validate(conn, previous)
        conn.execute("CHECKPOINT")
        conn.close()
    except BaseException:
        conn.close()
        tmp.unlink(missing_ok=True)
        wal.unlink(missing_ok=True)
        raise

    # A leftover WAL would make serving's read-only open fail or miss rows.
    if wal.exists():
        tmp.unlink(missing_ok=True)
        wal.unlink(missing_ok=True)
        raise RuntimeError(f"{wal} still exists after CHECKPOINT and close")
    tmp.replace(db_path)
    return result


def _fill(
    conn: duckdb.DuckDBPyConnection,
    *,
    full: bool,
    today: date,
    factory: ClientFactory,
) -> BuildResult:
    result = BuildResult(changed=False)
    touched_fys: set[int] = set()

    for endpoint in ENDPOINTS.values():
        client = factory(endpoint)
        (latest,) = conn.execute(
            f"SELECT MAX(record_date) FROM {endpoint.key}"
        ).fetchone()
        if full or latest is None:
            df = client.fetch_range(HISTORY_START, today)
        else:
            df = client.fetch_after(latest, today)
        added = insert_frame(conn, df, endpoint.key)
        result.records_added[endpoint.key] = added
        if endpoint.key == "deposits_withdrawals" and added:
            touched_fys.update(
                int(fy) for fy in df["record_fiscal_year"].dropna().unique()
            )

    if not any(result.records_added.values()):
        return result
    result.changed = True

    if full:
        touched_fys = {
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT record_fiscal_year FROM deposits_withdrawals "
                "WHERE record_fiscal_year IS NOT NULL"
            ).fetchall()
        }
    elif touched_fys:
        touched_fys.add(current_fiscal_year(today))
    populate_fiscal_years(conn, touched_fys)
    result.fiscal_years_populated = sorted(touched_fys)

    (latest_dw,) = conn.execute(
        "SELECT MAX(record_date) FROM deposits_withdrawals"
    ).fetchone()
    result.latest_record_date = latest_dw.isoformat() if latest_dw else None
    metadata = {
        "build_date": datetime.now(UTC).isoformat(),
        "latest_record_date": result.latest_record_date,
        "source": SOURCE,
        "schema_version": SCHEMA_VERSION,
    }
    for key, value in metadata.items():
        conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value, updated_at) "
            "VALUES (?, ?, CURRENT_TIMESTAMP)",
            [key, value],
        )
    return result
