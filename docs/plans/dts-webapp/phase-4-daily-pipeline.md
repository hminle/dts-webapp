# Phase 4: Daily Pipeline & CI — 🟡 In Progress

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

- [x] `gh workflow run ingest` → run succeeds; with no new Treasury data, the log shows
      `"changed": false` and the upload/deploy steps are skipped; healthchecks.io shows a success ping.
- [x] On a business day after ~22:30 UTC (or after Treasury publishes): the scheduled run
      uploads `snapshots/<today>/…`, triggers a deployment visible in `vercel ls`, and
      `curl -s https://dts-webapp.vercel.app/api/v1/meta/build` shows the new
      `latest_record_date`.
- [x] Failure path: temporarily set repo variable/secret so ingest fails (e.g. run the workflow
      on a branch where `APP_TREASURY_BASE_URL: https://10.255.255.1` is added to the Ingest
      step env) → job fails, healthchecks.io receives `/fail` and emails, R2 `latest/` object's
      `last-modified` (`curl -sI https://pub-<hash>.r2.dev/latest/treasury_data.duckdb`) is unchanged.
- [x] After a changed run, the warm-up step logs 200 for every URL and a manual
      `curl -sI` of `$U/categories/major-spending?...` right after shows `x-vercel-cache: HIT`.
- [x] Open a PR that changes a schema field without regenerating the contract → `ci` fails at the
      `git diff --exit-code` step; regenerate → green.
- [x] `gh workflow run ingest -f full=true` completes inside the 120-minute timeout (record the
      duration in Notes).

## Notes

- **If the retried `cf` upload still fails in CI**, switch the upload step to R2's
  S3-compatible API (`aws s3 cp --endpoint-url https://<account_id>.r2.cloudflarestorage.com`,
  preinstalled on GitHub runners, multipart for large files) with an R2 S3 access key pair as
  secrets `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY`. `cf r2 objects put --help` itself
  recommends the S3 API for most workloads.
- Use absolute paths with `cf --file` (`$PWD/...`).

- 2026-10-19: all four secrets set; PR #1 (Phases 1–6 + this phase) merged to `main` with
  `ci` green on its first run (backend 16 s, frontend 47 s). First manual `ingest` (Sunday): 19 s,
  `changed=false`, upload/deploy/warm-up skipped, healthcheck pinged.
- The Treasury API had nothing after 2026-10-15 on Sunday night: each DTS appears the next
  business day, so the run on day D usually adds day D−1.
- 2026-10-19 failure path: `APP_TREASURY_BASE_URL=https://10.255.255.1` on a throwaway branch →
  Ingest failed in 36 s ("artifact left unchanged", connect timeout), upload/deploy skipped,
  `/fail` pinged; R2 `latest/` ETag `09a979a7…` / last-modified 01:19 UTC unchanged.
- 2026-10-19 contract drift (draft PR #3, closed): a changed `Field` description failed `backend`
  at "Contract drift" with the one-line diff; after `export_openapi` + `gen:api` both jobs passed.
- **The first scheduled run never fired** (Mon 2026-10-19 22:30 UTC): by 00:42 UTC there was no
  `schedule` run at all, though the workflow was active on `main`. GitHub delays or drops cron
  runs under load, and a newly added schedule can miss its first slot. Started it by hand
  (run 39349259259). Watch whether Tuesday's fires; if cron keeps slipping, move it off the
  half hour or add a second slot (e.g. `30 23 * * 1-5`) — re-runs on the same data are no-ops.
- **First run with new data** (manual, 2026-10-20 00:42 UTC, 2 m 18 s): 235 rows for 2026-10-16
  across 7 tables, FY2027 rebuilt; both uploads succeeded on try 1 (66 MB); deploy hook → new
  production deploy Ready in ~1 m; `/api/v1/meta/build` → `latest_record_date` 2026-10-16;
  warm-up 17/17 URLs 200 in 0.06–0.25 s; success ping.
- Snapshots are keyed by the **UTC run date**, not the statement date: this run wrote
  `snapshots/2026-10-20/` for the 2026-10-16 statement.
- **The warm-up only warms the runner's edge region.** Vercel's CDN caches per edge; a request
  through `sfo1` right after the run was a `MISS` (then `HIT`). The step still matters: it keeps
  the `iad1` function warm, so other regions' first miss costs ~0.1–0.3 s, not the ~7 s cold
  start.
- `cf r2 objects get` has no `--file`; the runbook downloads snapshots from the public r2.dev URL.
- Actions warns that `checkout@v4`, `setup-node@v4` and `setup-uv@v6` target Node 20 (forced to
  24) — bump to their Node 24 majors when convenient.
- **Full rebuild** (run 39350200089, 2026-10-20): 4 m 42 s end to end, ~4 m of it ingestion —
  far inside the 120-min timeout. 867,583 rows from 2005-10-03 to 2026-10-16, 22 fiscal years;
  exactly the incremental artifact's count (867,348 + 235), so incremental and full agree.
  The rebuilt file is 49.6 MB vs 66.3 MB for the incrementally grown one (DuckDB doesn't
  compact on append) — a periodic full rebuild keeps the artifact and build download small.
- **Warm-up bug, fixed:** the step waited for `latest_record_date` to match, which the outgoing
  deployment already does on a full rebuild or rerun, so it warmed the old deployment (job
  ended 00:57:05, new deploy ready ~00:57:50). It now records the live `build_date` before
  firing the hook and waits for it to change; rerun 39350824714 waited 4 checks (~90 s) and then
  warmed the new deployment.
- Scheduler options if GitHub cron keeps slipping (not done yet): a Cloudflare Worker Cron
  Trigger (Free: 5 per account, minute precision) calling the `workflow_dispatch` API with a
  fine-grained token (Actions: write, this repo only); Vercel Cron on Hobby is once a day with
  ±59 min precision and would add a trigger route to the read-only API. Keep GitHub's `schedule`
  as a backup either way — duplicate runs queue on the `ingest` concurrency group and no-op.
