"""
Pydantic schemas for Treasury data validation and serialization.

These schemas define the structure and validation rules for API requests
and responses related to Treasury data.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.utils.anchor import AnchorWeekday


class TreasuryDataBase(BaseModel):
    """Base schema for Treasury data with common fields."""

    record_date: str = Field(..., description="Record date in YYYY-MM-DD format")
    data_source: str | None = Field(None, description="Data source endpoint key")
    account_type: str | None = Field(None, description="Account type")
    transaction_type: str | None = Field(None, description="Transaction type")
    transaction_catg: str | None = Field(None, description="Transaction category")
    account_desc: str | None = Field(None, description="Account description")

    # Financial amounts (in millions)
    transaction_today_amt: float | None = Field(
        None, description="Today's transaction amount"
    )
    transaction_mtd_amt: float | None = Field(None, description="Month-to-date amount")
    transaction_fytd_amt: float | None = Field(
        None, description="Fiscal year-to-date amount"
    )

    # Fiscal period
    record_fiscal_year: int | None = Field(None, description="Fiscal year")
    record_calendar_year: int | None = Field(None, description="Calendar year")


class TreasuryDataResponse(TreasuryDataBase):
    """Schema for Treasury data responses."""

    id: int = Field(..., description="Record ID")
    created_at: datetime | None = Field(None, description="Creation timestamp")


class TreasuryDataList(BaseModel):
    """Schema for paginated list of Treasury data."""

    items: list[TreasuryDataResponse] = Field(..., description="List of records")
    total: int = Field(..., description="Total number of records")
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(50, ge=1, le=1000, description="Number of records per page")
    pages: int = Field(..., description="Total number of pages")


class DatabaseStats(BaseModel):
    """Schema for database statistics."""

    record_count: int = Field(..., description="Total number of records")
    earliest_date: str | None = Field(None, description="Earliest record date")
    latest_date: str | None = Field(None, description="Latest record date")
    last_updated: str | None = Field(None, description="Last update timestamp")
    account_types: list[str] = Field(
        default_factory=list, description="Available account types"
    )
    fiscal_years: list[int] = Field(
        default_factory=list, description="Available fiscal years"
    )
    data_sources: list[str] = Field(
        default_factory=list, description="Available data sources"
    )


class TreasuryMetrics(BaseModel):
    """Schema for calculated treasury metrics."""

    date: str = Field(..., description="Date of metrics")
    total_deposits: dict[str, float] = Field(
        ..., description="Total deposits (today, mtd, fytd)"
    )
    total_withdrawals: dict[str, float] = Field(
        ..., description="Total withdrawals (today, mtd, fytd)"
    )
    net_government_transfers: dict[str, float] = Field(
        ..., description="Net government transfers (today, mtd, fytd)"
    )
    public_debt_cash_issues: dict[str, float] = Field(
        ..., description="Public debt cash issues (today, mtd, fytd)"
    )
    public_debt_cash_redemp: dict[str, float] = Field(
        ..., description="Public debt cash redemptions (today, mtd, fytd)"
    )


class WeeklyComparisonRequest(BaseModel):
    """Schema for weekly comparison requests."""

    first_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="First fiscal year to compare"
    )
    second_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Second fiscal year to compare"
    )
    data_source: str | None = Field(None, description="Filter by data source")
    anchor_weekday: AnchorWeekday = Field(
        "friday", description="Weekday each week is read on"
    )


class WeeklyDataPoint(BaseModel):
    """Schema for a single weekly data point."""

    week_number: int = Field(..., description="Week number in fiscal year")
    record_date: str = Field(..., description="Actual date of the record")
    net_transfer_today: float | None = Field(
        None, description="Net transfer amount for today"
    )
    net_transfer_mtd: float | None = Field(None, description="Net transfer MTD")
    net_transfer_fytd: float | None = Field(None, description="Net transfer FYTD")
    total_deposits: float | None = Field(None, description="Total deposits")
    total_withdrawals: float | None = Field(None, description="Total withdrawals")


class WeeklyComparisonResponse(BaseModel):
    """Schema for weekly comparison response."""

    first_fiscal_year: int = Field(..., description="First fiscal year")
    second_fiscal_year: int = Field(..., description="Second fiscal year")
    first_year_data: list[WeeklyDataPoint] = Field(
        default_factory=list, description="First year weekly data"
    )
    second_year_data: list[WeeklyDataPoint] = Field(
        default_factory=list, description="Second year weekly data"
    )
    comparison_weeks: int = Field(..., description="Number of weeks compared")


class DailyNetTransfer(BaseModel):
    """Schema for daily net transfers stored in database."""

    id: int | None = Field(None, description="Record ID")
    record_date: str = Field(..., description="Date of the record")
    record_fiscal_year: int = Field(..., description="Fiscal year")
    day_of_fiscal_year: int = Field(
        ..., description="Day number in fiscal year (sequential)"
    )

    # Today amounts
    tga_total_deposits_today: float = Field(
        ..., description="TGA Total Deposits (Today)"
    )
    tga_total_withdrawals_today: float = Field(
        ..., description="TGA Total Withdrawals (Today)"
    )
    public_debt_issues_today: float = Field(
        ..., description="Public Debt Cash Issues (Today)"
    )
    public_debt_redemptions_today: float = Field(
        ..., description="Public Debt Cash Redemptions (Today)"
    )
    total_deposits_today: float = Field(
        ..., description="Total Deposits excluding debt (Today)"
    )
    total_withdrawals_today: float = Field(
        ..., description="Total Withdrawals excluding debt (Today)"
    )
    net_flow_today: float = Field(..., description="Net Government Transfers (Today)")
    leading_flow: float = Field(
        ..., description="Leading Flow - equals Total Withdrawals (Today)"
    )

    # MTD amounts
    tga_total_deposits_mtd: float = Field(..., description="TGA Total Deposits (MTD)")
    tga_total_withdrawals_mtd: float = Field(
        ..., description="TGA Total Withdrawals (MTD)"
    )
    public_debt_issues_mtd: float = Field(
        ..., description="Public Debt Cash Issues (MTD)"
    )
    public_debt_redemptions_mtd: float = Field(
        ..., description="Public Debt Cash Redemptions (MTD)"
    )
    total_deposits_mtd: float = Field(
        ..., description="Total Deposits excluding debt (MTD)"
    )
    total_withdrawals_mtd: float = Field(
        ..., description="Total Withdrawals excluding debt (MTD)"
    )
    net_flow_mtd: float = Field(..., description="Net Government Transfers (MTD)")

    # FYTD amounts
    tga_total_deposits_fytd: float = Field(..., description="TGA Total Deposits (FYTD)")
    tga_total_withdrawals_fytd: float = Field(
        ..., description="TGA Total Withdrawals (FYTD)"
    )
    public_debt_issues_fytd: float = Field(
        ..., description="Public Debt Cash Issues (FYTD)"
    )
    public_debt_redemptions_fytd: float = Field(
        ..., description="Public Debt Cash Redemptions (FYTD)"
    )
    total_deposits_fytd: float = Field(
        ..., description="Total Deposits excluding debt (FYTD)"
    )
    total_withdrawals_fytd: float = Field(
        ..., description="Total Withdrawals excluding debt (FYTD)"
    )
    net_flow_fytd: float = Field(..., description="Net Government Transfers (FYTD)")

    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Update timestamp")


class YoYCategoryComparisonRequest(BaseModel):
    """Schema for year-over-year category comparison requests."""

    current_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Current fiscal year to compare"
    )
    previous_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Previous fiscal year to compare"
    )
    category_descriptions: list[str] = Field(
        ..., min_length=1, description="List of transaction_catg_desc values to compare"
    )
    transaction_type: str | None = Field(
        None, description="Filter by 'Deposits' or 'Withdrawals'"
    )
    comparison_mode: str = Field(
        default="fiscal_day",
        description=(
            "Comparison mode: 'fiscal_day' (Day N vs Day N) or 'calendar_date' (Dec 31 "
            "vs Dec 31)"
        ),
    )


class CategoryDailyDataPoint(BaseModel):
    """Schema for a single day's data for a category."""

    day_of_fiscal_year: int = Field(
        ..., description="Day number within the fiscal year (1-366)"
    )
    record_date: str = Field(..., description="Actual date in YYYY-MM-DD format")
    transaction_fytd_amt: float = Field(..., description="FYTD cumulative amount")


