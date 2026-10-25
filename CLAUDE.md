# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this app is

A public web app for analyzing the U.S. Treasury **Daily Treasury Statement (DTS)**: daily
deposits and withdrawals of the Treasury General Account, net transfers, fiscal-year and
year-over-year comparisons, and major spending/receipt categories. It is the SaaS rebuild of
`../dts-analysis/fullstack_app` — that repo is the **reference for all financial logic**
(queries, formulas, category definitions); this repo owns the production architecture.

Every visitor sees the same public-domain Treasury data, which changes once per business day.
That one fact drives the architecture:

- **Ingestion** is a batch job (`python -m app.ingest`) that fetches from the Treasury Fiscal
  Data API and produces an immutable `treasury_data.duckdb` file. It runs daily in GitHub
  Actions and stores the file in Cloudflare R2.
- **Serving** is a read-only FastAPI app that opens that file with `read_only=True`. It never
  writes, so there is no fetch/populate UI and no write concurrency to manage.
- **Deploy = data refresh.** After ingestion uploads a new file, a Vercel Deploy Hook
  rebuilds the app; the backend build downloads the file and bundles it. Vercel's CDN cache key
  includes the deployment URL, so a new deploy also starts a fresh cache.

The build-out is planned in `docs/plans/dts-webapp/` — read its README for current status
before starting work. Until a phase lands, the layout below is the target, not the state.

## Hosting

| Piece | Where | Notes |
|-------|-------|-------|
| Frontend (Vite static build) | Vercel, service `web` (`frontend/`) | CDN-served |
| Backend (FastAPI) | Vercel, service `api` (`backend/`) | One Python function on Fluid compute; `/api/*` is rewritten to it |
| Data file | Cloudflare R2 bucket `dts-data` | `latest/treasury_data.duckdb` + dated snapshots |
| Daily ingestion + CI | GitHub Actions | `.github/workflows/ingest.yml`, `ci.yml` |

Both services live in one Vercel project via **Vercel Services** (`vercel.json` `services` +
top-level `rewrites`); the backend receives the original path (`/api/v1/...`), so frontend and
API share one origin and need no CORS. Use the **`cf`** CLI for Cloudflare (not `wrangler`) —
discover commands with `cf cli search "<task>"`; in CI it authenticates from
`CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID`. Use the `vercel` CLI for Vercel.

The Vercel Hobby plan forbids commercial use: the app must move to **Pro before any paid
feature ships**.

## Commands

```bash
scripts/dev.sh                  # backend :8000 + frontend :5173, interleaved logs, Ctrl-C stops both
scripts/dev.sh --install        # same, but uv sync + pnpm install first
scripts/dev.sh --backend-only   # or --frontend-only
```

Backend (from `backend/`, always via `uv run` — uv is the only Python package manager here;
add dependencies with `uv add <pkg>` / `uv add --dev <pkg>`, never pip):

```bash
uv sync
uv run fastapi dev                            # :8000, docs at /docs
uv run pytest                                 # full suite
uv run pytest tests/test_data_api.py::test_name -x   # single test
uv run ruff check . && uv run ruff format .   # run both before finishing a change
uv run python -m scripts.export_openapi       # regenerate docs/contracts/openapi.json
uv run python -m scripts.fetch_artifact       # download latest.duckdb from R2 into data/
uv run python -m app.ingest --db data/treasury_data.duckdb            # incremental update
uv run python -m app.ingest --db data/treasury_data.duckdb --full     # rebuild from 2005
uv run python -m app.mcp_server                # MCP server over stdio (Claude Code loads it from .mcp.json)
```

Frontend (from `frontend/`, pnpm — not npm):

```bash
pnpm dev            # :5173, proxies /api to VITE_API_TARGET (default localhost:8000)
pnpm test           # vitest run
pnpm typecheck      # tsc -b (the root tsconfig has no files; --noEmit alone checks nothing)
pnpm build          # tsc -b && vite build
pnpm gen:api        # regenerate src/lib/api/schema.d.ts from the OpenAPI snapshot
```

## The contract loop (do not skip)

`docs/contracts/openapi.json` is the committed source of truth between backend and frontend.
After **any** endpoint or schema change: `uv run python -m scripts.export_openapi` in the same
commit, then `pnpm gen:api` in the frontend. The typed client is generated from that snapshot,
so a contract break surfaces as a TypeScript error instead of a runtime bug. Router
`operation_id`s are `"{tag}_{function_name}"` (`generate_unique_id` in `app/main.py`) — renaming
a route function renames the generated client method.

## Backend architecture (`backend/`)

Layering: `app/api/routers` (HTTP, validation, cache headers) → `app/services` (all query logic)
→ DuckDB through `app/core/duckdb.py`. `app/schemas` holds the wire models. Routers take
`CursorDep` (`app/api/deps.py`) and stay thin. Every serving router is
`APIRouter(prefix="/api/v1/<area>", tags=["<area>"])`; health is `/api/health`.

- **The serving app never writes.** `app/core/duckdb.py` opens the file once with
  `read_only=True`; each request gets its own `cursor()`. No module stores a connection or a
  cursor. Anything that writes belongs in `app/ingest/`.
- **Every data endpoint is `GET`.** Query parameters (Pydantic query models via
  `Annotated[Model, Query()]`) replace the JSON bodies the reference app used — a CDN never
  caches `POST`. Data responses carry `Cache-Control` set in one place (`app/api/caching.py`). The one
  exception is the MCP mount at `/api/mcp` (`app/main.py`), which is `POST` by protocol and is
  never CDN-cached.
- **No silent fallbacks.** Unknown endpoint keys, missing tables, and failed queries raise; the
  HTTP layer maps them to 4xx/5xx. Never return an empty list to hide an error.
