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
          # Public r2.dev read; a named User-Agent, since Cloudflare 403s some defaults.
          curl -fsS -A "dts-webapp-ingest/1.0" --retry 3 -o data/treasury_data.duckdb \
            "https://pub-22cfaba2d9874e799d437ddb6d289fd2.r2.dev/latest/treasury_data.duckdb"
      - name: Ingest
        id: ingest
        run: uv run --group ingest python -m app.ingest --db data/treasury_data.duckdb ${{ inputs.full && '--full' || '' }}
      - name: Upload snapshot and latest
        if: steps.ingest.outputs.changed == 'true'
        run: |
          # Single-request uploads of the ~50 MB file fail intermittently with
          # "fetch failed" (Phase 2 notes), so each put is retried and checked.
          put() {
            local size; size=$(stat -c %s data/treasury_data.duckdb)
            for try in 1 2 3 4 5 6; do
              if $CF r2 objects put "$1" --bucket-name dts-data --file "$PWD/data/treasury_data.duckdb" \
                   --content-type application/octet-stream 2>&1 | grep -q "\"size\": \"$size\""; then
                echo "$1 uploaded on try $try"; return 0
              fi
              echo "$1 try $try failed"; sleep $((try * 5))
            done
            return 1
          }
          D=$(date -u +%F)
          put "snapshots/$D/treasury_data.duckdb"
          put latest/treasury_data.duckdb
      - name: Trigger Vercel deploy
        if: steps.ingest.outputs.changed == 'true'
        run: curl -fsS -X POST "${{ secrets.VERCEL_DEPLOY_HOOK_URL }}"
      - name: Warm the CDN cache
        if: steps.ingest.outputs.changed == 'true'
        run: |
          # A cold Vercel function takes ~7 s (Phase 3 Notes). Wait until the new
          # deployment serves today's data, then request each page's default URLs so
          # visitors get cache HITs. Extend URLS as Phases 5-6 add pages.
          U=https://dts-webapp.vercel.app/api/v1
          want="${{ steps.ingest.outputs.latest_record_date }}"
          for i in $(seq 1 40); do
            curl -fsS "$U/meta/build?_=$(date +%s)" | grep -q "\"latest_record_date\":\"$want\"" && break
            sleep 30
          done
          FY=$(curl -fsS "$U/lookups/fiscal-years" | python3 -c 'import json,sys; print(json.load(sys.stdin)[0])')
          PREV=$((FY - 1))
          for path in meta/stats meta/build meta/record-counts meta/record-counts-by-year \
                      lookups/fiscal-years lookups/data-sources lookups/categories \
                      "net-transfers/fiscal-year/$FY" "net-transfers/fiscal-year/$PREV" \
                      "weekly/comparison?first_fiscal_year=$FY&second_fiscal_year=$PREV" \
                      "yoy/daily-comparison?current_fiscal_year=$FY&previous_fiscal_year=$PREV&metric=net_flow" \
                      "yoy/daily-comparison?current_fiscal_year=$FY&previous_fiscal_year=$PREV&metric=total_withdrawals" \
                      "yoy/daily-comparison?current_fiscal_year=$FY&previous_fiscal_year=$PREV&metric=total_deposits" \
                      "categories/major-spending?current_fiscal_year=$FY&previous_fiscal_year=$PREV" \
                      "categories/major-receipts?current_fiscal_year=$FY&previous_fiscal_year=$PREV" \
                      "categories/tbill-interest?current_fiscal_year=$FY&previous_fiscal_year=$PREV" \
                      "categories/irs-tax-refunds?current_fiscal_year=$FY&previous_fiscal_year=$PREV"; do
            curl -fsS -o /dev/null -w "%{http_code} %{time_total}s $path\n" "$U/$path" || true
          done
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
- [ ] After a changed run, the warm-up step logs 200 for every URL and a manual
      `curl -sI` of `$U/categories/major-spending?...` right after shows `x-vercel-cache: HIT`.
- [ ] Open a PR that changes a schema field without regenerating the contract → `ci` fails at the
      `git diff --exit-code` step; regenerate → green.
- [ ] `gh workflow run ingest -f full=true` completes inside the 120-minute timeout (record the
      duration in Notes).

## Notes

- **If the retried `cf` upload still fails in CI**, switch the upload step to R2's
  S3-compatible API (`aws s3 cp --endpoint-url https://<account_id>.r2.cloudflarestorage.com`,
  preinstalled on GitHub runners, multipart for large files) with an R2 S3 access key pair as
  secrets `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY`. `cf r2 objects put --help` itself
  recommends the S3 API for most workloads.
- Use absolute paths with `cf --file` (`$PWD/...`).

(record full-rebuild duration and any cf CLI quirks met in CI)
