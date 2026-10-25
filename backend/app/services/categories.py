"""Major spending and receipt categories, T-bill interest, IRS refunds, daily YoY.

Ported from the reference app; only the HTTP layer moved to app/api/routers.
"""

from __future__ import annotations

import logging

import duckdb
from fastapi import HTTPException

from app.constants.categories import (
    CATEGORY_REGISTRY,
    IRS_REFUND_CATEGORY,
    IRS_REFUND_COMPONENT_NAMES,
    MAJOR_RECEIPT_CATEGORIES,
    MAJOR_SPENDING_CATEGORIES,
    OTHER_RECEIPT_CATEGORIES,
    OTHER_SPENDING_CATEGORIES,
    TBILL_INTEREST_CATEGORY,
    TBILL_INTEREST_COMPONENT_NAMES,
    CategoryDef,
    CategoryKind,
)
from app.schemas.treasury import (
    CategoryDailyYoYDataPoint,
    CategoryDailyYoYRequest,
    CategoryDailyYoYResponse,
    IrsRefundComponent,
    IrsRefundRequest,
    IrsRefundResponse,
    MajorReceiptCategoriesRequest,
    MajorReceiptCategoriesResponse,
    MajorReceiptCategory,
    MajorSpendingCategoriesRequest,
    MajorSpendingCategoriesResponse,
    MajorSpendingCategory,
    SubcategoryBreakdown,
    TBillInterestComponent,
    TBillInterestRequest,
    TBillInterestResponse,
)
from app.utils.yoy import (
    ComparisonMode,
    FYTDSource,
    covered,
    fetch_component_fytd,
    find_aligned_previous_date,
    latest_date_for_fy,
    nullable_yoy,
)

logger = logging.getLogger(__name__)


# ── FYTDSource descriptors (one per "major" endpoint) ─────────────────


_SPENDING_SOURCE = FYTDSource(
    table="deposits_withdrawals",
    fytd_column="transaction_fytd_amt",
    key_column="transaction_catg",
    extra_filters={"transaction_type": "Withdrawals"},
)
_RECEIPT_SOURCE = FYTDSource(
    table="deposits_withdrawals",
    fytd_column="transaction_fytd_amt",
    key_column="transaction_catg",
    extra_filters={"transaction_type": "Deposits"},
)
_TBILL_SOURCE = FYTDSource(
    table="adjustment_public_debt",
    fytd_column="adj_fytd_amt",
    key_column="adj_type",
)
_IRS_REFUND_SOURCE = FYTDSource(
    table="income_tax_refunds",
    fytd_column="tax_refund_fytd_amt",
    key_column="tax_refund_type",
)


_SOURCES: dict[CategoryKind, FYTDSource] = {
    "spending": _SPENDING_SOURCE,
    "receipt": _RECEIPT_SOURCE,
    "tbill": _TBILL_SOURCE,
    "irs_refund": _IRS_REFUND_SOURCE,
}


def _source_for(kind: CategoryKind) -> FYTDSource:
    """The table, columns and side filter that hold a category kind's lines."""
    return _SOURCES[kind]


def category_fytd(
    cur: duckdb.DuckDBPyConnection, cat: CategoryDef, day: str
) -> float | None:
    """Σ FYTD of ``cat``'s components on ``day``; ``None`` before ``available_from``."""
    if not covered(cat.available_from, day):
        return None
    source = _source_for(cat.kind)
    return sum(fetch_component_fytd(cur, source, day, c) for c in cat.components)


# ── Shared validators / data-resolution helpers ──────────────────────


def _validate_yoy_request(
    current_fy: int,
    previous_fy: int,
    comparison_mode: str | None,
) -> ComparisonMode:
    """Shared validation for the four major-X YoY endpoints.

    Returns the resolved comparison mode (defaulting to ``fiscal_day``).
    Raises ``ValueError`` (HTTP 400) on bad input.
    """
    if current_fy == previous_fy:
        raise ValueError("Current and previous fiscal years must be different")
    mode = comparison_mode or "fiscal_day"
    if mode not in ("fiscal_day", "calendar_date"):
        raise ValueError("comparison_mode must be 'fiscal_day' or 'calendar_date'")
    return mode  # type: ignore[return-value]


