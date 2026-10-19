"""Liveness and data-presence check. Never cached: it describes this deployment."""

import duckdb
from fastapi import APIRouter

from app.core.duckdb import DataUnavailable, get_connection
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report that the API is up and how far its data reaches."""
    try:
        cursor = get_connection().cursor()
    except (DataUnavailable, duckdb.Error):
        # The one place a missing artifact is an answer rather than an error.
        return HealthResponse(status="ok", data_loaded=False)
    try:
        row = cursor.execute(
            "SELECT value FROM metadata WHERE key = 'latest_record_date'"
        ).fetchone()
    finally:
        cursor.close()
    return HealthResponse(
        status="ok", data_loaded=True, latest_record_date=row[0] if row else None
    )