class CategoryYearData(BaseModel):
    """Schema for a single category's data for one fiscal year."""

    category_description: str = Field(
        ..., description="The transaction_catg_desc value"
    )
    transaction_type: str = Field(..., description="'Deposits' or 'Withdrawals'")
    fiscal_year: int = Field(..., description="Fiscal year")
    data_points: list[CategoryDailyDataPoint] = Field(
        default_factory=list, description="Daily data points"
    )


class YoYCategoryComparisonResponse(BaseModel):
    """Schema for year-over-year category comparison response."""

    current_fiscal_year: int = Field(..., description="Current fiscal year")
    previous_fiscal_year: int = Field(..., description="Previous fiscal year")
    current_year_data: list[CategoryYearData] = Field(
        default_factory=list, description="Current year category data"
    )
    previous_year_data: list[CategoryYearData] = Field(
        default_factory=list, description="Previous year category data"
    )
    comparison_days: int = Field(
        ..., description="Number of days compared (limited by shortest year)"
    )
    comparison_mode: str = Field(
        default="fiscal_day",
        description="Comparison mode: 'fiscal_day' or 'calendar_date'",
    )


class CategoryListResponse(BaseModel):
    """Schema for available categories response."""

    deposits: list[str] = Field(
        default_factory=list, description="Categories under Deposits"
    )
    withdrawals: list[str] = Field(
        default_factory=list, description="Categories under Withdrawals"
    )


