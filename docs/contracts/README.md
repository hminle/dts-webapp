# API contract

`openapi.json` is the committed snapshot of the backend's OpenAPI spec — the
single source of truth for the backend↔frontend contract.

- Regenerate after any endpoint change, **in the same commit**:
  `cd backend && uv run python -m scripts.export_openapi`
- The frontend generates its typed client from it:
  `cd frontend && pnpm gen:api` (→ `src/lib/api/schema.d.ts`)

A contract break then surfaces as a TypeScript compile error, not a runtime bug.
