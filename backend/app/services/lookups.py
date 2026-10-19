"""Option lists the pages offer: fiscal years, data sources, categories."""

import duckdb

from app.constants.endpoints import ACCOUNT_TYPE_TABLES, ALL_TABLES, data_table_for
from app.schemas.treasury import CategoryListResponse


def get_account_types(
    cur: duckdb.DuckDBPyConnection, data_source: str | None
) -> list[str]:
    """Distinct account types, optionally for one table.

    A table without an ``account_type`` column has none (an empty list, as in
    the reference); an unknown table name is an error.
    """
    if data_source:
        table = data_table_for(data_source)
        if table not in ACCOUNT_TYPE_TABLES:
            return []
        tables: tuple[str, ...] = (table,)
    else:
        tables = ACCOUNT_TYPE_TABLES
    found: set[str] = set()
    for table in tables:
        found.update(
            row[0]
            for row in cur.execute(
                f"SELECT DISTINCT account_type FROM {table} "
                "WHERE account_type IS NOT NULL"
            ).fetchall()
        )
    return sorted(found)


def get_data_sources() -> list[str]:
    """Every queryable table, including the derived ``daily_net_transfers``."""
    return list(ALL_TABLES)


def get_fiscal_years(cur: duckdb.DuckDBPyConnection) -> list[int]:
    """Fiscal years with data in any table, newest first."""
    years: set[int] = set()
    for table in ALL_TABLES:
        years.update(
            row[0]
            for row in cur.execute(
                f"SELECT DISTINCT record_fiscal_year FROM {table} "
                "WHERE record_fiscal_year IS NOT NULL"
            ).fetchall()
        )
    return sorted(years, reverse=True)


def _categories(cur: duckdb.DuckDBPyConnection, transaction_type: str) -> list[str]:
    # The reference notes the labels live in transaction_catg, not _desc.
    rows = cur.execute(
        """
        SELECT DISTINCT transaction_catg
        FROM deposits_withdrawals
        WHERE transaction_type = ?
          AND transaction_catg IS NOT NULL
          AND transaction_catg != ''
        ORDER BY transaction_catg
        """,
        [transaction_type],
    ).fetchall()
    return [row[0] for row in rows if row[0]]


def get_categories(cur: duckdb.DuckDBPyConnection) -> CategoryListResponse:
    """Deposit and withdrawal category labels from ``deposits_withdrawals``."""
    return CategoryListResponse(
        deposits=_categories(cur, "Deposits"),
        withdrawals=_categories(cur, "Withdrawals"),
    )
