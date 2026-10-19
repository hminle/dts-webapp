"""Wire models for the health endpoint."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    data_loaded: bool
    latest_record_date: str | None = None
