"""Where the TGA closing balance lives in ``operating_cash_balance``, by era.

The Treasury moved the balance between rows twice. Since 2022-04-18 the
closing balance row carries the amount in ``open_today_bal``; its
``close_today_bal`` is NULL. Each era's last close equals the next era's
first open (checked on 2021-09-30/10-01 and 2022-04-15/04-18).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BalanceRow:
    """One era's row label and the column holding its closing balance."""

    account_type: str
    column: str


CLOSING_BALANCE_ROWS: tuple[BalanceRow, ...] = (
    # 2005-10-03 to 2021-09-30
    BalanceRow("Federal Reserve Account", "close_today_bal"),
    # 2021-10-01 to 2022-04-15
    BalanceRow("Treasury General Account (TGA)", "close_today_bal"),
    # 2022-04-18 on
    BalanceRow("Treasury General Account (TGA) Closing Balance", "open_today_bal"),
)
