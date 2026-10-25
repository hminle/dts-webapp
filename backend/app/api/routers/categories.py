"""Major spending and receipt categories."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.treasury import (
    CategoryDailyYoYRequest,
    CategoryDailyYoYResponse,
    CombinedCategoriesResponse,
    IrsRefundRequest,
    IrsRefundResponse,
    MajorReceiptCategoriesRequest,
    MajorReceiptCategoriesResponse,
    MajorSpendingCategoriesRequest,
    MajorSpendingCategoriesResponse,
    TBillInterestRequest,
    TBillInterestResponse,
)
from app.services import categories

router = APIRouter(
    prefix="/api/v1/categories",
    tags=["categories"],
    dependencies=[Depends(cache_public)],
)


@router.get("/major-spending", response_model=MajorSpendingCategoriesResponse)
def get_major_spending(
    cur: CursorDep, req: Annotated[MajorSpendingCategoriesRequest, Query()]
) -> MajorSpendingCategoriesResponse:
    """FYTD spending of the major categories, with YoY change."""
    return categories.get_major_spending(cur, req)


@router.get("/major-receipts", response_model=MajorReceiptCategoriesResponse)
def get_major_receipts(
    cur: CursorDep, req: Annotated[MajorReceiptCategoriesRequest, Query()]
) -> MajorReceiptCategoriesResponse:
    """FYTD receipts of the major categories, with YoY change."""
    return categories.get_major_receipts(cur, req)


@router.get("/other-spending", response_model=MajorSpendingCategoriesResponse)
def get_other_spending(
    cur: CursorDep, req: Annotated[MajorSpendingCategoriesRequest, Query()]
) -> MajorSpendingCategoriesResponse:
    """FYTD spending of the other preset categories, with YoY change."""
    return categories.get_other_spending(cur, req)


@router.get("/other-receipts", response_model=MajorReceiptCategoriesResponse)
def get_other_receipts(
    cur: CursorDep, req: Annotated[MajorReceiptCategoriesRequest, Query()]
) -> MajorReceiptCategoriesResponse:
    """FYTD receipts of the other preset categories, with YoY change."""
    return categories.get_other_receipts(cur, req)


@router.get("/combined", response_model=CombinedCategoriesResponse)
def get_combined(
    cur: CursorDep, req: Annotated[MajorSpendingCategoriesRequest, Query()]
) -> CombinedCategoriesResponse:
    """Figures made of several categories, with YoY change."""
    return categories.get_combined(cur, req)


@router.get("/tbill-interest", response_model=TBillInterestResponse)
def get_tbill_interest(
    cur: CursorDep, req: Annotated[TBillInterestRequest, Query()]
) -> TBillInterestResponse:
    """T-bill interest components, with YoY change."""
    return categories.get_tbill_interest(cur, req)


@router.get("/irs-tax-refunds", response_model=IrsRefundResponse)
def get_irs_tax_refunds(
    cur: CursorDep, req: Annotated[IrsRefundRequest, Query()]
) -> IrsRefundResponse:
    """IRS tax refund components, with YoY change."""
    return categories.get_irs_tax_refunds(cur, req)


@router.get("/daily-yoy", response_model=CategoryDailyYoYResponse)
def get_daily_yoy(
    cur: CursorDep, req: Annotated[CategoryDailyYoYRequest, Query()]
) -> CategoryDailyYoYResponse:
    """One category, day by day, in two fiscal years."""
    return categories.get_daily_yoy(cur, req)
