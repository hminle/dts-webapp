# Phase 1: Scaffold & First Deploy — ⬜ Not Started

**Goal**: The monorepo skeleton exists with FAM's structure, design tokens, and sidebar shell,
and a deployment on Vercel Services serves the shell at `/` and `GET /api/health` from FastAPI.

## Scope

- In scope: repo skeleton, backend skeleton (uv, FastAPI, settings, health, OpenAPI export,
  build-time artifact download script), frontend skeleton copied from FAM with the new sidebar
  and placeholder routes, `vercel.json` with two services, linking the Vercel project to the
  GitHub repo, first production deploy.
- Out of scope: any DuckDB schema or query (Phases 2–3), R2 bucket (Phase 2), real pages
  (Phases 5–7), GitHub Actions (Phase 4).

Branch: `feat/scaffold-deploy`.

## Implementation

`FAM` = `/home/hminle/gitrepos/personal-projects/family-financial-app`. Run every command from
the repo root unless a `cd` is shown.

### 1. Root files

- `.gitignore`:

  ```gitignore
  .DS_Store
  .env
  .env.*
  .vercel/
  __pycache__/
  *.pyc
  ```

- `scripts/dev.sh`: `cp $FAM/scripts/dev.sh scripts/dev.sh && chmod +x scripts/dev.sh`.
  No edits — it already starts `uv run fastapi dev` + `pnpm dev` and polls `/api/health`.
- `README.md`: replace the one-line body with: one paragraph on what the app is (copy the
  first paragraph of `CLAUDE.md` "What this app is"), then a "Quickstart" block
  (`scripts/dev.sh --install`, open `http://localhost:5173`), then "See `CLAUDE.md` and
  `docs/plans/dts-webapp/`".

### 2. Backend skeleton (`backend/`)

```bash
mkdir -p backend && cd backend
uv init --app --no-readme --python 3.12 --name dts-webapp-backend .
rm -f main.py hello.py            # uv init's sample entrypoint, if created
uv add "fastapi[standard]" pydantic-settings duckdb pandas
uv add --dev ruff pytest httpx
```

`duckdb` and `pandas` are added now (unused until Phase 2/3) so the Phase 2 cold-start
measurement runs against the real bundle size.

Then make `backend/pyproject.toml` contain, in addition to what uv wrote (`[project]`,
dependencies, `[dependency-groups] dev`):

```toml
[tool.fastapi]
entrypoint = "app.main:app"

[tool.vercel]
entrypoint = "app.main:app"

[tool.vercel.scripts]
# Runs on Vercel after dependency install: downloads the data artifact into data/
# so it is bundled with the function (deploy = data refresh).
build = "python -m scripts.fetch_artifact"

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

Files:

- `backend/.python-version`: `3.12`
- `backend/.gitignore`: `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `data/*.duckdb`,
  `data/*.duckdb.wal`, `data/*.download`, `data/*.building.duckdb`
- `backend/data/.gitkeep`: empty.
- `backend/README.md`: commands block copied from the Backend section of `CLAUDE.md`.
- `backend/app/__init__.py`, `backend/app/core/__init__.py`, `backend/app/api/__init__.py`,
  `backend/app/api/routers/__init__.py`, `backend/app/schemas/__init__.py`,
  `backend/scripts/__init__.py`, `backend/tests/__init__.py`: empty.
- `backend/app/core/config.py`:

  ```python
  """Application settings loaded from the environment (prefix ``APP_``)."""

  from functools import lru_cache
  from pathlib import Path

  from pydantic_settings import BaseSettings, SettingsConfigDict

  # Resolved from this file, not the working directory: on Vercel the cwd is the
  # project base, which is not guaranteed to be backend/.
  BACKEND_DIR = Path(__file__).resolve().parents[2]


  class Settings(BaseSettings):
      model_config = SettingsConfigDict(env_prefix="APP_")

      duckdb_path: Path = BACKEND_DIR / "data" / "treasury_data.duckdb"
      artifact_url: str | None = None


  @lru_cache
  def get_settings() -> Settings:
      return Settings()
  ```

  No CORS setting: production is same-origin (Vercel rewrites) and dev goes through Vite's
  `/api` proxy, so the browser never makes a cross-origin call.

- `backend/app/schemas/health.py`:

  ```python
  class HealthResponse(BaseModel):
      status: Literal["ok"]
      data_loaded: bool
  ```

