"""Wire models for agent-written SQL results."""

from typing import Any

from pydantic import BaseModel


class ColumnInfo(BaseModel):
    name: str
    type: str


class QueryResult(BaseModel):
    columns: list[ColumnInfo]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    elapsed_ms: int
