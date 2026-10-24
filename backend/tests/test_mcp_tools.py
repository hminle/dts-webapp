"""The MCP tools, called through an in-memory FastMCP client on the seeded DB."""

from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from app.core.config import get_settings
from app.core.duckdb import get_connection, reset_connection_for_tests
from app.services import meta


async def test_tool_names(mcp_client: Client) -> None:
    names = {t.name for t in await mcp_client.list_tools()}
    assert names == {"list_api", "describe_api", "call_api", "run_query"}


async def test_tools_are_read_only(mcp_client: Client) -> None:
    for tool in await mcp_client.list_tools():
        assert tool.annotations.read_only_hint is True


async def test_call_api_matches_service(mcp_client: Client) -> None:
    result = await mcp_client.call_tool("call_api", {"operation_id": "meta_get_stats"})
    assert result.data.status == 200
    expected = meta.get_stats(get_connection().cursor()).model_dump(mode="json")
    assert result.data.body == expected


async def test_call_api_path_param(mcp_client: Client) -> None:
    result = await mcp_client.call_tool(
        "call_api",
        {
            "operation_id": "net_transfers_get_for_date",
            "params": {"date": "2025-10-10"},
        },
    )
    assert result.data.status == 200
    assert result.data.path == "/api/v1/net-transfers/date/2025-10-10"


async def test_call_api_unknown_param(mcp_client: Client) -> None:
    with pytest.raises(ToolError, match="does not take"):
        await mcp_client.call_tool(
            "call_api", {"operation_id": "data_list_data", "params": {"nope": 1}}
        )


async def test_call_api_maps_4xx(mcp_client: Client) -> None:
    with pytest.raises(ToolError, match="400.*Unknown data source"):
        await mcp_client.call_tool(
            "call_api",
            {"operation_id": "data_list_data", "params": {"data_source": "nope"}},
        )


async def test_call_api_health_not_callable(mcp_client: Client) -> None:
    with pytest.raises(ToolError, match="Unknown operation"):
        await mcp_client.call_tool("call_api", {"operation_id": "health_health"})


async def test_call_api_byte_cap(
    mcp_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "mcp_max_response_bytes", 100)
    with pytest.raises(ToolError, match="over the 100-byte limit"):
        await mcp_client.call_tool("call_api", {"operation_id": "data_list_data"})


async def test_run_query_rows(mcp_client: Client) -> None:
    result = await mcp_client.call_tool(
        "run_query", {"sql": "SELECT count(*) AS n FROM metadata"}
    )
    assert result.data.columns[0].name == "n"
    assert result.data.rows == [[4]]


async def test_run_query_rejects_write(mcp_client: Client) -> None:
    with pytest.raises(ToolError, match="Only SELECT"):
        await mcp_client.call_tool(
            "run_query", {"sql": "INSERT INTO metadata VALUES ('a', 'b', now())"}
        )


async def test_run_query_byte_cap(
    mcp_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "mcp_max_response_bytes", 100)
    with pytest.raises(ToolError, match="Select fewer columns"):
        await mcp_client.call_tool(
            "run_query", {"sql": "SELECT * FROM deposits_withdrawals"}
        )


async def test_run_query_no_artifact(
    mcp_client: Client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_DUCKDB_PATH", str(tmp_path / "missing.duckdb"))
    get_settings.cache_clear()
    reset_connection_for_tests()
    with pytest.raises(ToolError, match="not loaded"):
        await mcp_client.call_tool("run_query", {"sql": "SELECT 1"})