def _resolve_yoy_dates(
    cur,
    source: FYTDSource,
    *,
    current_fy: int,
    previous_fy: int,
    comparison_mode: ComparisonMode,
) -> tuple[str, str]:
    """Return ``(current_date, previous_date)`` for a YoY comparison.

    ``previous_date`` is the empty string when no aligned previous-FY
    date can be found (mirrors legacy behavior). Raises
    ``HTTPException(404)`` when the current fiscal year has no data.
    """
    current_date = latest_date_for_fy(cur, source, current_fy)
    if not current_date:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for current fiscal year {current_fy}",
        )
    previous_date = (
        find_aligned_previous_date(
            cur,
            source=source,
            current_date=current_date,
            current_fy=current_fy,
            previous_fy=previous_fy,
            mode=comparison_mode,
        )
        or ""
    )
    return current_date, previous_date


def _build_subcategory_breakdown(
    cur,
    source: FYTDSource,
    components: tuple[str, ...],
    current_date: str,
    previous_date: str,
) -> tuple[list[SubcategoryBreakdown], float, float]:
    """Build per-component breakdowns and return ``(rows, total_cur, total_prev)``."""
    rows: list[SubcategoryBreakdown] = []
    total_current = 0.0
    total_previous = 0.0
    for component_key in components:
        current_val = fetch_component_fytd(cur, source, current_date, component_key)
        previous_val = (
            fetch_component_fytd(cur, source, previous_date, component_key)
            if previous_date
            else 0.0
        )
        rows.append(
            SubcategoryBreakdown(
                category_name=component_key,
                current_fytd=current_val,
                previous_fytd=previous_val,
                yoy_change=current_val - previous_val,
            )
        )
        total_current += current_val
        total_previous += previous_val
    return rows, total_current, total_previous


def _covered_totals(
    cat: CategoryDef,
    current_date: str,
    previous_date: str,
    total_current: float,
    total_previous: float,
) -> tuple[float | None, float | None]:
    """The totals, or ``None`` for a side whose date predates the category."""
    return (
        total_current if covered(cat.available_from, current_date) else None,
        total_previous if covered(cat.available_from, previous_date) else None,
    )


# ── Endpoints ─────────────────────────────────────────────────────────


def _category_yoy(
    cur: duckdb.DuckDBPyConnection,
    request: MajorSpendingCategoriesRequest | MajorReceiptCategoriesRequest,
    source: FYTDSource,
    defs: tuple[CategoryDef, ...],
    label: str,
) -> tuple[str, str, ComparisonMode, list[dict]]:
    """Validate, resolve the aligned dates and total each category in ``defs``.

    Returns ``(current_date, previous_date, comparison_mode, categories)``,
    where each category is a dict of the fields ``MajorSpendingCategory`` and
    ``MajorReceiptCategory`` share. Totals before a category's
    ``available_from`` are ``None``.
    """
    comparison_mode = _validate_yoy_request(
        request.current_fiscal_year,
        request.previous_fiscal_year,
        request.comparison_mode,
    )
    current_date, previous_date = _resolve_yoy_dates(
        cur,
        source,
        current_fy=request.current_fiscal_year,
        previous_fy=request.previous_fiscal_year,
        comparison_mode=comparison_mode,
    )

    categories: list[dict] = []
    for cat in defs:
        subcategories, total_current, total_previous = _build_subcategory_breakdown(
            cur, source, cat.components, current_date, previous_date
        )
        current_total, previous_total = _covered_totals(
            cat, current_date, previous_date, total_current, total_previous
        )
        delta, pct = nullable_yoy(current_total, previous_total)
        categories.append(
            {
                "name": cat.name,
                "current_fytd": current_total,
                "previous_fytd": previous_total,
                "yoy_change": delta,
                "yoy_percent_change": pct,
                "available_from": cat.available_from.isoformat(),
                "subcategories": subcategories,
            }
        )

    logger.info(
        "%s: FY%s (%s) vs FY%s (%s)",
        label,
        request.current_fiscal_year,
        current_date,
        request.previous_fiscal_year,
        previous_date,
    )
    return current_date, previous_date, comparison_mode, categories


