"""Weekly comparison of two fiscal years."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.treasury import WeeklyComparisonRequest, WeeklyComparisonResponse
from app.services import weekly

router = APIRouter(
    prefix="/api/v1/weekly", tags=["weekly"], dependencies=[Depends(cache_public)]
)


@router.get("/comparison", response_model=WeeklyComparisonResponse)
def get_comparison(
    cur: CursorDep, req: Annotated[WeeklyComparisonRequest, Query()]
) -> WeeklyComparisonResponse:
    """Net transfers FYTD on each week's anchor day (Friday by default), two FYs."""
    return weekly.get_comparison(cur, req)
