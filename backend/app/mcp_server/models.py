"""Wire models for MCP tool results (FastMCP returns them as structured output)."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class OperationSummary(BaseModel):
    operation_id: str
    method: str
    path: str
    tag: str
    summary: str


class ParameterInfo(BaseModel):
    # FastMCP dumps results without by_alias, so the model must opt in.
    model_config = ConfigDict(serialize_by_alias=True, validate_by_name=True)

    name: str
    location: Literal["path", "query"]
    required: bool
    description: str | None
    # Named json_schema so it doesn't shadow BaseModel.schema; "schema" on the wire.
    json_schema: dict[str, Any] = Field(serialization_alias="schema")


class OperationDetail(OperationSummary):
    description: str | None
    parameters: list[ParameterInfo]
    response_schema: dict[str, Any]
    # Every component schema the parameters and response reach, by name.
    components: dict[str, dict[str, Any]]


class ApiCallResult(BaseModel):
    status: int
    # The resolved path and query string actually requested.
    path: str
    body: Any


class SkillSummary(BaseModel):
    name: str
    description: str


class Skill(SkillSummary):
    formulas: list[str]
    body: str