# YoY Daily Comparison Schemas


class YoYDailyComparisonRequest(BaseModel):
    """Schema for year-over-year daily comparison requests."""

    current_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Current fiscal year to compare"
    )
    previous_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Previous fiscal year to compare"
    )
    metric: str = Field(
        ...,
        description=(
            "Metric to compare: 'net_flow', 'total_withdrawals', 'total_deposits', or "
            "a category name"
        ),
    )
    granularity: str = Field(
        default="daily", description="Data granularity: 'daily' only (weekly removed)"
    )
    comparison_mode: str = Field(
        default="fiscal_day",
        description=(
            "Comparison mode: 'fiscal_day' (Day N vs Day N) or 'calendar_date' (Dec 31 "
            "vs Dec 31)"
        ),
    )


class YoYDailyDataPoint(BaseModel):
    """Schema for a single day's YoY comparison data point."""

    day_of_fiscal_year: int = Field(
        ..., description="Day number within the fiscal year (1-366)"
    )
    current_date: str = Field(
        ..., description="Date in current fiscal year (YYYY-MM-DD)"
    )
    previous_date: str | None = Field(
        None, description="Date in previous fiscal year (YYYY-MM-DD)"
    )
    current_value: float = Field(..., description="Value in current fiscal year")
    previous_value: float = Field(..., description="Value in previous fiscal year")
    difference: float = Field(..., description="Current - Previous (YoY change)")
    percent_change: float | None = Field(
        None, description="Percent change from previous year"
    )


