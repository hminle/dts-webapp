"""Rolling averages of daily amounts."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.treasury import RollingAverageRequest, RollingAverageResponse
from app.services import rolling

router = APIRouter(
    prefix="/api/v1/rolling", tags=["rolling"], dependencies=[Depends(cache_public)]
)


@router.get("/daily", response_model=RollingAverageResponse)
def get_daily(
    cur: CursorDep, req: Annotated[RollingAverageRequest, Query()]
) -> RollingAverageResponse:
    """Each statement's amount and the mean of the last `window` statements."""
    return rolling.get_daily(cur, req)
