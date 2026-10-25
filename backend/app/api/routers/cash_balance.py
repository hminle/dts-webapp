"""The Treasury General Account's closing balance."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.caching import cache_public
from app.api.deps import CursorDep
from app.schemas.treasury import CashBalanceRequest, CashBalanceResponse
from app.services import cash_balance

router = APIRouter(
    prefix="/api/v1/cash-balance",
    tags=["cash_balance"],
    dependencies=[Depends(cache_public)],
)


@router.get("/daily", response_model=CashBalanceResponse)
def get_daily(
    cur: CursorDep, req: Annotated[CashBalanceRequest, Query()]
) -> CashBalanceResponse:
    """The TGA closing balance on each statement date."""
    return cash_balance.get_daily(cur, req)
