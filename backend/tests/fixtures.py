"""Row builders shaped like real DTS rows, for seeding test artifacts."""

from datetime import date

import pandas as pd


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
