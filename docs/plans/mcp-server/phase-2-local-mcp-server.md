# Phase 2: Local MCP server — ⬜ Not Started

**Goal**: A FastMCP server with `list_api`, `describe_api`, `call_api` and `run_query` that
Claude Code starts over stdio from `.mcp.json` and uses against the local artifact.

Branch: `feat/mcp-server`. Depends on Phase 1 (`app.services.sql.run_select`).

## Scope

- In scope: dependencies, the `app/mcp_server/` package, four tools, the stdio entrypoint,
  `.mcp.json`, tests, CLAUDE.md.
- Out of scope: `get_skills` and the skills folder (Phase 3); HTTP transport and mounting
  (Phase 4); any change to routers, services, or `docs/contracts/openapi.json`.

## Implementation

### 1. Dependencies (`backend/`)

```bash
uv add "fastmcp>=4.1.3,<5" "httpx>=0.28.1"
uv add --dev pytest-asyncio
```

`httpx` moves from the `dev` group to the main dependencies because `call_api` imports it at
runtime. Remove the `"httpx>=0.28.1"` line from `[dependency-groups].dev` by hand if `uv add`
leaves it there. Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]`. The existing tests
are all sync, so auto mode does not change them.

### 2. `backend/app/mcp_server/models.py` (new)

Wire models for tool results (FastMCP turns them into structured output):

```python
class OperationSummary(BaseModel):
    operation_id: str
    method: str          # always "GET" today
    path: str            # "/api/v1/net-transfers/date/{date}"
    tag: str
    summary: str

class ParameterInfo(BaseModel):
    name: str
    location: Literal["path", "query"]
    required: bool
    description: str | None
    json_schema: dict[str, Any] = Field(serialization_alias="schema")

class OperationDetail(OperationSummary):
    description: str | None
    parameters: list[ParameterInfo]
    response_schema: dict[str, Any]
    components: dict[str, dict[str, Any]]  # every $ref the response reaches, by name

class ApiCallResult(BaseModel):
    status: int
    path: str            # resolved path + query string actually requested
    body: Any
```

`json_schema` avoids shadowing `BaseModel.schema`; the alias keeps the wire name `schema`.

### 3. `backend/app/mcp_server/openapi_catalog.py` (new)

Pure functions over the spec dict from `api.openapi()`. No FastMCP import here, so it is unit
tested without a client.

```python
class CatalogError(ValueError):
    """An unknown operation, or parameters that don't fit it."""

def list_operations(spec: dict, query: str | None = None) -> list[OperationSummary]
def describe_operation(spec: dict, operation_id: str) -> OperationDetail
def build_request_path(spec: dict, operation_id: str, params: dict[str, Any]) -> str
```

Rules:

- **Callable operations** are `get` entries whose path starts with `/api/v1/`. `/api/health`
  is excluded everywhere (it says nothing about data). Sort by `path`.
- `query` matches when `query.lower()` is a substring of `operation_id`, `path` or `summary`
  (each lowercased). `None` or `""` → all operations.
- Unknown `operation_id` → `CatalogError(f"Unknown operation {id!r}. Call list_api to see
  the operation ids.")`.
- `describe_operation`: `parameters` from the operation's `parameters` list (`in` →
  `location`). `response_schema` = `responses["200"]["content"]["application/json"]["schema"]`.
  `components`: walk `response_schema` **and** every parameter schema, collect each
  `"$ref": "#/components/schemas/<Name>"`, add `spec["components"]["schemas"][Name]`, and walk
  that too until no new names appear (guard against cycles with a `seen` set).
- `build_request_path`:
  1. Unknown keys in `params` → `CatalogError(f"{op} does not take {sorted(unknown)}. It
     takes: {sorted(accepted)}.")`. This check is required, because FastAPI silently ignores
     unknown query parameters and the agent would get unfiltered data.
  2. Missing required parameters → `CatalogError(f"{op} requires {sorted(missing)}.")`.
  3. Path parameters: replace `{name}` with `urllib.parse.quote(str(value), safe="")`.
  4. Query parameters: drop keys whose value is `None`; encode each value with a private
     helper `_encode_value(value)` that turns `bool` into `"true"`/`"false"` (check `bool`
     before `int`) and leaves lists for `urlencode(..., doseq=True)`.
  5. Return `path` or `f"{path}?{urlencode(query, doseq=True)}"`.

### 4. `backend/app/mcp_server/server.py` (new)

```python
READ_ONLY = {"readOnlyHint": True, "openWorldHint": False}

def build_server(api: FastAPI) -> FastMCP:
    """Build the MCP server over ``api``, the FastAPI app it describes and calls."""
```

Inside, `mcp = FastMCP("dts-treasury", instructions=INSTRUCTIONS)` where the module constant
`INSTRUCTIONS` (Phase 3 rewrites it) is:

> U.S. Treasury Daily Treasury Statement data (public domain), refreshed once per business
> day. Amounts are millions of U.S. dollars. The fiscal year starts October 1. Use list_api
> and describe_api to find an endpoint, then call_api. Use run_query (DuckDB SQL, one SELECT)
> for anything the API doesn't answer; run "SHOW TABLES" and "DESCRIBE <table>" first.