class YoYDailyComparisonResponse(BaseModel):
    """Schema for year-over-year daily comparison response."""

    current_fiscal_year: int = Field(..., description="Current fiscal year")
    previous_fiscal_year: int = Field(..., description="Previous fiscal year")
    metric: str = Field(..., description="The metric being compared")
    granularity: str = Field(..., description="Data granularity: 'daily'")
    comparison_mode: str = Field(
        ..., description="Comparison mode: 'fiscal_day' or 'calendar_date'"
    )
    data_points: list[YoYDailyDataPoint] = Field(
        default_factory=list, description="YoY comparison data points"
    )
    comparison_days: int = Field(..., description="Number of days compared")


# Major Spending Categories Schemas


class SubcategoryBreakdown(BaseModel):
    """Schema for a subcategory within a major spending category."""

    category_name: str = Field(..., description="The transaction_catg value")
    current_fytd: float = Field(..., description="Current fiscal year FYTD amount")
    previous_fytd: float = Field(..., description="Previous fiscal year FYTD amount")
    yoy_change: float = Field(..., description="Year-over-year change amount")


class MajorSpendingCategory(BaseModel):
    """Schema for a major spending category with breakdown."""

    name: str = Field(
        ..., description="Display name (e.g., 'Social Security Benefits')"
    )
    current_fytd: float | None = Field(
        ...,
        description=(
            "Total current fiscal year FYTD amount"
            " (null when the date is before available_from)"
        ),
    )
    previous_fytd: float | None = Field(
        ...,
        description=(
            "Total previous fiscal year FYTD amount"
            " (null when the date is before available_from)"
        ),
    )
    yoy_change: float | None = Field(
        ...,
        description=(
            "Year-over-year change amount (null when the date is before available_from)"
        ),
    )
    yoy_percent_change: float | None = Field(
        None, description="Year-over-year percent change"
    )
    available_from: str = Field(
        ..., description="First comparable date (ISO); totals before it are null"
    )
    subcategories: list[SubcategoryBreakdown] = Field(
        default_factory=list, description="Breakdown by subcategory"
    )


class MajorSpendingCategoriesRequest(BaseModel):
    """Schema for requesting major spending categories data."""

    current_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Current fiscal year"
    )
    previous_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Previous fiscal year for Y-o-Y comparison"
    )
    comparison_mode: str = Field(
        default="fiscal_day",
        description=(
            "Comparison mode: 'fiscal_day' (Day N vs Day N) or 'calendar_date' (Dec 31 "
            "vs Dec 31)"
        ),
    )


class MajorSpendingCategoriesResponse(BaseModel):
    """Schema for major spending categories response."""

    current_fiscal_year: int = Field(..., description="Current fiscal year")
    previous_fiscal_year: int = Field(..., description="Previous fiscal year")
    current_date: str = Field(
        ..., description="Latest date with data in current fiscal year"
    )
    previous_date: str = Field(
        ..., description="Equivalent date in previous fiscal year"
    )
    comparison_mode: str = Field(
        default="fiscal_day", description="Comparison mode used"
    )
    categories: list[MajorSpendingCategory] = Field(
        default_factory=list, description="List of major spending categories"
    )


# Major Receipt Categories Schemas


class MajorReceiptCategory(BaseModel):
    """Schema for a major receipt category with breakdown."""

    name: str = Field(
        ..., description="Display name (e.g., 'Employment & Withholding Tax')"
    )
    current_fytd: float | None = Field(
        ...,
        description=(
            "Total current fiscal year FYTD amount"
            " (null when the date is before available_from)"
        ),
    )
    previous_fytd: float | None = Field(
        ...,
        description=(
            "Total previous fiscal year FYTD amount"
            " (null when the date is before available_from)"
        ),
    )
    yoy_change: float | None = Field(
        ...,
        description=(
            "Year-over-year change amount (null when the date is before available_from)"
        ),
    )
    yoy_percent_change: float | None = Field(
        None, description="Year-over-year percent change"
    )
    available_from: str = Field(
        ..., description="First comparable date (ISO); totals before it are null"
    )
    subcategories: list[SubcategoryBreakdown] = Field(
        default_factory=list, description="Breakdown by subcategory"
    )