- `backend/app/api/routers/health.py`: `router = APIRouter(prefix="/api", tags=["health"])`;
  `@router.get("/health", response_model=HealthResponse) def health() -> HealthResponse`
  returning `status="ok"`, `data_loaded=get_settings().duckdb_path.exists()`.
- `backend/app/main.py`:

  ```python
  def generate_unique_id(route: APIRoute) -> str:
      """Stable, readable operation ids so the generated TS client stays clean."""
      return f"{route.tags[0]}_{route.name}"


  app = FastAPI(
      title="DTS Analysis API",
      generate_unique_id_function=generate_unique_id,
      # Under /api so Vercel's /api/* rewrite reaches them; /docs would hit the
      # frontend service.
      docs_url="/api/docs",
      redoc_url=None,
      openapi_url="/api/openapi.json",
  )
  app.include_router(health.router)
  ```

- `backend/scripts/export_openapi.py`: copy `FAM/backend/scripts/export_openapi.py` verbatim
  (it writes `../docs/contracts/openapi.json` relative to `backend/`).
- `backend/scripts/fetch_artifact.py` — `main() -> int`, run as `python -m scripts.fetch_artifact`:
  1. `url = get_settings().artifact_url`. If `None`: print
     `fetch_artifact: APP_ARTIFACT_URL not set, skipping download` and return `0`
     (the deploy works without data; `/api/health` reports `data_loaded: false`).
  2. Download with `urllib.request.urlopen(url, timeout=120)` streaming via
     `shutil.copyfileobj` into `duckdb_path.with_suffix(".download")` (create the parent dir).
  3. Validate: `duckdb.connect(str(tmp), read_only=True)` then
     `SELECT value FROM metadata WHERE key = 'latest_record_date'` must return one row. Any
     exception or missing row → print the reason to stderr, delete the temp file, return `1`
     (fails the Vercel build, so the previous deployment stays live).
  4. `os.replace(tmp, duckdb_path)`; print
     `fetch_artifact: downloaded <bytes> bytes, latest_record_date=<value>`; return `0`.
  End the module with `if __name__ == "__main__": raise SystemExit(main())`.
- `backend/tests/conftest.py`: one fixture `client` → `TestClient(app)` (from
  `fastapi.testclient`) used as a context manager.
- `backend/tests/test_health.py`: `GET /api/health` → 200, body
  `{"status": "ok", "data_loaded": <bool>}`; with `monkeypatch.setenv("APP_DUCKDB_PATH",
  str(tmp_path / "missing.duckdb"))` and `get_settings.cache_clear()` → `data_loaded is False`.

Run `uv run python -m scripts.export_openapi` to create `docs/contracts/openapi.json`, and
create `docs/contracts/README.md` by copying `FAM/docs/contracts/README.md`.

### 3. Frontend skeleton (`frontend/`)

Copy, then edit only what is listed:

```bash
F=$FAM/frontend
mkdir -p frontend/src/{styles,lib/api,components/layout/data,routes/daily,routes/yoy,test} frontend/public
cp $F/{package.json,pnpm-lock.yaml,components.json,index.html,tsconfig.json,tsconfig.app.json,tsconfig.node.json,vite.config.ts,.gitignore} frontend/
cp $F/public/favicon.svg frontend/public/
cp $F/src/{main.tsx,vite-env.d.ts} frontend/src/
cp $F/src/styles/{globals.css,style-nova.css} frontend/src/styles/
cp $F/src/lib/{utils.ts,table.ts,query-client.ts} frontend/src/lib/
cp $F/src/lib/api/client.ts frontend/src/lib/api/
cp -r $F/src/hooks frontend/src/
cp -r $F/src/components/ui $F/src/components/reui frontend/src/components/
cp $F/src/components/icon-placeholder.tsx frontend/src/components/
cp $F/src/components/layout/{app-sidebar.tsx,app-title.tsx,header.tsx,main.tsx,nav-group.tsx,types.ts} frontend/src/components/layout/
cp $F/src/routes/__root.tsx frontend/src/routes/
cp $F/src/test/setup.ts frontend/src/test/
```

Do **not** copy: `components/layout/{app-shell,profile-switcher,nav-accounts*}`, `stores/`,
`features/`, `lib/format*`, any app component under `src/components/*.tsx` except
`icon-placeholder.tsx`, `src/routeTree.gen.ts` (regenerated), `src/lib/api/schema.d.ts`
(regenerated).

Edits:

- `frontend/package.json`: `"name": "dts-webapp-frontend"`. Leave dependencies identical (the
  copied `reui` data grid needs `@dnd-kit/*`; unused packages are tree-shaken).