- **Pagination happens in SQL** (`LIMIT/OFFSET` over `UNION ALL BY NAME`), never by
  materializing a table in pandas.
- **One endpoint registry**: `app/constants/endpoints.py` maps each Treasury endpoint key to its
  API path and display name; the key is also the DuckDB table name.
- **`day_of_fiscal_year` = `DENSE_RANK() OVER (ORDER BY record_date)`** within the fiscal year
  of `deposits_withdrawals` — everywhere, including the `daily_net_transfers` table ingestion
  builds.
- **Timestamps are timezone-aware UTC** (`datetime.now(UTC)`). The U.S. federal fiscal year
  starts Oct 1 (`app/utils/fiscal.py:current_fiscal_year`).
- **Ingestion is fetch-then-swap**: it builds into a temp file, validates it, and only then
  replaces the artifact. A failed run leaves yesterday's file untouched and exits non-zero.
- **MCP server** (`app/mcp_server/`): generic tools over the same app — `list_api`/`describe_api`
  read `app.openapi()`, `call_api` calls the app in-process via `httpx.ASGITransport`, `run_query`
  goes through `app/services/sql.py`. Agent SQL runs on the shared connection, which is why
  `app/core/duckdb.py` locks it down. Build with `build_server(app)`; never import the FastAPI app
  from inside `app/mcp_server/`.

Tests run against a small seeded DuckDB file built by the real schema code
(`tests/conftest.py`); they never touch the network or the real artifact.

## Frontend architecture (`frontend/`)

React 19 + Vite + TanStack Router (file-based, `src/routes/`, `routeTree.gen.ts` is generated) +
TanStack Query + Tailwind v4 + shadcn/ui (`base-nova` style) + Recharts. `@/` aliases `src/`.
The shell, design tokens, and component layers are copied from
`../family-financial-app/frontend` — keep them in step with that app's look.

- `src/lib/api/client.ts` is the only place the app touches the network (`openapi-fetch`, typed
  from `schema.d.ts`). No axios, no bare `fetch` in components.
- `src/features/<domain>/api.ts` holds that domain's query hooks and re-exports its wire types
  from `components['schemas'][...]`; feature code imports those aliases, not the raw schema.
- Pages are thin: a route file in `src/routes/` renders a page component from
  `src/features/<domain>/`, which composes components and calls pure helpers in
  `src/features/<domain>/lib.ts` (unit-tested with Vitest).
- Components: `src/components/ui/` is shadcn (generated — prefer `pnpm dlx shadcn@latest add`),
  `src/components/reui/` is the ReUI data-grid layer, `src/components/layout/` is the sidebar
  shell (nav items in `layout/data/sidebar-data.ts`), app-specific components sit directly in
  `src/components/`.
- Design tokens live in `src/styles/globals.css` (`:root` / `.dark`) and component looks in
  `src/styles/style-nova.css`. Use token classes (`bg-card`, `text-muted-foreground`,
  `--chart-*`), never raw hex in components; the categorical series palette is
  `src/lib/chart.ts`.
- Amounts from the Treasury API are **millions of dollars** as floats; format only at display
  time through `src/lib/format.ts`.
- Formula copy lives in `features/methodology/formulas.ts`; worked-example numbers live in
  `features/methodology/worked-examples.json`, which `backend/tests/test_formula_examples.py`
  checks against the real formula code. `backend/app/mcp_server/worked-examples.json` is a copy
  the MCP skills read (`test_mcp_skills.py` enforces it). Change a formula and all three must be
  updated in the same commit.

## Conventions

- Plans live in `docs/plans/<feature>/` — a `README.md` index with a phase status table plus
  per-phase docs. Before starting a feature, check whether a plan for it already exists and keep
  its status table current as phases land. The `planner` skill owns this format.
- Project skills in `.claude/skills/` are in force: `python-style` for anything in `backend/`,
  `fastapi` for routers/schemas/deps, `shadcn` and `minimalist-ui` for frontend UI work.
- Python: type hints everywhere, Google-style docstrings, Ruff (line length 88, see
  `backend/pyproject.toml`).
- Comments explain *why* a non-obvious choice was made. Match that density — no restating what
  the code says.
- Secrets (Cloudflare token, Vercel deploy hook, R2 URLs with credentials) live in GitHub
  Actions secrets and Vercel env vars only — never in the repo, never in `.env` files that are
  committed.

## Git branches and commits

Never commit straight to `main` — branch first. Branch names are
`<type>/<kebab-case-summary>`, with the type from the conventional set:

| Type | Use for |
|------|---------|
| `feat/` | a new capability (`feat/serving-api`) |
| `fix/` | a bug fix (`fix/weekly-week-alignment`) |
| `docs/` | docs and plan files only (`docs/dts-webapp-plan`) |
| `refactor/` | restructuring with no behaviour change |
| `test/` | tests only |
| `chore/` | deps, tooling, config (`chore/bump-vite`) |

When a branch implements one phase of a plan, name it after the phase:
`feat/ingestion` for `docs/plans/dts-webapp/phase-2-ingestion.md`.

Commit messages carry **no "Generated with Claude Code" line** — not in the subject, not
in the trailers. A `Co-Authored-By:` trailer is fine; the generated-with line belongs only
in a pull request description, if anywhere.

Before any `gh` command, check which account is active — `gh auth status`. It must be
**`hminle`**; switch with `gh auth switch --user hminle`. Two accounts are configured on
this machine, and the other one (`hminlesvg`) cannot see this repo, so it fails with "Could
not resolve to a Repository" even though `git push` succeeds — pushes go over SSH with a
separate credential, so a working push says nothing about which account `gh` will use.
