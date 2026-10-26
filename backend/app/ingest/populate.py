"""Build the derived ``daily_net_transfers`` table from ``deposits_withdrawals``."""

import logging
from collections.abc import Iterable
from typing import Any

import duckdb
import pandas as pd

from app.ingest.insert import insert_frame, utc_now_naive
from app.utils.deposits_withdrawals import net_transfer_series

logger = logging.getLogger(__name__)

METRIC_FIELDS = (
    "tga_total_deposits_today",
    "tga_total_withdrawals_today",
    "public_debt_issues_today",
    "public_debt_redemptions_today",
    "total_deposits_today",
    "total_withdrawals_today",
    "net_flow_today",
    "leading_flow",
    "tga_total_deposits_mtd",
    "tga_total_withdrawals_mtd",
    "public_debt_issues_mtd",
    "public_debt_redemptions_mtd",
    "total_deposits_mtd",
    "total_withdrawals_mtd",
    "net_flow_mtd",
    "tga_total_deposits_fytd",
    "tga_total_withdrawals_fytd",
    "public_debt_issues_fytd",
    "public_debt_redemptions_fytd",
    "total_deposits_fytd",
    "total_withdrawals_fytd",
    "net_flow_fytd",
)


def compute_daily_records(
    fy_df: pd.DataFrame, fiscal_year: int
) -> list[dict[str, Any]]:
    """Compute one ``daily_net_transfers`` row per date of a fiscal year.

    ``day_of_fiscal_year`` is the date's rank among *all* distinct dates in the
    FY, so it equals ``DENSE_RANK() OVER (ORDER BY record_date)``. The reference
    only advanced its counter on dates with valid metrics, so one bad day shifted
    every later day's number and disagreed with the YoY queries.
    """
    if fy_df.empty:
        return []
    dates = sorted(
        pd.to_datetime(fy_df["record_date"]).dt.strftime("%Y-%m-%d").unique()
    )
    day_numbers = {day: n for n, day in enumerate(dates, start=1)}
    series = net_transfer_series(fy_df)
    for day in sorted(set(dates) - {m["date"] for m in series}):
        logger.warning("FY %d: no metrics for %s, skipping", fiscal_year, day)
    now = utc_now_naive()
    records = [
        {
            "record_date": m["date"],
            "record_fiscal_year": fiscal_year,
            "day_of_fiscal_year": day_numbers[m["date"]],
            **{field: m[field] for field in METRIC_FIELDS},
            "created_at": now,
            "updated_at": now,
        }
        for m in series
    ]
    logger.info("FY %d: %d rows from %d dates", fiscal_year, len(records), len(dates))
    return records


def populate_fiscal_years(
    conn: duckdb.DuckDBPyConnection, fiscal_years: Iterable[int]
) -> dict[int, int]:
    """Replace ``daily_net_transfers`` rows for each fiscal year.

    Returns:
        Rows written per fiscal year.
    """
    written: dict[int, int] = {}
    for fy in sorted(set(fiscal_years)):
        fy_df = conn.execute(
            "SELECT * FROM deposits_withdrawals WHERE record_fiscal_year = ?", [fy]
        ).df()
        records = compute_daily_records(fy_df, fy)
        conn.execute(
            "DELETE FROM daily_net_transfers WHERE record_fiscal_year = ?", [fy]
        )
        written[fy] = insert_frame(conn, pd.DataFrame(records), "daily_net_transfers")
    return written