- `frontend/index.html`: `<title>DTS Analysis</title>`; add before `</head>`:

  ```html
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  ```

- `frontend/src/styles/globals.css`: in the `:root` block, add as its first line
  `--font-inter: "Inter", ui-sans-serif, system-ui, sans-serif;` (FAM references this
  variable but never defines it). No other token changes.
- `frontend/src/lib/query-client.ts`: `staleTime: 5 * 60_000` (data changes once a day;
  FAM's 30 s suits a ledger, not this).
- `frontend/src/components/layout/app-title.tsx`: replace the two spans with
  `DTS Analysis` (`font-bold`) and `U.S. Treasury daily statement` (`text-xs`).
- `frontend/src/components/layout/data/sidebar-data.ts` (new content):

  ```ts
  import {
    BarChart3, BookOpen, CalendarDays, CalendarRange, Database,
    LayoutDashboard, TrendingUp,
  } from 'lucide-react'
  import { type NavItem, type NavLink } from '../types'

  export const MENU_ITEMS: NavItem[] = [
    { title: 'Overview', url: '/', icon: LayoutDashboard },
    {
      title: 'Daily',
      icon: CalendarDays,
      items: [
        { title: 'Single date', url: '/daily/single-date' },
        { title: 'Net transfers', url: '/daily/net-transfers' },
      ],
    },
    { title: 'Fiscal year', url: '/fiscal-year', icon: BarChart3 },
    {
      title: 'Year over year',
      icon: TrendingUp,
      items: [
        { title: 'Net transfers', url: '/yoy/net-transfers' },
        { title: 'Withdrawals', url: '/yoy/withdrawals' },
        { title: 'Deposits', url: '/yoy/deposits' },
        { title: 'Category comparison', url: '/yoy/categories' },
      ],
    },
    { title: 'Weekly comparison', url: '/weekly', icon: CalendarRange },
  ]

  /** Pinned under the menu: about the data rather than views of it. */
  export const FOOTER_ITEMS: NavLink[] = [
    { title: 'Data status', url: '/data-status', icon: Database },
    { title: 'Methodology', url: '/methodology', icon: BookOpen },
  ]
  ```

- `frontend/src/components/layout/app-sidebar.tsx` (rewrite on FAM's structure):
  `AppSidebar()` takes no props; `<Sidebar collapsible='icon' variant='inset'>` →
  `<SidebarHeader><AppTitle /></SidebarHeader>` →
  `<SidebarContent><NavGroup title='Analysis' items={MENU_ITEMS} /></SidebarContent>` →
  `<SidebarFooter>` with `FOOTER_ITEMS` rendered through `SidebarMenuLink` (as FAM does) and
  `<p className='px-2 py-1 text-xs text-muted-foreground group-data-[collapsible=icon]:hidden'>Source: U.S. Treasury Fiscal Data</p>`
  → `<SidebarRail />`. Remove the profile and accounts imports.
- `frontend/src/routes/__root.tsx`: replace `import { AppShell } ...` and `<AppShell />` with
  `AppSidebar` from `@/components/layout/app-sidebar`. Keep `RootError`, `NotFound`
  (change link text to `Back to overview`), the `TooltipProvider` comment, and the `min-w-0`
  comment unchanged.
- `frontend/src/components/page-placeholder.tsx` (new):
  `PagePlaceholder({ title, phase }: { title: string; phase: number })` renders
  `<Header fixed><h1 className='text-base font-medium'>{title}</h1></Header>` and
  `<Main><p className='text-sm text-muted-foreground'>Coming in Phase {phase}.</p></Main>`.
- Route files, each `createFileRoute('<path>')({ component: () => <PagePlaceholder title='…' phase={N} /> })`:

  | File | Path | Title | Phase |
  |---|---|---|---|
  | `src/routes/index.tsx` | `/` | Overview | 5 |
  | `src/routes/data-status.tsx` | `/data-status` | Data status | 5 |
  | `src/routes/daily/single-date.tsx` | `/daily/single-date` | Single date | 5 |
  | `src/routes/daily/net-transfers.tsx` | `/daily/net-transfers` | Daily net transfers | 5 |
  | `src/routes/fiscal-year.tsx` | `/fiscal-year` | Fiscal year | 5 |
  | `src/routes/yoy/net-transfers.tsx` | `/yoy/net-transfers` | Net transfers year over year | 6 |
  | `src/routes/yoy/withdrawals.tsx` | `/yoy/withdrawals` | Withdrawals year over year | 6 |
  | `src/routes/yoy/deposits.tsx` | `/yoy/deposits` | Deposits year over year | 6 |
  | `src/routes/yoy/categories.tsx` | `/yoy/categories` | Category comparison | 6 |
  | `src/routes/weekly.tsx` | `/weekly` | Weekly comparison | 6 |
  | `src/routes/methodology.tsx` | `/methodology` | Methodology | 7 |

- `frontend/src/components/layout/app-sidebar.test.tsx`: build a router from `routeTree`
  with `createMemoryHistory({ initialEntries: ['/'] })`, render `<RouterProvider>` inside a
  `QueryClientProvider`, and assert: links named `Overview`, `Fiscal year`,
  `Weekly comparison`, `Data status`, `Methodology` exist; buttons `Daily` and
  `Year over year` exist; clicking `Year over year` reveals a link `Category comparison`
  with `href="/yoy/categories"`.

Then:

```bash
cd frontend && pnpm install && pnpm gen:api && pnpm build   # build regenerates routeTree.gen.ts
```

### 4. Vercel Services config — `vercel.json`

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "services": {
    "web": {
      "root": "frontend/",
      "framework": "vite",
      "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
    },
    "api": {
      "root": "backend/",
      "framework": "fastapi",
      "entrypoint": "app.main:app",
      "functions": {
        "app/main.py": {
          "maxDuration": 30,
          "excludeFiles": "{tests/**,.venv/**,.pytest_cache/**,.ruff_cache/**,scripts/**}"
        }
      }
    }
  },
  "rewrites": [
    { "source": "/api/(.*)", "destination": { "service": "api" } },
    { "source": "/(.*)", "destination": { "service": "web" } }
  ]
}
```

The `web` service rewrite is the SPA fallback (TanStack Router owns client paths); static
files take precedence over it. `scripts/**` is excluded from the function bundle — it runs at
build time only.

### 5. Link and deploy

```bash
gh auth status                      # active account must be hminle
vercel link --yes --project dts-webapp
vercel git connect                  # links github.com/hminle/dts-webapp (needed for Deploy Hooks in Phase 4)
vercel deploy --prod
```

The production alias is `https://dts-webapp.vercel.app` (or the alias the CLI prints). Use the
production URL for checks — preview URLs sit behind Vercel Deployment Protection and return 401
to `curl`.

## Verification

- [ ] `cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest -q` → all pass.
- [ ] `cd frontend && pnpm typecheck && pnpm test && pnpm build` → all pass;
      `ls frontend/dist/assets/*.js | wc -l` > 1 (route code splitting active).
- [ ] `scripts/dev.sh --install` → backend logs `Uvicorn running on http://127.0.0.1:8000`,
      `http://localhost:5173` shows the sidebar; `curl -s localhost:5173/api/health` →
      `{"status":"ok","data_loaded":false}` (through the Vite proxy).
- [ ] Sidebar in the browser: collapsing to the icon rail turns `Daily` / `Year over year`
      into dropdowns; text font is Inter (DevTools → Computed → `font-family` starts with
      `"Inter"`); the `.dark` class on `<html>` switches tokens.
- [ ] `curl -s https://dts-webapp.vercel.app/api/health` →
      `{"status":"ok","data_loaded":false}`.
- [ ] `curl -s -o /dev/null -w '%{http_code}' https://dts-webapp.vercel.app/yoy/categories` →
      `200` (SPA fallback), and `https://dts-webapp.vercel.app/api/docs` renders Swagger.
- [ ] Vercel build log for the `api` service contains
      `fetch_artifact: APP_ARTIFACT_URL not set, skipping download` (proves the
      `[tool.vercel.scripts] build` hook runs in services mode).
- [ ] `docs/contracts/openapi.json` contains the path `/api/health` with operationId
      `health_health`.

## Notes

- **If the build hook does not run in services mode** (the log line is missing), set
  `"buildCommand": "python -m scripts.fetch_artifact"` on the `api` service in `vercel.json`
  and redeploy; record which one worked here.
- **If the `functions` key is rejected** (build error naming `app/main.py`), the key is
  resolved differently in services mode — use the path the error message suggests and record
  it here.
- **Fallback if Vercel Services misbehaves** (it is beta): two Vercel projects —
  `dts-webapp` (root `frontend/`) and `dts-webapp-api` (root `backend/`) — with the frontend's
  `vercel.json` rewriting `/api/(.*)` to `https://dts-webapp-api.vercel.app/api/$1`. Paths and
  same-origin behavior stay identical for the browser. Update phase-0 and this note if used.
