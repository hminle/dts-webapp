"""Row builders shaped like real DTS rows, for seeding test artifacts."""

from datetime import date

import duckdb
import pandas as pd

from app.core.schema import create_schema
from app.ingest.insert import insert_frame


def _dw_row(day: date, fy: int, **fields: object) -> dict[str, object]:
    return {"record_date": day, "record_fiscal_year": fy, **fields}


def _amounts(today: float) -> dict[str, float]:
    # MTD/FYTD are simple multiples so tests can assert all three periods.
    return {
        "transaction_today_amt": today,
        "transaction_mtd_amt": today * 10,
        "transaction_fytd_amt": today * 100,
    }


def dw_day(
    day: date,
    fy: int,
    *,
    deposits: float,
    withdrawals: float,
    debt_issues: float,
    debt_redemptions: float,
) -> pd.DataFrame:
    """The four ``deposits_withdrawals`` rows ``calculate_daily_net_transfers`` uses.

    Labels match the reference formula (``app/utils/deposits_withdrawals.py``).
    """
    tga = "Treasury General Account (TGA)"
    return pd.DataFrame(
        [
            _dw_row(
                day,
                fy,
                account_type="Treasury General Account Total Deposits",
                transaction_type="Deposits",
                **_amounts(deposits),
            ),
            _dw_row(
                day,
                fy,
                account_type="Treasury General Account Total Withdrawals",
                transaction_type="Withdrawals",
                **_amounts(withdrawals),
            ),
            _dw_row(
                day,
                fy,
                account_type=tga,
                transaction_type="Deposits",
                transaction_catg="Public Debt Cash Issues (Table IIIB)",
                **_amounts(debt_issues),
            ),
            _dw_row(
                day,
                fy,
                account_type=tga,
                transaction_type="Withdrawals",
                transaction_catg="Public Debt Cash Redemp. (Table IIIB)",
                **_amounts(debt_redemptions),
            ),
        ]
    )


def dw_day_without_totals(day: date, fy: int) -> pd.DataFrame:
    """A date whose rows give the formula nothing to work with (it returns None)."""
    return pd.DataFrame(
        [
            _dw_row(
                day,
                fy,
                account_type="Supplementary Account",
                transaction_type="Deposits",
                **_amounts(1.0),
            )
        ]
    )


def endpoint_row(day: date, fy: int) -> pd.DataFrame:
    """One minimal row for any endpoint table."""
    return pd.DataFrame([{"record_date": day, "record_fiscal_year": fy}])


def dw_row(
    day: date,
    fy: int,
    *,
    account_type: str,
    transaction_type: str,
    today: float,
    transaction_catg: str | None = None,
    mtd: float | None = None,
    fytd: float | None = None,
) -> pd.DataFrame:
    """One ``deposits_withdrawals`` row; MTD/FYTD default to ×10 / ×100 of today."""
    return pd.DataFrame(
        [
            _dw_row(
                day,
                fy,
                account_type=account_type,
                transaction_type=transaction_type,
                transaction_catg=transaction_catg,
                transaction_today_amt=today,
                transaction_mtd_amt=today * 10 if mtd is None else mtd,
                transaction_fytd_amt=today * 100 if fytd is None else fytd,
            )
        ]
    )


def catg_row(
    day: date, fy: int, *, transaction_type: str, transaction_catg: str, fytd: float
) -> pd.DataFrame:
    """One TGA line-item row carrying only the FYTD amount the category sums read."""
    return dw_row(
        day,
        fy,
        account_type="Treasury General Account (TGA)",
        transaction_type=transaction_type,
        transaction_catg=transaction_catg,
        today=0.0,
        mtd=0.0,
        fytd=fytd,
    )


def apd_row(day: date, fy: int, *, adj_type: str, fytd: float) -> pd.DataFrame:
    """One ``adjustment_public_debt`` row (T-Bill interest components)."""
    return pd.DataFrame(
        [
            {
                "record_date": day,
                "record_fiscal_year": fy,
                "adj_type": adj_type,
                "adj_fytd_amt": fytd,
            }
        ]
    )


def itr_row(day: date, fy: int, *, tax_refund_type: str, fytd: float) -> pd.DataFrame:
    """One ``income_tax_refunds`` row (IRS refund components)."""
    return pd.DataFrame(
        [
            {
                "record_date": day,
                "record_fiscal_year": fy,
                "tax_refund_type": tax_refund_type,
                "tax_refund_fytd_amt": fytd,
            }
        ]
    )


def formula_db(frames: dict[str, list[pd.DataFrame]]) -> duckdb.DuckDBPyConnection:
    """An in-memory artifact holding exactly ``frames``, built by the real schema.

    Callers that need ``daily_net_transfers`` run ``populate_fiscal_years`` on it.
    """
    conn = duckdb.connect(":memory:")
    create_schema(conn)
    for table, table_frames in frames.items():
        for frame in table_frames:
            insert_frame(conn, frame, table)
    return conn