class MajorReceiptCategoriesRequest(BaseModel):
    """Schema for requesting major receipt categories data."""

    current_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Current fiscal year"
    )
    previous_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Previous fiscal year for Y-o-Y comparison"
    )
    comparison_mode: str = Field(
        default="fiscal_day",
        description=(
            "Comparison mode: 'fiscal_day' (Day N vs Day N) or 'calendar_date' (Dec 31 "
            "vs Dec 31)"
        ),
    )


class MajorReceiptCategoriesResponse(BaseModel):
    """Schema for major receipt categories response."""

    current_fiscal_year: int = Field(..., description="Current fiscal year")
    previous_fiscal_year: int = Field(..., description="Previous fiscal year")
    current_date: str = Field(
        ..., description="Latest date with data in current fiscal year"
    )
    previous_date: str = Field(
        ..., description="Equivalent date in previous fiscal year"
    )
    comparison_mode: str = Field(
        default="fiscal_day", description="Comparison mode used"
    )
    categories: list[MajorReceiptCategory] = Field(
        default_factory=list, description="List of major receipt categories"
    )


# T-Bill Interest Schemas


class TBillInterestComponent(BaseModel):
    """Schema for a T-Bill interest component (Bills or Bonds and Notes discount)."""

    name: str = Field(..., description="Component name (e.g., 'Bills (-) Discount')")
    adj_type: str = Field(
        ..., description="The adj_type value from adjustment_public_debt table"
    )
    current_fytd: float = Field(..., description="Current fiscal year FYTD amount")
    previous_fytd: float = Field(..., description="Previous fiscal year FYTD amount")
    yoy_change: float = Field(..., description="Year-over-year change amount")


class TBillInterestRequest(BaseModel):
    """Schema for requesting T-Bill interest data."""

    current_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Current fiscal year"
    )
    previous_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Previous fiscal year for Y-o-Y comparison"
    )
    comparison_mode: str = Field(
        default="fiscal_day",
        description=(
            "Comparison mode: 'fiscal_day' (Day N vs Day N) or 'calendar_date' (Dec 31 "
            "vs Dec 31)"
        ),
    )


class TBillInterestResponse(BaseModel):
    """Schema for T-Bill interest response."""

    current_fiscal_year: int = Field(..., description="Current fiscal year")
    previous_fiscal_year: int = Field(..., description="Previous fiscal year")
    current_date: str = Field(
        ..., description="Latest date with data in current fiscal year"
    )
    previous_date: str = Field(
        ..., description="Equivalent date in previous fiscal year"
    )
    comparison_mode: str = Field(
        default="fiscal_day", description="Comparison mode used"
    )
    total_current_fytd: float | None = Field(
        ...,
        description=(
            "Total T-Bill interest for current fiscal year"
            " (null when the date is before available_from)"
        ),
    )
    total_previous_fytd: float | None = Field(
        ...,
        description=(
            "Total T-Bill interest for previous fiscal year"
            " (null when the date is before available_from)"
        ),
    )
    total_yoy_change: float | None = Field(
        ...,
        description=(
            "Total year-over-year change (null when the date is before available_from)"
        ),
    )
    available_from: str = Field(
        ..., description="First comparable date (ISO); totals before it are null"
    )
    total_yoy_percent_change: float | None = Field(
        None, description="Total year-over-year percent change"
    )
    components: list[TBillInterestComponent] = Field(
        default_factory=list, description="Breakdown by component"
    )


# Category Daily YoY Schemas


class CategoryDailyYoYRequest(BaseModel):
    """Schema for requesting daily YoY data for a specific category."""

    category_name: str = Field(
        ...,
        description=(
            "Category name (e.g., 'Social Security Benefits', 'Medicare', 'T-Bill "
            "Interest')"
        ),
    )
    category_type: str = Field(
        ..., description="Type of category: 'spending', 'receipt', or 'tbill'"
    )
    current_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Current fiscal year"
    )
    previous_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Previous fiscal year for Y-o-Y comparison"
    )
    comparison_mode: str = Field(
        default="fiscal_day",
        description="Comparison mode: 'fiscal_day' or 'calendar_date'",
    )


