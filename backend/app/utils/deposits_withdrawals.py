"""Daily net transfers from ``deposits_withdrawals`` rows.

The Treasury has published Table II in more than one shape, and the totals are
read differently in each:

- From 2022-04-18 the statement carries its own total rows
  (``Treasury General Account Total Deposits`` / ``... Total Withdrawals``),
  with the Treasury's MTD and FYTD.
- Before that the app adds up the day's line items. Until FY2013 cash sat in
  two accounts, the Federal Reserve Account and the Tax and Loan Note
  Accounts, so both are summed and the transfers between them are dropped.
- The old format printed some lines (the "Other Withdrawals" sub-lines) only
  on days they had activity, so adding up a day's FYTD column misses every
  line absent that day. :func:`net_transfer_series` rebuilds MTD and FYTD for
  those days as running sums of the daily amounts.

Borrowing is removed on both sides. The debt lines were renamed on 2022-09-12,
from "(Table III-B)" to "(Table IIIB)", so they are matched by prefix.
"""

import logging
from datetime import date
from typing import Any

import pandas as pd

from app.utils.fiscal import current_fiscal_year

logger = logging.getLogger(__name__)

TOTAL_DEPOSITS = "Treasury General Account Total Deposits"
TOTAL_WITHDRAWALS = "Treasury General Account Total Withdrawals"
# "Other Withdrawals" is not an account: the 2020-08-14 statement filed nine
# withdrawal lines under it, and they are real spending.
CASH_ACCOUNTS = (
    "Treasury General Account (TGA)",
    "Federal Reserve Account",
    "Tax and Loan Note Accounts",
    "Other Withdrawals",
)
DEBT_ISSUES = "Public Debt Cash Issues"
DEBT_REDEMPTIONS = "Public Debt Cash Redemp."
TRANSFERS = "Transfers"

_COLUMNS = {
    "today": "transaction_today_amt",
    "mtd": "transaction_mtd_amt",
    "fytd": "transaction_fytd_amt",
}
_BASES = (
    "tga_total_deposits",
    "tga_total_withdrawals",
    "public_debt_issues",
    "public_debt_redemptions",
    "total_deposits",
    "total_withdrawals",
    "net_flow",
)

Amounts = dict[str, float]


def _amounts(rows: pd.DataFrame) -> Amounts:
    return {p: float(rows[col].fillna(0).sum()) for p, col in _COLUMNS.items()}


def _catg(df: pd.DataFrame) -> pd.Series:
    # Hand-built frames in tests may omit the column; real rows always have it.
    if "transaction_catg" not in df:
        return pd.Series("", index=df.index)
    return df["transaction_catg"].fillna("")


def _side(
    df: pd.DataFrame, transaction_type: str, total_account: str
) -> tuple[Amounts, bool] | None:
    """One side's gross amounts and whether they came from line items."""
    total = df[df["account_type"] == total_account]
    if not total.empty:
        return _amounts(total), False
    catg = _catg(df)
    items = df[
        df["account_type"].isin(CASH_ACCOUNTS)
        & (df["transaction_type"] == transaction_type)
        & ~catg.str.startswith(TRANSFERS)
    ]
    if items.empty:
        return None
    return _amounts(items), True


def _debt(df: pd.DataFrame, transaction_type: str, prefix: str) -> Amounts:
    catg = _catg(df)
    return _amounts(
        df[
            df["account_type"].isin(CASH_ACCOUNTS)
            & (df["transaction_type"] == transaction_type)
            & catg.str.startswith(prefix)
        ]
    )


def calculate_daily_net_transfers(df: pd.DataFrame, date: str) -> dict[str, Any] | None:
    """Net transfer metrics for one statement date.

    - Total deposits = gross deposits − public debt cash issues
    - Total withdrawals = gross withdrawals − public debt cash redemptions
    - Net flow = total withdrawals − total deposits
    - Leading flow = total withdrawals (today)

    MTD and FYTD are the statement's own columns. When ``line_items`` is true
    those undercount, and :func:`net_transfer_series` replaces them.

    Args:
        df: The ``deposits_withdrawals`` rows for the date.
        date: The date, ``YYYY-MM-DD``.

    Returns:
        The metrics, or None when either side has no usable rows.
    """
    if df.empty:
        logger.warning("No data provided for date %s", date)
        return None
    deposits = _side(df, "Deposits", TOTAL_DEPOSITS)
    withdrawals = _side(df, "Withdrawals", TOTAL_WITHDRAWALS)
    if deposits is None or withdrawals is None:
        logger.warning("No deposits or no withdrawals for %s", date)
        return None
    (gross_in, in_items), (gross_out, out_items) = deposits, withdrawals
    issues = _debt(df, "Deposits", DEBT_ISSUES)
    redemptions = _debt(df, "Withdrawals", DEBT_REDEMPTIONS)

    metrics: dict[str, Any] = {"date": date, "line_items": in_items or out_items}
    for p in _COLUMNS:
        total_in = gross_in[p] - issues[p]
        total_out = gross_out[p] - redemptions[p]
        metrics |= {
            f"tga_total_deposits_{p}": gross_in[p],
            f"tga_total_withdrawals_{p}": gross_out[p],
            f"public_debt_issues_{p}": issues[p],
            f"public_debt_redemptions_{p}": redemptions[p],
            f"total_deposits_{p}": total_in,
            f"total_withdrawals_{p}": total_out,
            f"net_flow_{p}": total_out - total_in,
        }
    metrics["leading_flow"] = metrics["total_withdrawals_today"]
    return metrics


def net_transfer_series(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Metrics for every date in ``df`` that has them, oldest first.

    Line-item days get MTD and FYTD as running sums of the daily amounts, so
    ``df`` must hold each fiscal year from its first statement. A date without
    usable rows is left out and adds nothing to the running sums.
    """
    if df.empty:
        return []
    dates = pd.to_datetime(df["record_date"]).dt.strftime("%Y-%m-%d")
    sums: dict[tuple[Any, ...], dict[str, float]] = {}
    series: list[dict[str, Any]] = []
    for day, day_df in df.groupby(dates, sort=True):
        metrics = calculate_daily_net_transfers(day_df, day)
        if metrics is None:
            continue
        fy = current_fiscal_year(date.fromisoformat(day))
        for period, key in (("mtd", (fy, day[:7])), ("fytd", (fy,))):
            running = sums.setdefault((period, *key), dict.fromkeys(_BASES, 0.0))
            for base in _BASES:
                running[base] += metrics[f"{base}_today"]
                if metrics["line_items"]:
                    metrics[f"{base}_{period}"] = running[base]
        series.append(metrics)
    return series
