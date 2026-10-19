"""Raw Treasury rows."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.treasury import TreasuryDataList, TreasuryDataResponse
from app.services import data
from app.services.data import DataFilters

router = APIRouter(
    prefix="/api/v1/data", tags=["data"], dependencies=[Depends(cache_public)]
)


@router.get("", response_model=TreasuryDataList)
def list_data(
    cur: CursorDep,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=1000, description="Records per page")
    ] = 50,
    data_source: Annotated[
        str | None, Query(description="Filter by data source (table name)")
    ] = None,
    account_type: Annotated[
        str | None, Query(description="Filter by account type")
    ] = None,
    fiscal_year: Annotated[
        int | None, Query(description="Filter by fiscal year")
    ] = None,
    start_date: Annotated[
        str | None, Query(description="Start date (YYYY-MM-DD)")
    ] = None,
    end_date: Annotated[str | None, Query(description="End date (YYYY-MM-DD)")] = None,
) -> TreasuryDataList:
    """One page of rows, newest first, across all tables or one."""
    filters = DataFilters(data_source, account_type, fiscal_year, start_date, end_date)
    return data.list_data(cur, filters, page, page_size)


@router.get("/date/{date}", response_model=list[TreasuryDataResponse])
def get_by_date(
    cur: CursorDep,
    date: str,
    data_source: Annotated[
        str | None, Query(description="Filter by data source (table name)")
    ] = None,
) -> list[dict[str, Any]]:
    """Every row for one date."""
    return data.get_data_by_date(cur, date, data_source)
