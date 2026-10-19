"""Daily net transfers (withdrawals minus deposits, excluding public debt)."""

from fastapi import APIRouter, Depends

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.treasury import DailyNetTransfer
from app.services import net_transfers

router = APIRouter(
    prefix="/api/v1/net-transfers",
    tags=["net_transfers"],
    dependencies=[Depends(cache_public)],
)


@router.get("/date/{date}", response_model=DailyNetTransfer)
def get_for_date(cur: CursorDep, date: str) -> DailyNetTransfer:
    """The net-transfer figures for one date."""
    return net_transfers.get_for_date(cur, date)


@router.get("/fiscal-year/{fiscal_year}", response_model=list[DailyNetTransfer])
def get_for_fiscal_year(cur: CursorDep, fiscal_year: int) -> list[DailyNetTransfer]:
    """Every day of a fiscal year, in order."""
    return net_transfers.get_for_fiscal_year(cur, fiscal_year)
