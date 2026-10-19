# Phase 4: Daily Pipeline & CI — ⬜ Not Started

**Goal**: Every business day, GitHub Actions updates the artifact from the Treasury API,
uploads it to R2, and triggers a Vercel deploy; failures alert loudly and never replace good
data. A CI workflow gates every PR on lint, tests, typecheck, build, and contract drift.

## Scope

- In scope: `.github/workflows/ingest.yml`, `.github/workflows/ci.yml`, GitHub secrets,
  Vercel Deploy Hook, healthchecks.io dead-man's switch, `docs/operations.md` runbook.
- Out of scope: new ingestion logic (Phase 2), backups beyond dated R2 snapshots,
  multi-region, alerts to users.

Branch: `feat/daily-pipeline`.

## Implementation

### 1. One-time cloud setup (record outcomes in `docs/operations.md`, never the secret values)

| Secret / resource | How |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare dashboard → My Profile → API Tokens → Create → template "Edit R2" (or custom: Account › Workers R2 Storage › Edit), scoped to the account. Store with `gh secret set CLOUDFLARE_API_TOKEN` |
| `CLOUDFLARE_ACCOUNT_ID` | `cf auth whoami` (or dashboard sidebar). `gh secret set CLOUDFLARE_ACCOUNT_ID` |
| `VERCEL_DEPLOY_HOOK_URL` | Vercel → project `dts-webapp` → Settings → Git → Deploy Hooks → name `daily-data`, branch `main`. `gh secret set VERCEL_DEPLOY_HOOK_URL` |
| `HEALTHCHECK_PING_URL` | healthchecks.io (free) → new check `dts-ingest`, schedule cron `30 22 * * 1-5` UTC, grace 3 h, email alert. `gh secret set HEALTHCHECK_PING_URL` |

Run `gh auth status` first — the active account must be `hminle`.

### 2. `.github/workflows/ingest.yml`

```yaml
name: ingest
on:
  schedule:
    - cron: "30 22 * * 1-5"   # 22:30 UTC weekdays; Treasury publishes ~16:00 ET
  workflow_dispatch:
    inputs:
      full:
        description: "Rebuild from 2005 (--full)"
        type: boolean
        default: false
concurrency:
  group: ingest
  cancel-in-progress: false
jobs:
  ingest:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    env:
      CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
      CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
      CF: npx --yes cf@1.0.0-beta.18
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - uses: actions/setup-node@v4
        with: { node-version: "24" }
      - run: curl -fsS -m 10 --retry 3 "${{ secrets.HEALTHCHECK_PING_URL }}/start"
      - run: uv sync --group ingest --locked
      - name: Download current artifact
        if: ${{ !inputs.full }}
        run: |
          mkdir -p data
          $CF r2 objects get latest/treasury_data.duckdb --bucket-name dts-data -q > data/treasury_data.duckdb
      - name: Ingest
        id: ingest
        run: uv run --group ingest python -m app.ingest --db data/treasury_data.duckdb ${{ inputs.full && '--full' || '' }}
      - name: Upload snapshot and latest
        if: steps.ingest.outputs.changed == 'true'
        run: |
          D=$(date -u +%F)
          $CF r2 objects put "snapshots/$D/treasury_data.duckdb" --bucket-name dts-data --file data/treasury_data.duckdb --content-type application/octet-stream
          $CF r2 objects put latest/treasury_data.duckdb --bucket-name dts-data --file data/treasury_data.duckdb --content-type application/octet-stream
      - name: Trigger Vercel deploy
        if: steps.ingest.outputs.changed == 'true'
        run: curl -fsS -X POST "${{ secrets.VERCEL_DEPLOY_HOOK_URL }}"
      - name: Ping success
        if: success()
        run: curl -fsS -m 10 --retry 3 "${{ secrets.HEALTHCHECK_PING_URL }}"
      - name: Ping failure
        if: failure()
        run: curl -fsS -m 10 --retry 3 "${{ secrets.HEALTHCHECK_PING_URL }}/fail"
```

Order matters: the snapshot upload precedes `latest/`, and the deploy hook fires only after
`latest/` is written, so a Vercel build can never fetch a half-updated pointer. GitHub
disables scheduled workflows after 60 days without repo activity — `docs/operations.md`
notes this and the healthcheck catches it.

### 3. `.github/workflows/ci.yml`

On `pull_request` and `push` to `main`, two jobs:

- `backend` (working dir `backend/`): `astral-sh/setup-uv@v6` → `uv sync --locked` →
  `uv run ruff check .` → `uv run ruff format --check .` → `uv run pytest -q` →
  `uv run python -m scripts.export_openapi` → `git diff --exit-code ../docs/contracts/openapi.json`
  (contract drift fails CI).
- `frontend` (working dir `frontend/`): `pnpm/action-setup@v4` + `actions/setup-node@v4`
  (`node-version: 24`, `cache: pnpm`, `cache-dependency-path: frontend/pnpm-lock.yaml`) →
  `pnpm install --frozen-lockfile` → `pnpm gen:api` → `git diff --exit-code src/lib/api/schema.d.ts`
  → `pnpm typecheck` → `pnpm test` → `pnpm build`.

### 4. `docs/operations.md`

Sections: **Daily pipeline** (schedule, what each step does, where logs are), **Run manually**
(`gh workflow run ingest`, `gh workflow run ingest -f full=true`), **Roll back data** (Vercel
dashboard → Deployments → previous production deployment → Promote; or re-upload a
`snapshots/<date>/` object to `latest/` with `cf r2 objects get`/`put` and re-trigger the hook),
**Failure triage** (healthchecks email → Actions run log → common causes: Treasury API outage →
just wait for next run; `ArtifactInvalid` → inspect the message, never force-upload),
**Secrets inventory** (names only), **Scheduled workflow disabled after 60 days** (re-enable in
the Actions tab).

## Verification

- [ ] `gh workflow run ingest` → run succeeds; with no new Treasury data, the log shows
      `"changed": false` and the upload/deploy steps are skipped; healthchecks.io shows a success ping.
- [ ] On a business day after ~22:30 UTC (or after Treasury publishes): the scheduled run
      uploads `snapshots/<today>/…`, triggers a deployment visible in `vercel ls`, and
      `curl -s https://dts-webapp.vercel.app/api/v1/meta/build` shows the new
      `latest_record_date`.
- [ ] Failure path: temporarily set repo variable/secret so ingest fails (e.g. run the workflow
      on a branch where `APP_TREASURY_BASE_URL: https://10.255.255.1` is added to the Ingest
      step env) → job fails, healthchecks.io receives `/fail` and emails, R2 `latest/` object's
      `last-modified` (`curl -sI https://pub-<hash>.r2.dev/latest/treasury_data.duckdb`) is unchanged.
- [ ] Open a PR that changes a schema field without regenerating the contract → `ci` fails at the
      `git diff --exit-code` step; regenerate → green.
- [ ] `gh workflow run ingest -f full=true` completes inside the 120-minute timeout (record the
      duration in Notes).

## Notes

(record full-rebuild duration and any cf CLI quirks met in CI)