class CategoryDailyYoYDataPoint(BaseModel):
    """Schema for a single day's YoY data for a category."""

    day_of_fiscal_year: int = Field(
        ..., description="Day number within the fiscal year"
    )
    current_date: str = Field(..., description="Date in current fiscal year")
    previous_date: str | None = Field(None, description="Date in previous fiscal year")
    current_fytd: float | None = Field(
        ...,
        description=(
            "FYTD amount in current year (null when the date is before available_from)"
        ),
    )
    previous_fytd: float | None = Field(
        ...,
        description=(
            "FYTD amount in previous year (null when the date is before available_from)"
        ),
    )
    yoy_change: float | None = Field(
        ...,
        description=(
            "YoY difference (current - previous)"
            " (null when the date is before available_from)"
        ),
    )
    yoy_percent_change: float | None = Field(None, description="YoY percent change")


class CategoryDailyYoYResponse(BaseModel):
    """Schema for category daily YoY response."""

    category_name: str = Field(..., description="Category name")
    category_type: str = Field(
        ..., description="Type: 'spending', 'receipt', or 'tbill'"
    )
    current_fiscal_year: int = Field(..., description="Current fiscal year")
    previous_fiscal_year: int = Field(..., description="Previous fiscal year")
    comparison_mode: str = Field(
        default="fiscal_day", description="Comparison mode used"
    )
    comparison_days: int = Field(..., description="Number of days compared")
    available_from: str = Field(
        ..., description="First comparable date (ISO); totals before it are null"
    )
    data_points: list[CategoryDailyYoYDataPoint] = Field(
        default_factory=list, description="Daily YoY data points"
    )


# IRS Tax Refund Schemas


class IrsRefundComponent(BaseModel):
    """Schema for an IRS tax refund component (Individual/Business, EFT/Check)."""

    name: str = Field(
        ..., description="Component name (e.g., 'Taxes - Individual Tax Refunds (EFT)')"
    )
    tax_refund_type: str = Field(
        ..., description="The tax_refund_type value from income_tax_refunds table"
    )
    current_fytd: float = Field(..., description="Current fiscal year FYTD amount")
    previous_fytd: float = Field(..., description="Previous fiscal year FYTD amount")
    yoy_change: float = Field(..., description="Year-over-year change amount")


class IrsRefundRequest(BaseModel):
    """Schema for requesting IRS tax refund data."""

    current_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Current fiscal year"
    )
    previous_fiscal_year: int = Field(
        ..., ge=2000, le=2100, description="Previous fiscal year for Y-o-Y comparison"
    )
    comparison_mode: str = Field(
        default="fiscal_day",
        description=(
            "Comparison mode: 'fiscal_day' (Day N vs Day N) or 'calendar_date' (Dec 31 "
            "vs Dec 31)"
        ),
    )


class IrsRefundResponse(BaseModel):
    """Schema for IRS tax refund response."""

    current_fiscal_year: int = Field(..., description="Current fiscal year")
    previous_fiscal_year: int = Field(..., description="Previous fiscal year")
    current_date: str = Field(
        ..., description="Latest date with data in current fiscal year"
    )
    previous_date: str = Field(
        ..., description="Equivalent date in previous fiscal year"
    )
    comparison_mode: str = Field(
        default="fiscal_day", description="Comparison mode used"
    )
    total_current_fytd: float | None = Field(
        ...,
        description=(
            "Total IRS tax refunds for current fiscal year"
            " (null when the date is before available_from)"
        ),
    )
    total_previous_fytd: float | None = Field(
        ...,
        description=(
            "Total IRS tax refunds for previous fiscal year"
            " (null when the date is before available_from)"
        ),
    )
    total_yoy_change: float | None = Field(
        ...,
        description=(
            "Total year-over-year change (null when the date is before available_from)"
        ),
    )
    available_from: str = Field(
        ..., description="First comparable date (ISO); totals before it are null"
    )
    total_yoy_percent_change: float | None = Field(
        None, description="Total year-over-year percent change"
    )
    components: list[IrsRefundComponent] = Field(
        default_factory=list, description="Breakdown by component"
    )