def _spending_response(
    cur: duckdb.DuckDBPyConnection,
    request: MajorSpendingCategoriesRequest,
    defs: tuple[CategoryDef, ...],
    label: str,
) -> MajorSpendingCategoriesResponse:
    current_date, previous_date, mode, categories = _category_yoy(
        cur, request, _SPENDING_SOURCE, defs, label
    )
    return MajorSpendingCategoriesResponse(
        current_fiscal_year=request.current_fiscal_year,
        previous_fiscal_year=request.previous_fiscal_year,
        current_date=current_date,
        previous_date=previous_date,
        comparison_mode=mode,
        categories=[MajorSpendingCategory(**c) for c in categories],
    )


def _receipt_response(
    cur: duckdb.DuckDBPyConnection,
    request: MajorReceiptCategoriesRequest,
    defs: tuple[CategoryDef, ...],
    label: str,
) -> MajorReceiptCategoriesResponse:
    current_date, previous_date, mode, categories = _category_yoy(
        cur, request, _RECEIPT_SOURCE, defs, label
    )
    return MajorReceiptCategoriesResponse(
        current_fiscal_year=request.current_fiscal_year,
        previous_fiscal_year=request.previous_fiscal_year,
        current_date=current_date,
        previous_date=previous_date,
        comparison_mode=mode,
        categories=[MajorReceiptCategory(**c) for c in categories],
    )


def get_major_spending(
    cur: duckdb.DuckDBPyConnection, request: MajorSpendingCategoriesRequest
) -> MajorSpendingCategoriesResponse:
    """Major federal spending categories with Y-o-Y comparison.

    Aggregates key spending categories (Social Security Benefits, Medicare,
    Medicaid, Interest on Treasury Securities) from
    ``deposits_withdrawals`` (Withdrawals only) using the registry in
    :mod:`app.constants.categories`.

    Comparison modes:
        * ``fiscal_day`` — align by day-of-fiscal-year (Day 61 vs Day 61).
        * ``calendar_date`` — align by calendar month-day (Dec 31 vs Dec 31).
    """
    return _spending_response(cur, request, MAJOR_SPENDING_CATEGORIES, "Major spending")


def get_other_spending(
    cur: duckdb.DuckDBPyConnection, request: MajorSpendingCategoriesRequest
) -> MajorSpendingCategoriesResponse:
    """The other preset spending categories (Defense, SNAP & WIC, …) with YoY.

    Same rules as :func:`get_major_spending`, over
    :data:`app.constants.categories.OTHER_SPENDING_CATEGORIES`.
    """
    return _spending_response(cur, request, OTHER_SPENDING_CATEGORIES, "Other spending")


def get_major_receipts(
    cur: duckdb.DuckDBPyConnection, request: MajorReceiptCategoriesRequest
) -> MajorReceiptCategoriesResponse:
    """Major federal receipt categories with Y-o-Y comparison.

    Aggregates Employment & Withholding Tax, Customs & Duties (Tariffs), etc.
    from ``deposits_withdrawals`` (Deposits only) using the registry in
    :mod:`app.constants.categories`.
    """
    return _receipt_response(cur, request, MAJOR_RECEIPT_CATEGORIES, "Major receipts")


