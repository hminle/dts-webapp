"""Checks an artifact must pass before it may replace the published one."""

from dataclasses import dataclass
from datetime import date

import duckdb

from app.constants.endpoints import ENDPOINT_TABLES

REQUIRED_METADATA = ("build_date", "latest_record_date", "source", "schema_version")


class ArtifactInvalid(RuntimeError):
    """The built artifact failed validation; it must not be published."""


@dataclass(frozen=True)
class Snapshot:
    counts: dict[str, int]
    latest: dict[str, date | None]


def snapshot(conn: duckdb.DuckDBPyConnection) -> Snapshot:
    """Row count and latest ``record_date`` of every endpoint table."""
    counts: dict[str, int] = {}
    latest: dict[str, date | None] = {}
    for table in ENDPOINT_TABLES:
        count, max_date = conn.execute(
            f"SELECT COUNT(*), MAX(record_date) FROM {table}"
        ).fetchone()
        counts[table] = count
        latest[table] = max_date
    return Snapshot(counts=counts, latest=latest)


def validate(conn: duckdb.DuckDBPyConnection, previous: Snapshot | None) -> Snapshot:
    """Validate the artifact and return its snapshot.

    Every failure is collected so one run reports all of them.

    Raises:
        ArtifactInvalid: If any check fails.
    """
    current = snapshot(conn)
    problems: list[str] = []

    for table in ENDPOINT_TABLES:
        if current.counts[table] == 0:
            problems.append(f"{table} is empty")
        if previous is None:
            continue
        if current.counts[table] < previous.counts[table]:
            problems.append(
                f"{table} shrank: {current.counts[table]} rows, "
                f"previously {previous.counts[table]}"
            )
        before, now = previous.latest[table], current.latest[table]
        if before is not None and (now is None or now < before):
            problems.append(
                f"{table} latest date went back: {now}, previously {before}"
            )

    for fy, dates, rows, max_day in conn.execute(
        """
        SELECT dw.fy, dw.dates, COALESCE(d.rows, 0), d.max_day
        FROM (
            SELECT record_fiscal_year AS fy, COUNT(DISTINCT record_date) AS dates
            FROM deposits_withdrawals
            WHERE record_fiscal_year IS NOT NULL
            GROUP BY 1
        ) dw
        LEFT JOIN (
            SELECT record_fiscal_year AS fy, COUNT(*) AS rows,
                   MAX(day_of_fiscal_year) AS max_day
            FROM daily_net_transfers
            GROUP BY 1
        ) d USING (fy)
        ORDER BY fy
        """
    ).fetchall():
        if rows == 0:
            problems.append(f"daily_net_transfers has no rows for FY{fy}")
        elif max_day > dates:
            problems.append(
                f"daily_net_transfers FY{fy}: day {max_day} exceeds {dates} dates"
            )

    present = {
        row[0]
        for row in conn.execute(
            "SELECT key FROM metadata WHERE key IN (?, ?, ?, ?)",
            list(REQUIRED_METADATA),
        ).fetchall()
    }
    for key in REQUIRED_METADATA:
        if key not in present:
            problems.append(f"metadata is missing {key}")

    if problems:
        raise ArtifactInvalid("; ".join(problems))
    return current
