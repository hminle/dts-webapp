"""The Methodology page's worked examples, run through the real formula code.

The page renders its figures from ``worked-examples.json``; this test feeds the
file's inputs to the functions that compute the live numbers, so the page can't
show arithmetic the app doesn't do.
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from app.schemas.treasury import (
    IrsRefundRequest,
    MajorReceiptCategoriesRequest,
    MajorSpendingCategoriesRequest,
    TBillInterestRequest,
)
from app.services.categories import (
    get_irs_tax_refunds,
    get_major_receipts,
    get_major_spending,
    get_tbill_interest,
)
from app.utils.deposits_withdrawals import calculate_daily_net_transfers
from app.utils.yoy import yoy_change
from tests.fixtures import apd_row, catg_row, dw_row, formula_db, itr_row

EXAMPLES_PATH = (
    Path(__file__).resolve().parents[2]
    / "frontend/src/features/methodology/worked-examples.json"
)
EX = json.loads(EXAMPLES_PATH.read_text())
CATS = EX["categories"]
CUR = date.fromisoformat(CATS["current_date"])
PREV = date.fromisoformat(CATS["previous_date"])
YEARS = {"current_fiscal_year": 2027, "previous_fiscal_year": 2026}


def _pct(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def test_net_transfers_example() -> None:
    nt = EX["net_transfers"]
    day = date.fromisoformat(nt["date"])
    today, fytd = nt["inputs"]["today"], nt["inputs"]["fytd"]

    def row(account_type: str, transaction_type: str, key: str, catg=None):
        return dw_row(
            day,
            nt["fiscal_year"],
            account_type=account_type,
            transaction_type=transaction_type,
            transaction_catg=catg,
            today=today[key],
            mtd=fytd[key],
            fytd=fytd[key],
        )

    tga = "Treasury General Account (TGA)"
    df = pd.concat(
        [
            row("Treasury General Account Total Deposits", "Deposits", "tga_deposits"),
            row(
                "Treasury General Account Total Withdrawals",
                "Withdrawals",
                "tga_withdrawals",
            ),
            row(tga, "Deposits", "debt_issues", "Public Debt Cash Issues (Table IIIB)"),
            row(
                tga,
                "Withdrawals",
                "debt_redemptions",
                "Public Debt Cash Redemp. (Table IIIB)",
            ),
        ],
        ignore_index=True,
    )
    m = calculate_daily_net_transfers(df, nt["date"])
    for period in ("today", "fytd"):
        out = nt["outputs"][period]
        assert m[f"total_deposits_{period}"] == out["total_deposits"]
        assert m[f"total_withdrawals_{period}"] == out["total_withdrawals"]
        assert m[f"net_flow_{period}"] == out["net_transfers"]


@pytest.mark.parametrize("key", ["yoy", "yoy_negative_base"])
def test_yoy_examples(key: str) -> None:
    ex = EX[key]
    current = ex["current"]["value"] if key == "yoy" else ex["current"]
    previous = ex["previous"]["value"] if key == "yoy" else ex["previous"]
    delta, pct = yoy_change(current, previous)
    assert delta == ex["difference"]
    assert _pct(pct) == ex["percent_change"]


def test_yoy_example_is_the_net_transfers_fytd() -> None:
    assert (
        EX["yoy"]["current"]["value"]
        == EX["net_transfers"]["outputs"]["fytd"]["net_transfers"]
    )


def _assert_card(card, ex: dict) -> None:
    assert card.current_fytd == ex["current_total"]
    assert card.previous_fytd == ex["previous_total"]
    assert card.yoy_change == ex["difference"]
    assert _pct(card.yoy_percent_change) == ex["percent_change"]


def _line_items(transaction_type: str, ex: dict) -> list[pd.DataFrame]:
    return [
        catg_row(d, fy, transaction_type=transaction_type, transaction_catg=k, fytd=v)
        for d, fy, side in ((CUR, 2027, "current"), (PREV, 2026, "previous"))
        for k, v in ex[side].items()
    ]


def test_medicare_example() -> None:
    conn = formula_db(
        {"deposits_withdrawals": _line_items("Withdrawals", CATS["medicare"])}
    )
    result = get_major_spending(conn.cursor(), MajorSpendingCategoriesRequest(**YEARS))
    card = next(c for c in result.categories if c.name == "Medicare")
    _assert_card(card, CATS["medicare"])


def test_customs_example() -> None:
    conn = formula_db(
        {"deposits_withdrawals": _line_items("Deposits", CATS["customs"])}
    )
    result = get_major_receipts(conn.cursor(), MajorReceiptCategoriesRequest(**YEARS))
    card = next(c for c in result.categories if c.name == "Customs & Duties (Tariffs)")
    _assert_card(card, CATS["customs"])


def test_tbill_example() -> None:
    ex = CATS["tbill"]
    conn = formula_db(
        {
            "adjustment_public_debt": [
                apd_row(d, fy, adj_type=k, fytd=v)
                for d, fy, side in ((CUR, 2027, "current"), (PREV, 2026, "previous"))
                for k, v in ex[side].items()
            ]
        }
    )
    r = get_tbill_interest(conn.cursor(), TBillInterestRequest(**YEARS))
    assert (r.total_current_fytd, r.total_previous_fytd) == (
        ex["current_total"],
        ex["previous_total"],
    )
    assert r.total_yoy_change == ex["difference"]
    assert _pct(r.total_yoy_percent_change) == ex["percent_change"]


def test_irs_refunds_example() -> None:
    ex = CATS["irs_refunds"]
    conn = formula_db(
        {
            "income_tax_refunds": [
                itr_row(CUR, 2027, tax_refund_type=k, fytd=v)
                for k, v in ex["table_v"].items()
            ]
        }
    )
    r = get_irs_tax_refunds(conn.cursor(), IrsRefundRequest(**YEARS))
    assert r.total_current_fytd == ex["table_v_total"]
    # Table II lists only the two EFT refund lines.
    eft = sum(v for k, v in ex["table_v"].items() if k.endswith("(EFT)"))
    assert eft == ex["table_ii_eft_only"]
