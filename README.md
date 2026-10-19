# dts-webapp

A public web app for analyzing the U.S. Treasury **Daily Treasury Statement (DTS)**: daily
deposits and withdrawals of the Treasury General Account, net transfers, fiscal-year and
year-over-year comparisons, and major spending/receipt categories. A daily job builds a
read-only DuckDB file from the Treasury Fiscal Data API; Vercel serves the FastAPI API and the
React frontend from it.

## Quickstart

```bash
scripts/dev.sh --install   # uv sync + pnpm install, then backend :8000 + frontend :5173
```

Open http://localhost:5173.

See `CLAUDE.md` for architecture and conventions, and `docs/plans/dts-webapp/` for the
build-out plan.