def get_other_receipts(
    cur: duckdb.DuckDBPyConnection, request: MajorReceiptCategoriesRequest
) -> MajorReceiptCategoriesResponse:
    """The other preset receipt categories (income taxes, …) with YoY.

    Same rules as :func:`get_major_receipts`, over
    :data:`app.constants.categories.OTHER_RECEIPT_CATEGORIES`.
    """
    return _receipt_response(cur, request, OTHER_RECEIPT_CATEGORIES, "Other receipts")


def get_tbill_interest(
    cur: duckdb.DuckDBPyConnection, request: TBillInterestRequest
) -> TBillInterestResponse:
    """T-Bill interest with Y-o-Y comparison.

    Sums ``Bills (-) Discount`` + ``Bonds and Notes (-) Discount`` from
    ``adjustment_public_debt`` (Table III-B). Components and friendly
    display names are sourced from
    :data:`app.constants.categories.TBILL_INTEREST_COMPONENT_NAMES`.
    """
    comparison_mode = _validate_yoy_request(
        request.current_fiscal_year,
        request.previous_fiscal_year,
        request.comparison_mode,
    )
    current_date, previous_date = _resolve_yoy_dates(
        cur,
        _TBILL_SOURCE,
        current_fy=request.current_fiscal_year,
        previous_fy=request.previous_fiscal_year,
        comparison_mode=comparison_mode,
    )

    components: list[TBillInterestComponent] = []
    total_current = 0.0
    total_previous = 0.0
    for adj_type, display_name in TBILL_INTEREST_COMPONENT_NAMES.items():
        current_val = fetch_component_fytd(cur, _TBILL_SOURCE, current_date, adj_type)
        previous_val = (
            fetch_component_fytd(cur, _TBILL_SOURCE, previous_date, adj_type)
            if previous_date
            else 0.0
        )
        components.append(
            TBillInterestComponent(
                name=display_name,
                adj_type=adj_type,
                current_fytd=current_val,
                previous_fytd=previous_val,
                yoy_change=current_val - previous_val,
            )
        )
        total_current += current_val
        total_previous += previous_val

    current_total, previous_total = _covered_totals(
        TBILL_INTEREST_CATEGORY,
        current_date,
        previous_date,
        total_current,
        total_previous,
    )
    total_delta, total_pct = nullable_yoy(current_total, previous_total)

    logger.info(
        "T-Bill interest: FY%s (%s) vs FY%s (%s)",
        request.current_fiscal_year,
        current_date,
        request.previous_fiscal_year,
        previous_date,
    )
    return TBillInterestResponse(
        current_fiscal_year=request.current_fiscal_year,
        previous_fiscal_year=request.previous_fiscal_year,
        current_date=current_date,
        previous_date=previous_date,
        comparison_mode=comparison_mode,
        total_current_fytd=current_total,
        total_previous_fytd=previous_total,
        total_yoy_change=total_delta,
        total_yoy_percent_change=total_pct,
        available_from=TBILL_INTEREST_CATEGORY.available_from.isoformat(),
        components=components,
    )


