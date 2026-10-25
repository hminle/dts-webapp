"""The FastMCP server: generic tools over the API and the artifact.

``build_server`` takes the FastAPI app as an argument instead of importing
``app.main``, because ``app.main`` builds this server once it is mounted.
"""

from typing import Any

import anyio
import httpx
from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from app.core.config import get_settings
from app.core.duckdb import DataUnavailable, get_connection
from app.mcp_server import skills
from app.mcp_server.models import (
    ApiCallResult,
    OperationDetail,
    OperationSummary,
    Skill,
    SkillSummary,
)
from app.mcp_server.openapi_catalog import (
    CatalogError,
    build_request_path,
    describe_operation,
    list_operations,
)
from app.schemas.sql import QueryResult
from app.services import sql as sql_service

INSTRUCTIONS = (
    "U.S. Treasury Daily Treasury Statement data (public domain), refreshed once per "
    "business day. Amounts are millions of U.S. dollars. The fiscal year starts "
    'October 1. Start with get_skills("start-here"): it says which tool to use for '
    "which question. Read the matching skill before computing a figure yourself, so "
    "your numbers match the app's."
)

READ_ONLY = {"readOnlyHint": True, "openWorldHint": False}


def build_server(api: FastAPI) -> FastMCP:
    """Build the MCP server over ``api``, the FastAPI app it describes and calls."""
    mcp = FastMCP("dts-treasury", instructions=INSTRUCTIONS)
    # The routes are fixed once the app is built, so read the spec once.
    spec = api.openapi()

    @mcp.tool(annotations=READ_ONLY)
    def list_api(query: str | None = None) -> list[OperationSummary]:
        """List the API operations you can call with call_api.

        Pass a word to filter by operation id, path or summary, case-insensitively.
        Example: list_api(query="yoy").
        """
        return list_operations(spec, query)

    @mcp.tool(annotations=READ_ONLY)
    def describe_api(operation_id: str) -> OperationDetail:
        """Show one operation's parameters and response schema before calling it.

        Example: describe_api(operation_id="net_transfers_get_for_date").
        """
        try:
            return describe_operation(spec, operation_id)
        except CatalogError as exc:
            raise ToolError(str(exc)) from exc

    @mcp.tool(annotations=READ_ONLY)
    async def call_api(
        operation_id: str, params: dict[str, Any] | None = None
    ) -> ApiCallResult:
        """Call one API operation and return its JSON body.

        params holds path and query parameters by name, exactly as describe_api
        lists them. Example: call_api(operation_id="net_transfers_get_for_date",
        params={"date": "2025-10-10"}).
        """
        try:
            path = build_request_path(spec, operation_id, params or {})
        except CatalogError as exc:
            raise ToolError(str(exc)) from exc
        # The base URL is never resolved: ASGITransport hands the request
        # straight to the app in this process.
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api), base_url="http://dts.internal"
        ) as client:
            response = await client.get(path)

        cap = get_settings().mcp_max_response_bytes
        size = len(response.content)
        if size > cap:
            raise ToolError(
                f"Response is {size} bytes, over the {cap}-byte limit. Narrow it: a "
                "smaller page_size, a date range, or run_query with GROUP BY."
            )
        if response.status_code >= 400:
            raise ToolError(f"{response.status_code} from {path}: {_detail(response)}")
        return ApiCallResult(
            status=response.status_code, path=path, body=response.json()
        )

    @mcp.tool(annotations=READ_ONLY)
    async def run_query(sql: str, max_rows: int | None = None) -> QueryResult:
        """Run one read-only DuckDB SELECT against the Treasury tables.

        Use it for questions the API doesn't answer. Start with "SHOW TABLES" and
        "DESCRIBE <table>". Returns 200 rows unless max_rows says otherwise (at
        most 2000); truncated is true when rows were cut off. Example:
        run_query(sql="SELECT max(record_date) FROM deposits_withdrawals").
        """

        def _run() -> QueryResult:
            cur = get_connection().cursor()
            try:
                return sql_service.run_select(cur, sql, max_rows)
            finally:
                cur.close()

        # A worker thread keeps a long query off the event loop, which matters
        # once the server also answers HTTP.
        try:
            result = await anyio.to_thread.run_sync(_run)
        except sql_service.QueryRejected as exc:
            raise ToolError(str(exc)) from exc
        except DataUnavailable as exc:
            raise ToolError(
                "Data is not loaded yet. Locally: cd backend && uv run python -m "
                "scripts.fetch_artifact"
            ) from exc

        cap = get_settings().mcp_max_response_bytes
        size = len(result.model_dump_json())
        if size > cap:
            raise ToolError(
                f"Result is {size} bytes, over the {cap}-byte limit. Select fewer "
                "columns or lower max_rows."
            )
        return result

    @mcp.tool(annotations=READ_ONLY)
    async def get_skills(name: str | None = None) -> list[SkillSummary] | Skill:
        """Read a methodology guide: how the app computes a figure, with SQL.

        Without a name, lists the guides. Start with get_skills(name="start-here").
        """
        try:
            loaded = skills.load_skills()
        except skills.SkillError as exc:
            raise ToolError(str(exc)) from exc
        if name is None:
            return [
                SkillSummary(name=s.name, description=s.description)
                for s in loaded.values()
            ]
        if name not in loaded:
            raise ToolError(f"No skill {name!r}. Available: {', '.join(loaded)}.")
        skill = loaded[name]

        def _render() -> str:
            cur = get_connection().cursor()
            try:
                return skills.render(skill.body, cur)
            finally:
                cur.close()

        # {{schema}} runs a query, so keep it off the event loop like run_query.
        try:
            body = await anyio.to_thread.run_sync(_render)
        except (skills.SkillError, sql_service.QueryRejected) as exc:
            raise ToolError(str(exc)) from exc
        except DataUnavailable as exc:
            raise ToolError(
                "Data is not loaded yet. Locally: cd backend && uv run python -m "
                "scripts.fetch_artifact"
            ) from exc
        return Skill(
            name=skill.name,
            description=skill.description,
            formulas=list(skill.formulas),
            body=body,
        )

    return mcp


def _detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text[:500]
    if isinstance(body, dict) and "detail" in body:
        return str(body["detail"])
    return response.text[:500]
