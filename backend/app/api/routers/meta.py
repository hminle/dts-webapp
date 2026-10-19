"""Facts about the published artifact."""

from fastapi import APIRouter, Depends

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.meta import BuildInfo
from app.schemas.treasury import DatabaseStats
from app.services import meta

router = APIRouter(
    prefix="/api/v1/meta", tags=["meta"], dependencies=[Depends(cache_public)]
)


@router.get("/stats", response_model=DatabaseStats)
def get_stats(cur: CursorDep) -> DatabaseStats:
    """Record count, date range and dimensions across the endpoint tables."""
    return meta.get_stats(cur)


@router.get("/record-counts", response_model=dict[str, int])
def get_record_counts(cur: CursorDep) -> dict[str, int]:
    """Row count per endpoint table."""
    return meta.get_record_counts(cur)


@router.get("/record-counts-by-year", response_model=dict[int, int])
def get_record_counts_by_year(cur: CursorDep) -> dict[int, int]:
    """Rows per fiscal year across endpoint tables, newest first."""
    return meta.get_record_counts_by_year(cur)


@router.get("/build", response_model=BuildInfo)
def get_build(cur: CursorDep) -> BuildInfo:
    """When this artifact was built and how far its data reaches."""
    return meta.get_build_info(cur)