def get_irs_tax_refunds(
    cur: duckdb.DuckDBPyConnection, request: IrsRefundRequest
) -> IrsRefundResponse:
    """IRS Tax Refunds with Y-o-Y comparison.

    Sources ``income_tax_refunds`` (Table V), which includes both EFT and
    Check refunds for individuals and businesses. The
    ``deposits_withdrawals`` table only carries EFT refund categories, so
    using it would understate the total.

    Components are sourced from
    :data:`app.constants.categories.IRS_REFUND_COMPONENT_NAMES` (insertion
    order is preserved on Python 3.7+ dicts and matches the legacy hand-
    rolled list).
    """
    comparison_mode = _validate_yoy_request(
        request.current_fiscal_year,
        request.previous_fiscal_year,
        request.comparison_mode,
    )
    current_date, previous_date = _resolve_yoy_dates(
        cur,
        _IRS_REFUND_SOURCE,
        current_fy=request.current_fiscal_year,
        previous_fy=request.previous_fiscal_year,
        comparison_mode=comparison_mode,
    )

    components: list[IrsRefundComponent] = []
    total_current = 0.0
    total_previous = 0.0
    for refund_type, display_name in IRS_REFUND_COMPONENT_NAMES.items():
        current_val = fetch_component_fytd(
            cur, _IRS_REFUND_SOURCE, current_date, refund_type
        )
        previous_val = (
            fetch_component_fytd(cur, _IRS_REFUND_SOURCE, previous_date, refund_type)
            if previous_date
            else 0.0
        )
        components.append(
            IrsRefundComponent(
                name=display_name,
                tax_refund_type=refund_type,
                current_fytd=current_val,
                previous_fytd=previous_val,
                yoy_change=current_val - previous_val,
            )
        )
        total_current += current_val
        total_previous += previous_val

    current_total, previous_total = _covered_totals(
        IRS_REFUND_CATEGORY, current_date, previous_date, total_current, total_previous
    )
    total_delta, total_pct = nullable_yoy(current_total, previous_total)

    logger.info(
        "IRS Tax Refunds: FY%s (%s) vs FY%s (%s)",
        request.current_fiscal_year,
        current_date,
        request.previous_fiscal_year,
        previous_date,
    )
    return IrsRefundResponse(
        current_fiscal_year=request.current_fiscal_year,
        previous_fiscal_year=request.previous_fiscal_year,
        current_date=current_date,
        previous_date=previous_date,
        comparison_mode=comparison_mode,
        total_current_fytd=current_total,
        total_previous_fytd=previous_total,
        total_yoy_change=total_delta,
        total_yoy_percent_change=total_pct,
        available_from=IRS_REFUND_CATEGORY.available_from.isoformat(),
        components=components,
    )


