"""Liveness and data-presence check."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report that the API is up and whether the data artifact is present."""
    return HealthResponse(status="ok", data_loaded=get_settings().duckdb_path.exists())
