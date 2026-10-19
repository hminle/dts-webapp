"""Year-over-year comparisons of categories and daily metrics.

Ported from the reference app; only the HTTP layer moved to app/api/routers.
"""

from __future__ import annotations

import logging

import duckdb
import pandas as pd
from fastapi import HTTPException

from app.schemas.treasury import (
    CategoryDailyDataPoint,
    CategoryYearData,
    YoYCategoryComparisonRequest,
    YoYCategoryComparisonResponse,
    YoYDailyComparisonRequest,
    YoYDailyComparisonResponse,
    YoYDailyDataPoint,
)

logger = logging.getLogger(__name__)


def get_category_comparison(
    cur: duckdb.DuckDBPyConnection, request: YoYCategoryComparisonRequest
) -> YoYCategoryComparisonResponse:
    """
    Get year-over-year comparison for selected category descriptions.

    This endpoint compares FYTD amounts for selected categories across two fiscal years.

    Comparison modes:
    - 'fiscal_day': Align by day-of-fiscal-year (Day 61 vs Day 61)
    - 'calendar_date': Align by calendar month-day (Dec 31 vs Dec 31)

    Args:
        request: Fiscal years, categories and comparison_mode to compare
        cur: DuckDB cursor

    Returns:
        YoYCategoryComparisonResponse with daily data for both fiscal years
    """
    if request.current_fiscal_year == request.previous_fiscal_year:
        raise ValueError("Current and previous fiscal years must be different")

    comparison_mode = request.comparison_mode or "fiscal_day"
    if comparison_mode not in ["fiscal_day", "calendar_date"]:
        raise ValueError("comparison_mode must be 'fiscal_day' or 'calendar_date'")

    def get_category_data_for_fiscal_year(
        fiscal_year: int,
        categories: list[str],
        transaction_type: str | None,
    ) -> list[CategoryYearData]:
        """
        Get category data for a fiscal year with day_of_fiscal_year calculation.
        """
        params = [fiscal_year]

        category_placeholders = ", ".join(["?" for _ in categories])
        params.extend(categories)

        type_filter = ""
        if transaction_type:
            type_filter = "AND transaction_type = ?"
            params.append(transaction_type)

        query = f"""
        WITH ranked_data AS (
            SELECT
                record_date,
                transaction_catg,
                transaction_type,
                transaction_fytd_amt,
                DENSE_RANK() OVER (ORDER BY record_date) as day_of_fiscal_year
            FROM deposits_withdrawals
            WHERE record_fiscal_year = ?
              AND transaction_catg IN ({category_placeholders})
              {type_filter}
            ORDER BY record_date, transaction_catg
        )
        SELECT * FROM ranked_data
        ORDER BY transaction_catg, day_of_fiscal_year
        """

        df = cur.execute(query, params).df()

        if df.empty:
            return []

        if pd.api.types.is_datetime64_any_dtype(df["record_date"]):
            df["record_date"] = df["record_date"].dt.strftime("%Y-%m-%d")

        result = []
        for category in categories:
            category_df = df[df["transaction_catg"] == category]

            if category_df.empty:
                continue

            txn_type = category_df["transaction_type"].iloc[0]

            data_points = []
            for _, row in category_df.iterrows():
                data_points.append(
                    CategoryDailyDataPoint(
                        day_of_fiscal_year=int(row["day_of_fiscal_year"]),
                        record_date=str(row["record_date"]),
                        transaction_fytd_amt=float(row["transaction_fytd_amt"])
                        if pd.notna(row["transaction_fytd_amt"])
                        else 0.0,
                    )
                )

            result.append(
                CategoryYearData(
                    category_description=category,
                    transaction_type=txn_type,
                    fiscal_year=fiscal_year,
                    data_points=data_points,
                )
            )

        return result

    current_year_data = get_category_data_for_fiscal_year(
        request.current_fiscal_year,
        request.category_descriptions,
        request.transaction_type,
    )

    previous_year_data = get_category_data_for_fiscal_year(
        request.previous_fiscal_year,
        request.category_descriptions,
        request.transaction_type,
    )

    if comparison_mode == "fiscal_day":
        # Original behavior: count matching day_of_fiscal_year values.
        max_current_days = max(
            (len(cat.data_points) for cat in current_year_data), default=0
        )
        max_previous_days = max(
            (len(cat.data_points) for cat in previous_year_data), default=0
        )
        comparison_days = min(max_current_days, max_previous_days)
    else:
        # calendar_date mode: count matching MM-DD values across both years.
        current_month_days = set()
        previous_month_days = set()

        for cat in current_year_data:
            for dp in cat.data_points:
                if len(dp.record_date) >= 10:
                    current_month_days.add(dp.record_date[5:10])

        for cat in previous_year_data:
            for dp in cat.data_points:
                if len(dp.record_date) >= 10:
                    previous_month_days.add(dp.record_date[5:10])

        comparison_days = len(current_month_days & previous_month_days)

    logger.info(
        "YoY comparison: FY %s vs FY %s, %d categories, %d days, mode=%s",
        request.current_fiscal_year,
        request.previous_fiscal_year,
        len(request.category_descriptions),
        comparison_days,
        comparison_mode,
    )

    return YoYCategoryComparisonResponse(
        current_fiscal_year=request.current_fiscal_year,
        previous_fiscal_year=request.previous_fiscal_year,
        current_year_data=current_year_data,
        previous_year_data=previous_year_data,
        comparison_days=comparison_days,
        comparison_mode=comparison_mode,
    )