# Weekly Snapshot Schemas


class SnapshotFigure(BaseModel):
    """One FYTD figure against the same business day a year earlier."""

    current: float | None = Field(..., description="FYTD on the snapshot date")
    previous: float | None = Field(
        ..., description="FYTD on the aligned previous-FY date"
    )
    change: float | None = Field(..., description="current − previous")
    percent_change: float | None = Field(..., description="change ÷ |previous| × 100")


class WeeklySnapshotRequest(BaseModel):
    """Schema for requesting one week's snapshot."""

    anchor_weekday: AnchorWeekday = Field(
        "thursday", description="Weekday the week ends on"
    )
    as_of: date | None = Field(
        None, description="Read the week on or before this date; default latest"
    )


class SnapshotCashBalance(BaseModel):
    """The TGA closing balance on the snapshot date, a week and a year earlier."""

    closing: float | None = Field(
        ..., description="On record_date; null if the statement has no balance row"
    )
    previous_week: float | None = Field(..., description="On previous_week_date")
    change_week: float | None = Field(..., description="closing − previous_week")
    year_ago: float | None = Field(
        ..., description="On previous_date (same fiscal day)"
    )
    change_year: float | None = Field(..., description="closing − year_ago")
    percent_change_year: float | None = Field(
        ..., description="change_year ÷ |year_ago| × 100"
    )


class WeeklySnapshotResponse(BaseModel):
    """One week's statement: month and fiscal year to date, against a year ago."""

    anchor_weekday: AnchorWeekday = Field(..., description="Weekday the week ends on")
    anchor_date: str = Field(..., description="The Thursday/Friday the week ends on")
    record_date: str = Field(
        ..., description="Statement used; earlier than anchor_date after a holiday"
    )
    fiscal_year: int = Field(..., description="Fiscal year of record_date")
    day_of_fiscal_year: int = Field(..., description="Business day of the fiscal year")
    previous_fiscal_year: int = Field(..., description="fiscal_year − 1")
    previous_date: str | None = Field(
        ..., description="Same day_of_fiscal_year in the previous FY"
    )
    withdrawals_mtd: float = Field(..., description="Total withdrawals, month to date")
    net_transfers_mtd: float = Field(..., description="Net transfers, month to date")
    withdrawals_fytd: SnapshotFigure
    deposits_fytd: SnapshotFigure
    net_transfers_fytd: SnapshotFigure
    withholding_fytd: SnapshotFigure
    withdrawals_10d_average: float | None = Field(
        ..., description="Mean withdrawals over the last 10 statements"
    )
    projected_monthly_withdrawals: float | None = Field(
        ..., description="withdrawals_10d_average × 20"
    )
    unemployment_10d_average: float | None = Field(
        ..., description="Mean unemployment benefits over the last 10 statements"
    )
    interest_income_fytd: SnapshotFigure
    net_customs_fytd: SnapshotFigure
    cash_balance: SnapshotCashBalance
    previous_week_date: str | None = Field(
        ..., description="Statement used for the week before"
    )
    previous_week_net_transfers_gap: float | None = Field(
        ..., description="Last week's net-transfers FYTD change from a year earlier"
    )
    net_transfers_gap_change: float | None = Field(
        ..., description="This week's net-transfers change minus last week's"
    )
    gap_change_unavailable_reason: str | None = Field(
        ..., description="Why net_transfers_gap_change is null, when it is"
    )


# Rolling Average Schemas

RollingMetric = Literal["total_withdrawals", "unemployment_benefits"]


