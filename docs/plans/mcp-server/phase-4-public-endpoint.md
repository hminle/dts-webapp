# Phase 4: Public endpoint — ✅ Done

**Goal**: The same MCP server, served as stateless streamable HTTP at `/api/mcp` from the
existing Vercel function, so anyone can connect an agent to the public data.

Branch: `feat/mcp-public`. Depends on Phase 3. Start this phase only when the owner decides to
make the server public. Phases 1–3 are complete on their own.

## Scope

- In scope: mounting in `app/main.py`, an HTTP test, a Vercel preview check, `docs/operations.md`,
  CLAUDE.md.
- Out of scope: authentication; a separate Vercel function or project; a frontend page about
  the MCP server (a later plan, if wanted); CDN caching of MCP responses (they are `POST`).

## Implementation

### 1. `backend/app/main.py`

After the `for module in (...): app.include_router(module.router)` loop (line 57–58), append:

```python
# Mounted last so every /api/v1 route matches first. Stateless: each request
# stands alone, so any Fluid compute instance can serve it.
mcp_app = build_server(app).http_app(path="/", stateless_http=True)
# The MCP session manager starts in this lifespan, and Starlette ignores the
# lifespans of mounted apps, so the FastAPI app has to run it.
app.router.lifespan_context = mcp_app.lifespan
app.mount("/api/mcp", mcp_app)
```

Import `from app.mcp_server.server import build_server` at the top with the other `app.`
imports. `app/mcp_server/server.py` does not import `app.main` (Phase 2 Notes), so this is not
circular.

`http_app(path="/")` mounted at `/api/mcp` is the pattern from the FastMCP FastAPI docs
("path='/' since we mount at /mcp"). Mounts do not appear in `app.openapi()`, so the contract
snapshot does not change.

### 2. `backend/tests/test_mcp_http.py` (new)

Use the existing `client` fixture (`TestClient`, which runs the lifespan inside `with`).

| Test | Expect |
|---|---|
| `test_mcp_initialize_over_http` | `POST /api/mcp/` with headers `Accept: application/json, text/event-stream`, `Content-Type: application/json` and a JSON-RPC `initialize` body (`protocolVersion` from `mcp.types.LATEST_PROTOCOL_VERSION`, `capabilities: {}`, `clientInfo: {"name": "test", "version": "0"}`) → 200, and the body (JSON or a single SSE `data:` line) holds `result.serverInfo.name == "dts-treasury"` |
| `test_mcp_path_without_slash` | `POST /api/mcp` (no trailing slash) with the same request, `follow_redirects=False` → record the status. If it is 307, see Notes |
| `test_v1_routes_unchanged` | `GET /api/v1/meta/stats` → 200 and still has the `Cache-Control` header from `app/api/caching.py` |
| `test_unknown_api_path_still_404` | `GET /api/v1/nope` → 404 with FastAPI's `{"detail": "Not Found"}` |
| `test_openapi_has_no_mcp_path` | no key in `app.openapi()["paths"]` starts with `/api/mcp` |

For an end-to-end check with the real client, run a FastMCP `Client` against
`StreamableHttpTransport` pointed at a local `uv run fastapi dev` (Verification below), not in
the unit tests.

### 3. Vercel preview check

`vercel.json` needs no change: `/api/(.*)` already rewrites to the `api` service, `maxDuration`
is 30 s (`query_timeout_seconds` is 10), and the skills folder and
`app/mcp_server/worked-examples.json` are under `backend/app/`, which is bundled.

Open a PR. On its preview deployment:

1. `curl -sS -X POST "$PREVIEW/api/mcp/" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'`
   → 200 with `serverInfo.name` `dts-treasury`. If the preview has Vercel deployment protection
   on, add the `x-vercel-protection-bypass` header from the project settings.
2. `claude mcp add --transport http dts-preview "$PREVIEW/api/mcp/"`, then in Claude Code ask
   for the latest day's net transfers. It answers using `call_api` or `run_query`.
3. `get_skills("data-model")` lists all 11 tables (the `{{schema}}` placeholder ran on the
   bundled artifact).
4. Run `SELECT count(*) FROM range(100000000000) a` through `run_query` → a `ToolError` saying it
   exceeded 10s, and the function log shows no 504.

