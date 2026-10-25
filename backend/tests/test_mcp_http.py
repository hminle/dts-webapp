"""The MCP server mounted at /api/mcp/ over stateless streamable HTTP."""

import json
from typing import Any

import httpx
import mcp.types
from fastapi.testclient import TestClient

from app.main import app

HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": mcp.types.LATEST_PROTOCOL_VERSION,
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"},
    },
}


def _message(response: httpx.Response) -> dict[str, Any]:
    # Streamable HTTP may answer with plain JSON or a one-event SSE stream.
    if response.headers["content-type"].startswith("text/event-stream"):
        [data] = [
            line.removeprefix("data: ")
            for line in response.text.splitlines()
            if line.startswith("data: ")
        ]
        return json.loads(data)
    return response.json()


def test_mcp_initialize_over_http(client: TestClient) -> None:
    response = client.post("/api/mcp/", json=INITIALIZE, headers=HEADERS)
    assert response.status_code == 200
    assert _message(response)["result"]["serverInfo"]["name"] == "dts-treasury"


def test_mcp_path_without_slash(client: TestClient) -> None:
    # Starlette redirects the bare mount path; some clients won't re-POST, so
    # docs/operations.md gives the URL with the slash.
    response = client.post(
        "/api/mcp", json=INITIALIZE, headers=HEADERS, follow_redirects=False
    )
    assert response.status_code == 307
    assert response.headers["location"].endswith("/api/mcp/")


def test_v1_routes_unchanged(client: TestClient) -> None:
    response = client.get("/api/v1/meta/stats")
    assert response.status_code == 200
    assert "Cache-Control" in response.headers


def test_unknown_api_path_still_404(client: TestClient) -> None:
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_openapi_has_no_mcp_path() -> None:
    assert not [p for p in app.openapi()["paths"] if p.startswith("/api/mcp")]
