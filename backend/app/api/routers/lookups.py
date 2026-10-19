"""Option lists for the pages' pickers."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.treasury import CategoryListResponse
from app.services import lookups

router = APIRouter(
    prefix="/api/v1/lookups", tags=["lookups"], dependencies=[Depends(cache_public)]
)


@router.get("/account-types", response_model=list[str])
def get_account_types(
    cur: CursorDep,
    data_source: Annotated[
        str | None, Query(description="Filter by data source (table name)")
    ] = None,
) -> list[str]:
    """Distinct account types, optionally for one table."""
    return lookups.get_account_types(cur, data_source)


@router.get("/data-sources", response_model=list[str])
def get_data_sources() -> list[str]:
    """Every queryable table."""
    return lookups.get_data_sources()


@router.get("/fiscal-years", response_model=list[int])
def get_fiscal_years(cur: CursorDep) -> list[int]:
    """Fiscal years with data, newest first."""
    return lookups.get_fiscal_years(cur)


@router.get("/categories", response_model=CategoryListResponse)
def get_categories(cur: CursorDep) -> CategoryListResponse:
    """Deposit and withdrawal category labels."""
    return lookups.get_categories(cur)
