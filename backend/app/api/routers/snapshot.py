"""Weekly snapshot of one statement against a year earlier."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.treasury import WeeklySnapshotRequest, WeeklySnapshotResponse
from app.services import snapshot

router = APIRouter(
    prefix="/api/v1/snapshot", tags=["snapshot"], dependencies=[Depends(cache_public)]
)


@router.get("/weekly", response_model=WeeklySnapshotResponse)
def get_weekly(
    cur: CursorDep, req: Annotated[WeeklySnapshotRequest, Query()]
) -> WeeklySnapshotResponse:
    """One week's statement: month and fiscal year to date, against a year earlier."""
    return snapshot.get_weekly(cur, req)
