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
    RollingAverageRequest,
    TBillInterestRequest,
    WeeklySnapshotRequest,
)
from app.services.categories import (
    get_combined,
    get_irs_tax_refunds,
    get_major_receipts,
    get_major_spending,
    get_tbill_interest,
)
from app.services.rolling import get_daily
from app.services.snapshot import get_weekly
from app.utils.deposits_withdrawals import calculate_daily_net_transfers
from app.utils.yoy import yoy_change
from tests.fixtures import apd_row, catg_row, dnt_row, dw_row, formula_db, itr_row

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


def test_social_security_example() -> None:
    ex = CATS["social_security"]
    conn = formula_db({"deposits_withdrawals": _line_items("Withdrawals", ex)})
    result = get_major_spending(conn.cursor(), MajorSpendingCategoriesRequest(**YEARS))
    card = next(c for c in result.categories if c.name == "Social Security Benefits")
    _assert_card(card, ex)


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


ROLL = EX["rolling"]
COMB = EX["combined"]
ROLL_DATES = [date.fromisoformat(d) for d in ROLL["withdrawals_dates"]]
CBP = "DHS - Customs & Border Protection (CBP)"


def _unemployment_rows() -> list[pd.DataFrame]:
    return [
        dw_row(
            day,
            2026,
            account_type="Treasury General Account (TGA)",
            transaction_type="Withdrawals",
            transaction_catg="DOL - Unemployment Benefits",
            today=v,
        )
        for day, v in zip(ROLL_DATES, ROLL["unemployment_today"], strict=True)
    ]


def _combined_frames() -> dict[str, list[pd.DataFrame]]:
    """Interest, customs and CBP lines on the example's two dates."""
    lines, adjustments = [], []
    for day, fy, side in (
        (COMB["current_date"], 2026, "current"),
        (COMB["previous_date"], 2025, "previous"),
    ):
        d = date.fromisoformat(day)
        income = COMB["interest_income"][side]
        customs = COMB["net_customs"][side]
        # Each year carries the customs line name in force at the time.
        customs_line = (
            "DHS - Customs Duties, Taxes, and Fees"
            if side == "current"
            else "DHS - Customs and Certain Excise Taxes"
        )
        for catg, kind, value in (
            (
                "Interest on Treasury Securities",
                "Withdrawals",
                income["Interest on Treasury Securities"],
            ),
            (customs_line, "Deposits", customs["customs"]),
            (CBP, "Withdrawals", customs["cbp"]),
        ):
            lines.append(
                catg_row(
                    d, fy, transaction_type=kind, transaction_catg=catg, fytd=value
                )
            )
        for adj in ("Bills (-)", "Bonds and Notes (-)"):
            adjustments.append(apd_row(d, fy, adj_type=adj, fytd=income[adj]))
    return {"deposits_withdrawals": lines, "adjustment_public_debt": adjustments}


def test_rolling_example() -> None:
    conn = formula_db(
        {
            "daily_net_transfers": [
                dnt_row(
                    day,
                    2026,
                    i + 1,
                    withdrawals_fytd=0,
                    deposits_fytd=0,
                    withdrawals_today=v,
                )
                for i, (day, v) in enumerate(
                    zip(ROLL_DATES, ROLL["withdrawals_today"], strict=True)
                )
            ],
            "deposits_withdrawals": _unemployment_rows(),
        }
    )
    end = date.fromisoformat(ROLL["end_date"])
    for metric, average in (
        ("total_withdrawals", ROLL["withdrawals_average"]),
        ("unemployment_benefits", ROLL["unemployment_average"]),
    ):
        result = get_daily(
            conn.cursor(),
            RollingAverageRequest(
                metric=metric, window=ROLL["window"], start_date=end, end_date=end
            ),
        )
        (point,) = result.points
        assert point.rolling_average == pytest.approx(average)
        if metric == "total_withdrawals":
            assert point.projected_monthly == pytest.approx(ROLL["projected_monthly"])


def _combined_example(name: str, key: str) -> None:
    conn = formula_db(_combined_frames())
    result = get_combined(
        conn.cursor(),
        MajorSpendingCategoriesRequest(
            current_fiscal_year=2026, previous_fiscal_year=2025
        ),
    )
    (figure,) = [c for c in result.categories if c.name == name]
    expected = COMB[key]
    assert (result.current_date, result.previous_date) == (
        COMB["current_date"],
        COMB["previous_date"],
    )
    assert (figure.current_fytd, figure.previous_fytd, figure.yoy_change) == (
        expected["current_total"],
        expected["previous_total"],
        expected["difference"],
    )
    assert _pct(figure.yoy_percent_change) == expected["percent_change"]


