"""Raw Treasury rows across tables, paginated in SQL."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import duckdb
from fastapi import HTTPException

from app.constants.endpoints import ACCOUNT_TYPE_TABLES, ALL_TABLES, data_table_for
from app.schemas.treasury import TreasuryDataList
from app.utils.frames import convert_df_for_pydantic

WhereFor = Callable[[str], tuple[str, list[Any]]]


@dataclass(frozen=True)
class DataFilters:
    data_source: str | None = None
    account_type: str | None = None
    fiscal_year: int | None = None
    start_date: str | None = None
    end_date: str | None = None

    def tables(self) -> list[str]:
        if self.data_source:
            return [data_table_for(self.data_source)]
        return list(ALL_TABLES)

    def where_for(self, table: str) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        # As in the reference, the account_type filter only narrows tables that
        # have the column; other tables are returned unfiltered by it.
        if self.account_type and table in ACCOUNT_TYPE_TABLES:
            clauses.append("account_type = ?")
            params.append(self.account_type)
        if self.fiscal_year:
            clauses.append("record_fiscal_year = ?")
            params.append(self.fiscal_year)
        if self.start_date:
            clauses.append("record_date >= ?")
            params.append(self.start_date)
        if self.end_date:
            clauses.append("record_date <= ?")
            params.append(self.end_date)
        return (" AND ".join(clauses) or "TRUE"), params


def _paginated_union(
    cur: duckdb.DuckDBPyConnection,
    tables: list[str],
    where_for: WhereFor,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    total = 0
    branches: list[str] = []
    params: list[Any] = []
    for table in tables:
        where, table_params = where_for(table)
        total += cur.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {where}", table_params
        ).fetchone()[0]
        branches.append(
            f"SELECT *, '{table}' AS data_source FROM {table} WHERE {where}"
        )
        params.extend(table_params)

    # UNION ALL BY NAME fills columns a table lacks with NULL, which is what the
    # reference's pd.concat did after loading every table in full. The
    # data_source, id tiebreak keeps pages stable for rows sharing a date.
    query = (
        "SELECT * FROM ("
        + " UNION ALL BY NAME ".join(branches)
        + ") ORDER BY record_date DESC, data_source, id LIMIT ? OFFSET ?"
    )
    df = cur.execute(query, [*params, page_size, (page - 1) * page_size]).df()
    return convert_df_for_pydantic(df).to_dict(orient="records"), total


def list_data(
    cur: duckdb.DuckDBPyConnection, filters: DataFilters, page: int, page_size: int
) -> TreasuryDataList:
    """One page of rows matching ``filters``, newest first."""
    items, total = _paginated_union(
        cur, filters.tables(), filters.where_for, page, page_size
    )
    return TreasuryDataList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total else 0,
    )


def get_data_by_date(
    cur: duckdb.DuckDBPyConnection, date: str, data_source: str | None
) -> list[dict[str, Any]]:
    """Every row for one date, table by table.

    Raises:
        HTTPException: 404 when no table has rows for the date.
    """
    tables = [data_table_for(data_source)] if data_source else list(ALL_TABLES)
    # _table_order keeps the reference's table-by-table output order.
    branches = [
        f"SELECT *, '{t}' AS data_source, {i} AS _table_order FROM {t} "
        "WHERE record_date = ?"
        for i, t in enumerate(tables)
    ]
    df = cur.execute(
        "SELECT * EXCLUDE (_table_order) FROM ("
        + " UNION ALL BY NAME ".join(branches)
        + ") ORDER BY _table_order, id",
        [date] * len(tables),
    ).df()
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for date {date}")
    return convert_df_for_pydantic(df).to_dict(orient="records")