`spec = api.openapi()` once at build time (FastAPI caches it; the routes don't change at runtime).

Tools. Each docstring is what the agent reads, so write them for an agent: what the tool does,
when to use it, one example call. Every one is decorated `@mcp.tool(annotations=READ_ONLY)`.

| Tool | Signature | Body |
|---|---|---|
| `list_api` | `def list_api(query: str \| None = None) -> list[OperationSummary]` | `list_operations(spec, query)` |
| `describe_api` | `def describe_api(operation_id: str) -> OperationDetail` | `describe_operation(...)`; `CatalogError` → `ToolError(str(exc))` |
| `call_api` | `async def call_api(operation_id: str, params: dict[str, Any] \| None = None) -> ApiCallResult` | see below |
| `run_query` | `async def run_query(sql: str, max_rows: int \| None = None) -> QueryResult` | see below |

`call_api`:

1. `path = build_request_path(spec, operation_id, params or {})` (`CatalogError` → `ToolError`).
2. `async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://dts.internal") as client:`
   `response = await client.get(path)`. The base URL is never resolved; ASGITransport hands the
   request straight to the app.
3. `cap = get_settings().mcp_max_response_bytes`. `len(response.content) > cap` →
   `ToolError(f"Response is {n} bytes, over the {cap}-byte limit. Narrow it: a smaller
   page_size, a date range, or run_query with GROUP BY.")`.
4. `response.status_code >= 400` → `ToolError(f"{status} from {path}: {detail}")`, where
   `detail` is `response.json().get("detail")` if the body is a JSON object, else
   `response.text[:500]`.
5. Return `ApiCallResult(status=..., path=path, body=response.json())`.

`run_query`:

1. Define an inner sync function `_run() -> QueryResult` that opens
   `cur = get_connection().cursor()`, returns `run_select(cur, sql, max_rows)`, and closes the
   cursor in `finally`.
2. `result = await anyio.to_thread.run_sync(_run)`. Running it in a worker thread keeps a
   10-second query off the event loop, which matters once Phase 4 serves HTTP. Do not rely on
   FastMCP's handling of sync tools.
3. `QueryRejected` (covers `QueryTimeout`, `QueryBusy`) → `ToolError(str(exc))`.
   `DataUnavailable` → `ToolError("Data is not loaded yet. Locally: cd backend && uv run python
   -m scripts.fetch_artifact")`.
4. `len(result.model_dump_json()) > cap` → `ToolError(f"Result is {n} bytes, over the
   {cap}-byte limit. Select fewer columns or lower max_rows.")`.
5. Return `result`.

Raise with `raise ToolError(...) from exc` everywhere so Sentry keeps the cause.

### 5. `backend/app/mcp_server/__init__.py` and `__main__.py` (new)

`__init__.py`: a one-line docstring, `"""MCP server: generic tools over the DTS API and artifact."""`.

`__main__.py`:

```python
"""Run the MCP server over stdio: ``uv run python -m app.mcp_server``."""

from app.main import app
from app.mcp_server.server import build_server


def main() -> None:
    build_server(app).run()


if __name__ == "__main__":
    main()
```

`run()` with no arguments is stdio. Nothing on this import path may write to stdout, because
in stdio mode stdout carries the protocol.

### 6. `backend/tests/conftest.py`

Add, below the `empty_client` fixture:

```python
@pytest.fixture
async def mcp_client(
    seeded_db: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[Client]:
    monkeypatch.setenv("APP_DUCKDB_PATH", str(seeded_db))
    get_settings.cache_clear()
    reset_connection_for_tests()
    async with Client(build_server(app)) as client:
        yield client
    reset_connection_for_tests()
    get_settings.cache_clear()
```

Imports: `from collections.abc import AsyncIterator`, `from fastmcp import Client`,
`from app.mcp_server.server import build_server`.

### 7. Tests

`backend/tests/test_mcp_catalog.py` (sync, uses `spec = app.openapi()`):

| Test | Expect |
|---|---|
| `test_lists_every_v1_get_operation` | 20 operations; all `method == "GET"`; none has path `/api/health`; sorted by path |
| `test_query_filters_case_insensitively` | `query="NET-TRANSFERS"` → exactly the two `net_transfers_*` ids |
| `test_query_matches_summary` | pick a word from one operation's summary in the spec; that operation is in the result |
| `test_describe_path_parameter` | `net_transfers_get_for_date` has one parameter `date`, `location == "path"`, `required` |
| `test_describe_inlines_refs` | for `net_transfers_get_for_date`, `"DailyNetTransfer" in detail.components`; no `$ref` in the result points at a name missing from `components` |
| `test_describe_unknown_operation` | `CatalogError` whose message names `list_api` |
| `test_build_path_substitutes_path_params` | `net_transfers_get_for_date`, `{"date": "2025-10-10"}` → `/api/v1/net-transfers/date/2025-10-10` |
| `test_build_path_encodes_query` | `data_list_data`, `{"page_size": 5, "data_source": "deposits_withdrawals", "fiscal_year": None}` → path has `page_size=5&data_source=deposits_withdrawals` and no `fiscal_year` |
| `test_build_path_lowercases_bools` | find any operation with a boolean query param in the spec; if none exists, test `_encode_value(True) == "true"` on the private helper instead |
| `test_build_path_rejects_unknown_param` | `CatalogError` whose message lists the accepted names |
| `test_build_path_requires_path_param` | `net_transfers_get_for_date`, `{}` → `CatalogError` mentioning `date` |

`backend/tests/test_mcp_tools.py` (async, uses `mcp_client`; `ToolError` from
`fastmcp.exceptions`, which the client raises for an error result):

| Test | Expect |
|---|---|
| `test_tool_names` | `{t.name for t in await mcp_client.list_tools()} == {"list_api", "describe_api", "call_api", "run_query"}` |
| `test_tools_are_read_only` | every tool's `annotations.readOnlyHint is True` |
| `test_call_api_matches_service` | `call_api("meta_get_stats")` → `.data` `status == 200` and `body == meta.get_stats(get_connection().cursor()).model_dump(mode="json")` |
| `test_call_api_path_param` | `call_api("net_transfers_get_for_date", {"date": "2025-10-10"})` → status 200 |
| `test_call_api_unknown_param` | `call_api("data_list_data", {"nope": 1})` → `ToolError` |
| `test_call_api_maps_4xx` | `call_api("data_list_data", {"data_source": "nope"})` → `ToolError` matching `"400"` and `"Unknown data source"` |
| `test_call_api_health_not_callable` | `call_api("health_health")` → `ToolError` "Unknown operation" |
| `test_call_api_byte_cap` | monkeypatch `get_settings().mcp_max_response_bytes` to `100`; `call_api("data_list_data")` → `ToolError` "over the 100-byte limit" |
| `test_run_query_rows` | `run_query("SELECT count(*) AS n FROM metadata")` → `columns[0].name == "n"`, `rows == [[4]]` |
| `test_run_query_rejects_write` | `INSERT ...` → `ToolError` "Only SELECT" |
| `test_run_query_byte_cap` | cap `100`; `SELECT * FROM deposits_withdrawals` → `ToolError` "Select fewer columns" |
| `test_run_query_no_artifact` | inside the test, point `APP_DUCKDB_PATH` at `tmp_path / "missing.duckdb"`, clear settings, reset the connection; `run_query("SELECT 1")` → `ToolError` "not loaded" |

### 8. `.mcp.json` (repo root, new)

```json
{
  "mcpServers": {
    "dts": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "backend", "python", "-m", "app.mcp_server"]
    }
  }
}
```

`--directory backend` is relative to where Claude Code starts, which is the repo root. Claude
Code asks once before it trusts a project `.mcp.json`.

### 9. `CLAUDE.md`

- In the backend Commands block, after the `--full` ingest line, add:
  `uv run python -m app.mcp_server                # MCP server over stdio (Claude Code loads it from .mcp.json)`
- In "Backend architecture", add one bullet after "Ingestion is fetch-then-swap":
  `- **MCP server** (`app/mcp_server/`): generic tools over the same app — `list_api`/`describe_api` read `app.openapi()`, `call_api` calls the app in-process via `httpx.ASGITransport`, `run_query` goes through `app/services/sql.py`. Agent SQL runs on the shared connection, which is why `app/core/duckdb.py` locks it down. Build with `build_server(app)`; never import the FastAPI app from inside `app/mcp_server/`.`

## Verification

- [ ] `cd backend && uv run pytest tests/test_mcp_catalog.py tests/test_mcp_tools.py -x` — all pass.
- [ ] `cd backend && uv run pytest` — full suite passes.
- [ ] `cd backend && uv run ruff check . && uv run ruff format --check .` — clean.
- [ ] `git diff --exit-code docs/contracts/openapi.json` — no change.
- [ ] Stdio smoke test against the real artifact (from `backend/`; fetch it first if missing):
      ```bash
      uv run python - <<'EOF'
      import asyncio
      from fastmcp import Client
      from fastmcp.client.transports import StdioTransport

      async def main() -> None:
          t = StdioTransport(command="uv", args=["run", "python", "-m", "app.mcp_server"])
          async with Client(t) as c:
              print(sorted(x.name for x in await c.list_tools()))
              r = await c.call_tool("run_query", {"sql": "SELECT max(record_date) AS d FROM deposits_withdrawals"})
              print(r.data)

      asyncio.run(main())
      EOF
      ```
      prints the four tool names and a `QueryResult` whose one row is the latest business day.
- [ ] In Claude Code at the repo root: `/mcp` lists `dts` as connected with 4 tools. Asking
      "what was the TGA net transfer on the latest day?" makes the agent use
      `list_api` → `call_api` (or `run_query`) and answer with a dollar figure in millions.

## Notes

- `build_server` takes the app as an argument; `server.py` must not `import app.main`. Phase 4
  builds the server inside `app/main.py`, and an import from the other side would be circular.
- If a FastMCP 4.x release renames `annotations` keys or the `Client` error type, follow the
  installed version's docs and record the difference here.