def get_daily_yoy(
    cur: duckdb.DuckDBPyConnection, request: CategoryDailyYoYRequest
) -> CategoryDailyYoYResponse:
    """
    Get daily YoY data for a specific major category.

    Returns daily FYTD values with YoY comparison for chart visualization.

    Category types:
    - 'spending': Major spending categories (Social Security, Medicare, etc.)
    - 'receipt': Major receipt categories (Employment Tax, Customs, etc.)
    - 'tbill': T-Bill interest components

    Comparison modes:
    - 'fiscal_day': Align by day-of-fiscal-year (Day 61 vs Day 61)
    - 'calendar_date': Align by calendar month-day (Dec 31 vs Dec 31)
    """
    current_fy = request.current_fiscal_year
    previous_fy = request.previous_fiscal_year
    category_name = request.category_name
    category_type = request.category_type.lower()
    comparison_mode = request.comparison_mode or "fiscal_day"

    if current_fy == previous_fy:
        raise ValueError("Current and previous fiscal years must be different")

    if category_type not in ["spending", "receipt", "tbill", "irs_refund"]:
        raise ValueError(
            "category_type must be 'spending', 'receipt', 'tbill', or 'irs_refund'"
        )

    if comparison_mode not in ["fiscal_day", "calendar_date"]:
        raise ValueError("comparison_mode must be 'fiscal_day' or 'calendar_date'")

    cat_info: CategoryDef | None = CATEGORY_REGISTRY.get(category_name)
    if cat_info is None:
        raise ValueError(
            (
                f"Unknown category: {category_name}. "
                f"Valid categories: {list(CATEGORY_REGISTRY.keys())}"
            ),
        )

    # extra_filters are already applied via filter_clause(), which is why
    # this dispatcher needs no separate per-kind SQL templates.
    source = _source_for(cat_info.kind)

    placeholders = ", ".join("?" for _ in cat_info.components)
    extra_clause, extra_params = source.filter_clause()
    daily_query = f"""
    SELECT record_date, SUM({source.fytd_column}) as fytd_amt
    FROM {source.table}
    WHERE record_fiscal_year = ?
      AND {source.key_column} IN ({placeholders}){extra_clause}
    GROUP BY record_date
    ORDER BY record_date
    """
    current_result = cur.execute(
        daily_query, [current_fy, *cat_info.components, *extra_params]
    ).fetchall()
    previous_result = cur.execute(
        daily_query, [previous_fy, *cat_info.components, *extra_params]
    ).fetchall()

    def format_date(d):
        if hasattr(d, "strftime"):
            return d.strftime("%Y-%m-%d")
        return str(d)

    current_data = {}
    for i, (date, fytd) in enumerate(current_result):
        date_str = format_date(date)
        current_data[date_str] = {"fytd": float(fytd) if fytd else 0.0, "day": i + 1}

    previous_data = {}
    for i, (date, fytd) in enumerate(previous_result):
        date_str = format_date(date)
        previous_data[date_str] = {"fytd": float(fytd) if fytd else 0.0, "day": i + 1}

    def previous_point(prev_info: dict) -> tuple[str | None, float | None]:
        # A missing aligned date or one before the category's coverage has
        # no comparable total, which is not the same as a total of 0.
        prev_date = prev_info["date"]
        if not covered(cat_info.available_from, prev_date):
            return prev_date, None
        return prev_date, prev_info["fytd"]

    data_points = []

    if comparison_mode == "fiscal_day":
        previous_by_day = {
            v["day"]: {"date": k, "fytd": v["fytd"]} for k, v in previous_data.items()
        }

        for curr_date, curr_info in sorted(current_data.items()):
            day_num = curr_info["day"]
            curr_fytd = (
                curr_info["fytd"]
                if covered(cat_info.available_from, curr_date)
                else None
            )

            prev_info = previous_by_day.get(day_num, {"date": None, "fytd": None})
            prev_date, prev_fytd = previous_point(prev_info)
            yoy_delta, yoy_percent = nullable_yoy(curr_fytd, prev_fytd)

            data_points.append(
                CategoryDailyYoYDataPoint(
                    day_of_fiscal_year=day_num,
                    current_date=curr_date,
                    previous_date=prev_date,
                    current_fytd=curr_fytd,
                    previous_fytd=prev_fytd,
                    yoy_change=yoy_delta,
                    yoy_percent_change=yoy_percent,
                )
            )
    else:
        # calendar_date mode: match by MM-DD.
        previous_by_mmdd = {}
        for date_str, info in previous_data.items():
            mm_dd = date_str[5:10]  # Extract MM-DD
            previous_by_mmdd[mm_dd] = {"date": date_str, "fytd": info["fytd"]}

        for curr_date, curr_info in sorted(current_data.items()):
            day_num = curr_info["day"]
            curr_fytd = (
                curr_info["fytd"]
                if covered(cat_info.available_from, curr_date)
                else None
            )
            mm_dd = curr_date[5:10]

            prev_info = previous_by_mmdd.get(mm_dd, {"date": None, "fytd": None})
            prev_date, prev_fytd = previous_point(prev_info)
            yoy_delta, yoy_percent = nullable_yoy(curr_fytd, prev_fytd)

            data_points.append(
                CategoryDailyYoYDataPoint(
                    day_of_fiscal_year=day_num,
                    current_date=curr_date,
                    previous_date=prev_date,
                    current_fytd=curr_fytd,
                    previous_fytd=prev_fytd,
                    yoy_change=yoy_delta,
                    yoy_percent_change=yoy_percent,
                )
            )

    logger.info(
        "Category daily YoY: %s FY%s vs FY%s, %d days",
        category_name,
        current_fy,
        previous_fy,
        len(data_points),
    )

    return CategoryDailyYoYResponse(
        category_name=category_name,
        category_type=category_type,
        current_fiscal_year=current_fy,
        previous_fiscal_year=previous_fy,
        comparison_mode=comparison_mode,
        comparison_days=len(data_points),
        available_from=cat_info.available_from.isoformat(),
        data_points=data_points,
    )
