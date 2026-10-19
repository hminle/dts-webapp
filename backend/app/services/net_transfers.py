"""Pre-computed daily net transfers (built by ingestion's populate step)."""

import duckdb
from fastapi import HTTPException

from app.schemas.treasury import DailyNetTransfer
from app.utils.frames import convert_df_for_pydantic


def get_for_date(cur: duckdb.DuckDBPyConnection, date: str) -> DailyNetTransfer:
    """The net-transfer row for one date.

    Raises:
        HTTPException: 404 when the date has no statement.
    """
    df = cur.execute(
        "SELECT * FROM daily_net_transfers WHERE record_date = ?", [date]
    ).df()
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No daily net transfers data found for date {date}. "
                "Data for this date is not available."
            ),
        )
    return DailyNetTransfer(**convert_df_for_pydantic(df).to_dict(orient="records")[0])


def get_for_fiscal_year(
    cur: duckdb.DuckDBPyConnection, fiscal_year: int
) -> list[DailyNetTransfer]:
    """Every net-transfer row of a fiscal year, by day of the fiscal year.

    Raises:
        HTTPException: 404 when the fiscal year has no rows.
    """
    df = cur.execute(
        "SELECT * FROM daily_net_transfers WHERE record_fiscal_year = ? "
        "ORDER BY day_of_fiscal_year",
        [fiscal_year],
    ).df()
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No daily net transfers data found for fiscal year {fiscal_year}. "
                "Data for this fiscal year is not available."
            ),
        )
    records = convert_df_for_pydantic(df).to_dict(orient="records")
    return [DailyNetTransfer(**r) for r in records]