def get_daily_comparison(
    cur: duckdb.DuckDBPyConnection, request: YoYDailyComparisonRequest
) -> YoYDailyComparisonResponse:
    """
    Get year-over-year daily comparison for a specific metric.

    This endpoint compares daily values for a metric across two fiscal years.

    Comparison modes:
    - 'fiscal_day': Align by day-of-fiscal-year (Day 61 vs Day 61)
    - 'calendar_date': Align by calendar month-day (Dec 31 vs Dec 31)

    Supported metrics:
    - 'net_flow': Net Government Transfers (from daily_net_transfers)
    - 'total_withdrawals': Total Withdrawals excluding debt (from daily_net_transfers)
    - 'total_deposits': Total Deposits excluding debt (from daily_net_transfers)
    - Category name: FYTD amount for a specific category (from deposits_withdrawals)

    Args:
        request: YoY comparison request with fiscal years, metric, and comparison_mode
        cur: DuckDB cursor

    Returns:
        YoYDailyComparisonResponse with aligned data points and differences
    """
    if request.current_fiscal_year == request.previous_fiscal_year:
        raise ValueError("Current and previous fiscal years must be different")

    comparison_mode = request.comparison_mode or "fiscal_day"
    if comparison_mode not in ["fiscal_day", "calendar_date"]:
        raise ValueError("comparison_mode must be 'fiscal_day' or 'calendar_date'")

    metric_column_map = {
        "net_flow": "net_flow_fytd",
        "total_withdrawals": "total_withdrawals_fytd",
        "total_deposits": "total_deposits_fytd",
    }

    is_builtin_metric = request.metric in metric_column_map

    if is_builtin_metric:
        column = metric_column_map[request.metric]

        current_query = f"""
        SELECT day_of_fiscal_year, record_date, {column} as value
        FROM daily_net_transfers
        WHERE record_fiscal_year = ?
        ORDER BY day_of_fiscal_year
        """

        previous_query = f"""
        SELECT day_of_fiscal_year, record_date, {column} as value
        FROM daily_net_transfers
        WHERE record_fiscal_year = ?
        ORDER BY day_of_fiscal_year
        """

        current_df = cur.execute(current_query, (request.current_fiscal_year,)).df()
        previous_df = cur.execute(previous_query, (request.previous_fiscal_year,)).df()

    else:
        # Treat the metric as a transaction_catg lookup against deposits_withdrawals.
        current_query = """
        WITH ranked_data AS (
            SELECT
                record_date,
                transaction_fytd_amt as value,
                DENSE_RANK() OVER (ORDER BY record_date) as day_of_fiscal_year
            FROM deposits_withdrawals
            WHERE record_fiscal_year = ?
              AND transaction_catg = ?
            ORDER BY record_date
        )
        SELECT day_of_fiscal_year, record_date, value FROM ranked_data
        ORDER BY day_of_fiscal_year
        """

        current_df = cur.execute(
            current_query, (request.current_fiscal_year, request.metric)
        ).df()
        previous_df = cur.execute(
            current_query, (request.previous_fiscal_year, request.metric)
        ).df()

    if current_df.empty and previous_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for metric '{request.metric}' in either fiscal year",
        )

    for df in [current_df, previous_df]:
        if not df.empty and pd.api.types.is_datetime64_any_dtype(df["record_date"]):
            df["record_date"] = df["record_date"].dt.strftime("%Y-%m-%d")

    data_points = []

    if comparison_mode == "fiscal_day":
        # Align by day_of_fiscal_year (original behavior).
        current_lookup = {}
        for _, row in current_df.iterrows():
            current_lookup[int(row["day_of_fiscal_year"])] = {
                "date": str(row["record_date"]),
                "value": float(row["value"]) if pd.notna(row["value"]) else 0.0,
            }

        previous_lookup = {}
        for _, row in previous_df.iterrows():
            previous_lookup[int(row["day_of_fiscal_year"])] = {
                "date": str(row["record_date"]),
                "value": float(row["value"]) if pd.notna(row["value"]) else 0.0,
            }

        # For a fair YoY view, only show days up to the minimum available.
        max_current_day = max(current_lookup.keys()) if current_lookup else 0
        max_previous_day = max(previous_lookup.keys()) if previous_lookup else 0
        max_comparison_day = min(max_current_day, max_previous_day)

        all_days = sorted([d for d in current_lookup.keys() if d <= max_comparison_day])

        for day in all_days:
            current_data = current_lookup.get(day, {"date": "", "value": 0.0})
            previous_data = previous_lookup.get(day, {"date": "", "value": 0.0})

            current_value = current_data["value"]
            previous_value = previous_data["value"]
            difference = current_value - previous_value

            percent_change = None
            if previous_value != 0:
                percent_change = (
                    (current_value - previous_value) / abs(previous_value)
                ) * 100

            data_points.append(
                YoYDailyDataPoint(
                    day_of_fiscal_year=day,
                    current_date=current_data["date"]
                    if current_data["date"]
                    else previous_data["date"],
                    previous_date=previous_data["date"]
                    if previous_data["date"]
                    else None,
                    current_value=current_value,
                    previous_value=previous_value,
                    difference=difference,
                    percent_change=percent_change,
                )
            )

    else:  # comparison_mode == "calendar_date"
        # Align by calendar month-day (e.g., Oct-15 vs Oct-15).

        def get_month_day(date_str: str) -> str:
            """Extract MM-DD from YYYY-MM-DD for comparison."""
            if not date_str or len(date_str) < 10:
                return ""
            return date_str[5:10]  # Returns "MM-DD"

        current_lookup = {}
        for _, row in current_df.iterrows():
            date_str = str(row["record_date"])
            month_day = get_month_day(date_str)
            if month_day:
                current_lookup[month_day] = {
                    "date": date_str,
                    "day": int(row["day_of_fiscal_year"]),
                    "value": float(row["value"]) if pd.notna(row["value"]) else 0.0,
                }

        previous_lookup = {}
        for _, row in previous_df.iterrows():
            date_str = str(row["record_date"])
            month_day = get_month_day(date_str)
            if month_day:
                previous_lookup[month_day] = {
                    "date": date_str,
                    "day": int(row["day_of_fiscal_year"]),
                    "value": float(row["value"]) if pd.notna(row["value"]) else 0.0,
                }

        common_month_days = sorted(
            set(current_lookup.keys()) & set(previous_lookup.keys())
        )

        # Sort by the current year's day_of_fiscal_year for proper ordering.
        common_month_days_sorted = sorted(
            common_month_days, key=lambda md: current_lookup[md]["day"]
        )

        for month_day in common_month_days_sorted:
            current_data = current_lookup[month_day]
            previous_data = previous_lookup[month_day]

            current_value = current_data["value"]
            previous_value = previous_data["value"]
            difference = current_value - previous_value

            percent_change = None
            if previous_value != 0:
                percent_change = (
                    (current_value - previous_value) / abs(previous_value)
                ) * 100

            data_points.append(
                YoYDailyDataPoint(
                    day_of_fiscal_year=current_data["day"],
                    current_date=current_data["date"],
                    previous_date=previous_data["date"],
                    current_value=current_value,
                    previous_value=previous_value,
                    difference=difference,
                    percent_change=percent_change,
                )
            )

    comparison_days = len(data_points)

    logger.info(
        "YoY daily comparison: FY %s vs FY %s, metric=%s, mode=%s, days=%d",
        request.current_fiscal_year,
        request.previous_fiscal_year,
        request.metric,
        comparison_mode,
        comparison_days,
    )

    return YoYDailyComparisonResponse(
        current_fiscal_year=request.current_fiscal_year,
        previous_fiscal_year=request.previous_fiscal_year,
        metric=request.metric,
        granularity=request.granularity,
        comparison_mode=comparison_mode,
        data_points=data_points,
        comparison_days=comparison_days,
    )
