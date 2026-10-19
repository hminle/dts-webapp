# Operations

Runbook for the production app at <https://dts-webapp.vercel.app>. Secret values never go in
this file — only their names and where they live.

## Daily pipeline

`.github/workflows/ingest.yml` runs at **22:30 UTC Monday–Friday** (Treasury publishes the DTS
around 16:00 ET) and can be started by hand. Steps:

1. Ping healthchecks.io `/start`.
2. Download the current artifact from the public R2 URL
   (`https://pub-22cfaba2d9874e799d437ddb6d289fd2.r2.dev/latest/treasury_data.duckdb`).
3. `python -m app.ingest` fetches new Treasury rows into a temp copy, validates it, and swaps it
   in. No new data → `changed=false` and every later step but the success ping is skipped.
4. Upload `snapshots/<UTC date>/treasury_data.duckdb`, then `latest/treasury_data.duckdb` to
   bucket `dts-data` (`cf r2 objects put`, retried up to 6 times, checked by size).
5. POST the Vercel Deploy Hook `daily-data` (builds `main`); the build downloads `latest/`.
6. Wait for the new deployment to report the new `latest_record_date`, then request each page's
   default API URLs so the CDN cache is warm.
7. Ping healthchecks.io (success, or `/fail` if any step failed).

Logs: GitHub → Actions → `ingest`. Deployments: `vercel ls` or the Vercel dashboard.

`.github/workflows/ci.yml` gates every PR and push to `main`: ruff, pytest, OpenAPI contract
drift (backend); generated-client drift, typecheck, tests, build (frontend).

## Run manually

```bash
gh workflow run ingest                 # incremental
gh workflow run ingest -f full=true    # rebuild from 2005
gh run watch                           # follow the run
```

## Roll back data

- **Fastest:** Vercel dashboard → Deployments → the previous production deployment → Promote.
  Its bundled artifact comes back with it.
- **Replace `latest/`:** download a snapshot and upload it as `latest/`, then fire the hook:

  ```bash
  curl -fsS -A "dts-webapp-ops/1.0" -o old.duckdb \
    https://pub-22cfaba2d9874e799d437ddb6d289fd2.r2.dev/snapshots/2026-10-16/treasury_data.duckdb
  cf r2 objects put latest/treasury_data.duckdb --bucket-name dts-data --file "$PWD/old.duckdb" \
    --content-type application/octet-stream
  curl -fsS -X POST "$VERCEL_DEPLOY_HOOK_URL"
  ```

  The next scheduled run starts from this file and re-fetches anything newer.

## Failure triage

healthchecks.io emails when a run pings `/fail` or no ping arrives within the 3 h grace.

1. Open the failed run in Actions and find the first red step.
2. Common causes:
   - **Treasury API outage / timeouts** (`TreasuryAPIError`) — nothing to do; the next run
     catches up, because ingestion fetches everything after the artifact's latest date.
   - **`ArtifactInvalid`** — validation rejected the new build. Read the message; never
     upload a file by hand to get past it. `latest/` was not touched.
   - **Upload failed after 6 tries** — R2 was flaky; re-run the workflow. If it keeps
     happening, switch the upload to R2's S3 API (see the Phase 4 plan Notes).
   - **Deploy hook failed** — data is in R2; run `curl -fsS -X POST` on the hook, or redeploy
     from the Vercel dashboard.

## Secrets inventory

GitHub Actions secrets (`gh secret list`):

| Name | What it is |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token with Workers R2 Storage: Edit on the account |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account id (from `cf auth whoami`) |
| `VERCEL_DEPLOY_HOOK_URL` | Vercel → Settings → Git → Deploy Hooks → `daily-data` (branch `main`) |
| `HEALTHCHECK_PING_URL` | healthchecks.io check `dts-ingest` (cron `30 22 * * 1-5` UTC, grace 3 h) |

A leaked deploy hook only lets someone trigger rebuilds; rotate it by deleting and recreating it
in Vercel and updating the secret.

## Scheduled workflow disabled after 60 days

GitHub turns off scheduled workflows in a repo with no activity for 60 days. The healthcheck
stops getting pings and emails. Fix: Actions → `ingest` → **Enable workflow**, then
`gh workflow run ingest`.