def test_interest_income_example() -> None:
    _combined_example("Interest Income Transfers", "interest_income")


def test_net_customs_example() -> None:
    _combined_example("Net Customs Receipts", "net_customs")


def test_weekly_snapshot_example() -> None:
    ws = EX["weekly_snapshot"]
    week = ws["previous_week"]
    fy = ws["fiscal_year"]
    withheld = "Taxes - Withheld Individual/FICA"

    withdrawals_today = dict(zip(ROLL_DATES, ROLL["withdrawals_today"], strict=True))

    def statement(day: str, fiscal_year: int, n: int, figures: dict, key: str, **kw):
        d = date.fromisoformat(day)
        return dnt_row(
            d,
            fiscal_year,
            n,
            withdrawals_fytd=figures["withdrawals_fytd"][key],
            deposits_fytd=figures["deposits_fytd"][key],
            withdrawals_today=withdrawals_today.get(d, 0.0),
            **kw,
        )

    n, last_n = ws["day_of_fiscal_year"], week["day_of_fiscal_year"]
    snapshot_days = {
        date.fromisoformat(ws["record_date"]),
        date.fromisoformat(week["record_date"]),
    }
    # The other statements of the 10-day window carry only their withdrawals.
    window_rows = [
        dnt_row(day, fy, 0, withdrawals_fytd=0, deposits_fytd=0, withdrawals_today=v)
        for day, v in withdrawals_today.items()
        if day not in snapshot_days
    ]
    combined = _combined_frames()
    conn = formula_db(
        {
            "adjustment_public_debt": combined["adjustment_public_debt"],
            "daily_net_transfers": [
                *window_rows,
                statement(
                    ws["record_date"],
                    fy,
                    n,
                    ws,
                    "current",
                    withdrawals_mtd=ws["withdrawals_mtd"],
                    net_mtd=ws["net_transfers_mtd"],
                ),
                statement(ws["previous_date"], fy - 1, n, ws, "previous"),
                statement(week["record_date"], fy, last_n, week, "current"),
                statement(week["previous_date"], fy - 1, last_n, week, "previous"),
            ],
            "deposits_withdrawals": [
                *combined["deposits_withdrawals"],
                *_unemployment_rows(),
                *(
                    catg_row(
                        date.fromisoformat(day),
                        year,
                        transaction_type="Deposits",
                        transaction_catg=withheld,
                        fytd=ws["withholding_fytd"][key],
                    )
                    for day, year, key in (
                        (ws["record_date"], fy, "current"),
                        (ws["previous_date"], fy - 1, "previous"),
                    )
                ),
            ],
        }
    )
    s = get_weekly(
        conn.cursor(),
        WeeklySnapshotRequest(
            anchor_weekday=ws["anchor_weekday"],
            as_of=date.fromisoformat(ws["record_date"]),
        ),
    )

    assert (s.anchor_date, s.record_date, s.previous_date) == (
        ws["anchor_date"],
        ws["record_date"],
        ws["previous_date"],
    )
    assert s.day_of_fiscal_year == n
    assert (s.withdrawals_mtd, s.net_transfers_mtd) == (
        ws["withdrawals_mtd"],
        ws["net_transfers_mtd"],
    )
    for key in ("withdrawals_fytd", "deposits_fytd", "net_transfers_fytd"):
        figure, expected = getattr(s, key), ws[key]
        assert (figure.current, figure.previous, figure.change) == (
            expected["current"],
            expected["previous"],
            expected["change"],
        )
        assert _pct(figure.percent_change) == expected["percent_change"]
    assert s.withholding_fytd.change == ws["withholding_fytd"]["change"]
    assert (
        _pct(s.withholding_fytd.percent_change)
        == (ws["withholding_fytd"]["percent_change"])
    )
    assert s.previous_week_date == week["record_date"]
    assert s.previous_week_net_transfers_gap == week["gap"]
    assert s.net_transfers_gap_change == ws["gap_change"]
    assert s.withdrawals_10d_average == pytest.approx(ws["withdrawals_10d_average"])
    assert s.projected_monthly_withdrawals == pytest.approx(
        ws["projected_monthly_withdrawals"]
    )
    assert s.unemployment_10d_average == pytest.approx(ws["unemployment_10d_average"])
    for key in ("interest_income_fytd", "net_customs_fytd"):
        figure, expected = getattr(s, key), ws[key]
        assert (figure.current, figure.previous, figure.change) == (
            expected["current"],
            expected["previous"],
            expected["change"],
        )
        assert _pct(figure.percent_change) == expected["percent_change"]
