"""Wire models describing the published artifact."""

from pydantic import BaseModel


class BuildInfo(BaseModel):
    build_date: str
    latest_record_date: str
    source: str
    schema_version: str
