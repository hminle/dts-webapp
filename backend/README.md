# dts-webapp backend

Read-only FastAPI API and the daily ingestion job. See `../CLAUDE.md` for architecture.

```bash
uv sync
uv run fastapi dev                            # :8000, docs at /api/docs
uv run pytest                                 # full suite
uv run ruff check . && uv run ruff format .   # run both before finishing a change
uv run python -m scripts.export_openapi       # regenerate ../docs/contracts/openapi.json
uv run python -m scripts.fetch_artifact       # download the artifact into data/ (needs APP_ARTIFACT_URL)
```

The published artifact is public at
`https://pub-22cfaba2d9874e799d437ddb6d289fd2.r2.dev/latest/treasury_data.duckdb`
(R2 bucket `dts-data`; dated copies under `snapshots/YYYY-MM-DD/`). Vercel's `APP_ARTIFACT_URL`
points there. Rebuild locally with
`uv run --group ingest python -m app.ingest --db data/treasury_data.duckdb --full`.
