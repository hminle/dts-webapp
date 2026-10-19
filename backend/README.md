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