### 4. `docs/operations.md`

Add `## MCP server` after `## Rate limiting`:

- Endpoint `https://<production-domain>/api/mcp/`, stateless streamable HTTP, no auth, read-only.
- How to connect: `claude mcp add --transport http dts https://<production-domain>/api/mcp/`.
- Limits and where they live (`Settings` in `backend/app/core/config.py`, env prefix `APP_`):
  the table from phase-0 "Limits".
- MCP requests count against `api-per-ip` (300/min). An agent session makes a handful per
  question, so the limit stays as it is. If 429s show up for `/api/mcp` in Firewall → Overview,
  that is where to look first.
- To turn it off without a code change: there is none. Remove the mount in `app/main.py` and
  deploy. (Say so explicitly; no hidden flag.)

### 5. `CLAUDE.md`

In "Backend architecture", in the "Every data endpoint is `GET`" bullet, append: "The one
exception is the MCP mount at `/api/mcp` (`app/main.py`), which is `POST` by protocol and is
never CDN-cached."

## Verification

- [x] `cd backend && uv run pytest tests/test_mcp_http.py -x` — all pass.
- [x] `cd backend && uv run pytest` — full suite passes.
- [x] `cd backend && uv run ruff check . && uv run ruff format --check .` — clean.
- [x] `cd backend && uv run python -m scripts.export_openapi && git diff --exit-code ../docs/contracts/openapi.json` — no change.
- [x] Local end-to-end: `uv run fastapi dev`, then
      ```bash
      uv run python - <<'EOF'
      import asyncio
      from fastmcp import Client
      from fastmcp.client.transports import StreamableHttpTransport

      async def main() -> None:
          async with Client(StreamableHttpTransport("http://localhost:8000/api/mcp/")) as c:
              print(sorted(t.name for t in await c.list_tools()))
              print((await c.call_tool("list_api", {"query": "yoy"})).data)

      asyncio.run(main())
      EOF
      ```
      prints the five tool names and the `yoy_*` operations.
- [x] Stdio still works: the Phase 2 stdio smoke test passes unchanged.
- [x] Preview checks 1, 3 and 4 in §3 pass (check 2 needs the protection bypass; run it against production after merge).
- [ ] After merge, the same `curl` against production returns 200.

## Notes

- **Trailing slash.** Starlette's `Mount("/api/mcp")` serves `/api/mcp/`; a request to
  `/api/mcp` may get a 307 redirect, and some clients won't re-`POST` after a redirect. The docs
  and `claude mcp add` commands above use the trailing slash for that reason. If
  `test_mcp_path_without_slash` shows 307, keep the slash everywhere and say so in
  `docs/operations.md`. Do not add a second route to hide it.
- **SSE vs JSON responses.** Streamable HTTP may answer with `text/event-stream`. The tools
  return in one message, so this works on Vercel's Python runtime. If the preview shows
  buffered or broken streams, pass `json_response=True` to `http_app(...)` and record it here.
- **Cold start.** Building the server reads `app.openapi()` once at import. Compare the preview's
  cold-start time with production's; if it grows by more than 200 ms, note it here.
- **Results on landing (preview of PR #20, checked with `vercel curl`, which gets past
  deployment protection).**
  - `initialize` → 200 `text/event-stream` in 0.5 s. SSE works on Vercel's Python runtime, so
    `json_response=True` is not needed.
  - `POST /api/mcp` → 307 to `https://…/api/mcp/`. The redirect keeps https, but the slash stays
    in every documented URL.
  - `get_skills("data-model")` lists all 11 tables, so the skills folder and the worked-examples
    copy are bundled.
  - `run_query` over `range(100000000000)` → tool error "exceeded 10s" after 10.18 s, HTTP 200,
    no 504.
  - The lifespan swap works across repeated `TestClient` contexts (the full suite opens many).
  - `get_skills` returns a union (`list | Skill`), so FastMCP wraps its `structuredContent` as
    `{"result": ...}`. The FastMCP client unwraps it (`.data`); raw HTTP clients see the
    wrapper.
  - Check 2 (`claude mcp add` against the preview) is blocked by deployment protection; run it
    against production after merge.
  - Cold start was not measured separately.