class RollingAverageRequest(BaseModel):
    """Schema for requesting a rolling average of a daily amount."""

    metric: RollingMetric = Field(..., description="Daily amount to average")
    window: int = Field(10, ge=2, le=60, description="Statements per average")
    start_date: date | None = Field(
        None, description="First date returned; default a year before end_date"
    )
    end_date: date | None = Field(
        None, description="Last date returned; default latest"
    )


class RollingPoint(BaseModel):
    """One statement's amount and the rolling average ending on it."""

    record_date: str = Field(..., description="Statement date")
    value: float = Field(..., description="That statement's amount")
    rolling_average: float | None = Field(
        ...,
        description=(
            "Mean of the last `window` statements; null until there are that many"
        ),
    )
    projected_monthly: float | None = Field(
        ..., description="rolling_average × 20, withdrawals only"
    )


class RollingAverageResponse(BaseModel):
    """Schema for rolling average response."""

    metric: RollingMetric = Field(..., description="Daily amount averaged")
    window: int = Field(..., description="Statements per average")
    monthly_multiplier: int | None = Field(
        ..., description="Business days a month in the projection; null if none"
    )
    start_date: str = Field(..., description="First date returned")
    end_date: str = Field(..., description="Last date returned")
    points: list[RollingPoint] = Field(
        default_factory=list, description="One point per statement"
    )


# Combined Category Schemas


class CombinedTermValue(BaseModel):
    """One category inside a combined figure."""

    category_name: str = Field(..., description="Registry category name")
    sign: int = Field(..., description="1 adds the category, -1 subtracts it")
    current_fytd: float | None = Field(
        ..., description="Category FYTD on current_date; null before its coverage"
    )
    previous_fytd: float | None = Field(
        ..., description="Category FYTD on previous_date; null before its coverage"
    )


class CombinedCategory(BaseModel):
    """A figure made of several categories, with YoY change."""

    name: str = Field(..., description="Display name")
    available_from: str = Field(
        ..., description="First comparable date (ISO): the latest of its terms'"
    )
    current_fytd: float | None = Field(
        ..., description="Signed sum on current_date; null if any term is"
    )
    previous_fytd: float | None = Field(
        ..., description="Signed sum on previous_date; null if any term is"
    )
    yoy_change: float | None = Field(..., description="current − previous")
    yoy_percent_change: float | None = Field(
        ..., description="yoy_change ÷ |previous| × 100"
    )
    terms: list[CombinedTermValue] = Field(
        default_factory=list, description="The categories it is made of"
    )


class CombinedCategoriesResponse(BaseModel):
    """Schema for combined categories response."""

    current_fiscal_year: int = Field(..., description="Current fiscal year")
    previous_fiscal_year: int = Field(..., description="Previous fiscal year")
    current_date: str = Field(
        ..., description="Latest date with data in current fiscal year"
    )
    previous_date: str = Field(
        ..., description="Equivalent date in previous fiscal year"
    )
    comparison_mode: str = Field(..., description="Comparison mode used")
    categories: list[CombinedCategory] = Field(
        default_factory=list, description="The combined figures"
    )


# Cash Balance Schemas


class CashBalanceRequest(BaseModel):
    """Schema for requesting the TGA closing balance over a range."""

    start_date: date | None = Field(None, description="Default a year before end_date")
    end_date: date | None = Field(None, description="Default the latest statement")


class CashBalancePoint(BaseModel):
    """The closing balance on one statement date."""

    record_date: str = Field(..., description="Statement date")
    closing_balance: float = Field(
        ..., description="TGA closing balance, millions of dollars"
    )


class CashBalanceResponse(BaseModel):
    """Schema for cash balance response."""

    start_date: str = Field(..., description="First date requested")
    end_date: str = Field(..., description="Last date requested")
    points: list[CashBalancePoint] = Field(
        default_factory=list, description="One point per statement"
    )
