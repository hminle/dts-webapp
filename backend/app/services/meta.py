"""Facts about the artifact: size, coverage, and when it was built."""

import duckdb

from app.constants.endpoints import ACCOUNT_TYPE_TABLES, ENDPOINT_TABLES
from app.schemas.meta import BuildInfo
from app.schemas.treasury import DatabaseStats


def _metadata(cur: duckdb.DuckDBPyConnection) -> dict[str, str]:
    return dict(cur.execute("SELECT key, value FROM metadata").fetchall())


def get_stats(cur: duckdb.DuckDBPyConnection) -> DatabaseStats:
    """Record count, date range and dimensions across the endpoint tables."""
    record_count = 0
    earliest: str | None = None
    latest: str | None = None
    fiscal_years: set[int] = set()
    for table in ENDPOINT_TABLES:
        count, low, high = cur.execute(
            f"SELECT COUNT(*), MIN(record_date)::VARCHAR, MAX(record_date)::VARCHAR "
            f"FROM {table}"
        ).fetchone()
        record_count += count
        if low and (earliest is None or low < earliest):
            earliest = low
        if high and (latest is None or high > latest):
            latest = high
        fiscal_years.update(
            row[0]
            for row in cur.execute(
                f"SELECT DISTINCT record_fiscal_year FROM {table} "
                "WHERE record_fiscal_year IS NOT NULL"
            ).fetchall()
        )
    account_types: set[str] = set()
    for table in ACCOUNT_TYPE_TABLES:
        account_types.update(
            row[0]
            for row in cur.execute(
                f"SELECT DISTINCT account_type FROM {table} "
                "WHERE account_type IS NOT NULL"
            ).fetchall()
        )
    return DatabaseStats(
        record_count=record_count,
        earliest_date=earliest,
        latest_date=latest,
        # The reference read a "last_updated" key its fetch task wrote; the
        # ingestion job records the same moment as build_date.
        last_updated=_metadata(cur).get("build_date"),
        account_types=sorted(account_types),
        fiscal_years=sorted(fiscal_years, reverse=True),
        data_sources=list(ENDPOINT_TABLES),
    )


def get_record_counts(cur: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Row count per endpoint table."""
    return {
        table: cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ENDPOINT_TABLES
    }


def get_record_counts_by_year(cur: duckdb.DuckDBPyConnection) -> dict[int, int]:
    """Rows per fiscal year summed across endpoint tables, newest year first."""
    counts: dict[int, int] = {}
    for table in ENDPOINT_TABLES:
        for year, count in cur.execute(
            f"SELECT record_fiscal_year, COUNT(*) FROM {table} "
            "WHERE record_fiscal_year IS NOT NULL GROUP BY 1"
        ).fetchall():
            counts[year] = counts.get(year, 0) + count
    return dict(sorted(counts.items(), reverse=True))


def get_build_info(cur: duckdb.DuckDBPyConnection) -> BuildInfo:
    """The metadata ingestion wrote when it built this artifact."""
    return BuildInfo.model_validate(_metadata(cur))
