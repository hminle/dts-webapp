"""Year-over-year comparisons."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.treasury import (
    YoYCategoryComparisonRequest,
    YoYCategoryComparisonResponse,
    YoYDailyComparisonRequest,
    YoYDailyComparisonResponse,
)
from app.services import yoy

router = APIRouter(
    prefix="/api/v1/yoy", tags=["yoy"], dependencies=[Depends(cache_public)]
)


@router.get("/category-comparison", response_model=YoYCategoryComparisonResponse)
def get_category_comparison(
    cur: CursorDep, req: Annotated[YoYCategoryComparisonRequest, Query()]
) -> YoYCategoryComparisonResponse:
    """FYTD amounts of selected categories in two fiscal years.

    Pass several categories as repeated keys:
    ``?category_descriptions=A&category_descriptions=B``.
    """
    return yoy.get_category_comparison(cur, req)


@router.get("/daily-comparison", response_model=YoYDailyComparisonResponse)
def get_daily_comparison(
    cur: CursorDep, req: Annotated[YoYDailyComparisonRequest, Query()]
) -> YoYDailyComparisonResponse:
    """One metric, day by day, in two fiscal years."""
    return yoy.get_daily_comparison(cur, req)
