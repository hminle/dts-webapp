# Phase 7: Launch Hygiene — 🟡 In Progress

**Goal**: The public app is safe to share: caching is verified end to end, abusive traffic is
rate limited, backend errors reach a monitor, and the site states its methodology, data source,
terms, privacy policy, and "not financial advice" disclaimer.

## Scope

- In scope: cache/HEADER verification, one Vercel WAF rate-limit rule, security headers,
  Sentry for the backend, Vercel Web Analytics, Methodology / Terms / Privacy pages, a
  disclaimer in the sidebar footer, launch checklist, operations doc updates.
- Out of scope: custom domain (none yet — add later in Cloudflare DNS → Vercel), auth,
  payments, email, SEO beyond a `<meta name="description">`.

Branch: `feat/launch-hygiene`.

## Implementation

### 1. Cache and header audit (no code unless a check fails)

Script the audit in `docs/launch-checklist.md` as copy-pasteable commands against
`https://dts-webapp.vercel.app`:

- every `GET /api/v1/*` route from the Endpoint Map (one representative URL each) returns
  `cache-control` containing `s-maxage=86400` and, on the second request, `x-vercel-cache: HIT`;
- no `/api/*` response carries `set-cookie` (it would silently disable CDN caching — Vercel
  never caches responses with `Set-Cookie`);
- `/api/health` returns no `s-maxage`;
- a static asset under `/assets/` returns `cache-control: public, max-age=31536000, immutable`.

### 2. Rate limiting (Vercel Firewall, dashboard)

Hobby allows one WAF rate-limit rule per project. Create it: Project → Firewall → Configure →
New Rule → name `api-per-ip` → If **Request Path** starts with `/api/` → Then **Rate Limit**,
Fixed Window, 60 s, 300 requests, key **IP**, action **Default (429)** → Save → Review Changes
→ Publish. Start with action **Log** for one day, check the Firewall overview for false
positives, then switch to 429. Cached responses are served by the CDN, so normal browsing stays
far under 300/min per visitor. Record the rule in `docs/operations.md`.

### 3. Security headers — `vercel.json` (top level, applies to both services)

```json
"headers": [
  {
    "source": "/(.*)",
    "headers": [
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
      { "key": "X-Frame-Options", "value": "DENY" },
      { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" }
    ]
  }
]
```

If Vercel rejects top-level `headers` in services mode, move the block into the `web` service
and add the same headers in FastAPI via a tiny middleware in `backend/app/main.py`; note which
in Notes.

### 4. Error monitoring — Sentry (backend)

- `cd backend && uv add "sentry-sdk[fastapi]"`.
- `Settings.sentry_dsn: str | None = None`; in `backend/app/main.py`, if set:
  `sentry_sdk.init(dsn=..., traces_sample_rate=0.0, send_default_pii=False)` before
  creating `app`.
- Create a free Sentry project (platform FastAPI); `vercel env add APP_SENTRY_DSN production`.
- Frontend errors are out of scope for now; `__root.tsx`'s `RootError` already shows them.

### 5. Analytics — Vercel Web Analytics

`cd frontend && pnpm add @vercel/analytics`; render `<Analytics />` from
`@vercel/analytics/react` once inside the root component in `frontend/src/routes/__root.tsx`;
enable Web Analytics on the project in the Vercel dashboard. It is cookieless, which the privacy
page states.

### 6. Content pages

Write copy for a non-specialist reader; numbers and definitions must match the code.

- `frontend/src/features/methodology/methodology-page.tsx` (route `routes/methodology.tsx`,
  replacing the placeholder): sections **Source** (Treasury Fiscal Data API, the 9 DTS tables
  by display name from `ENDPOINTS`), **Update schedule** (each business day ~22:30 UTC after the
  ~4 pm ET release), **Units** (millions of dollars), **Net transfers** (total withdrawals −
  total deposits, both excluding public-debt cash issues/redemptions — the formula in
  `backend/app/utils/deposits_withdrawals.py`), **Fiscal year** (Oct 1 – Sep 30;
  `day_of_fiscal_year` = the Nth business day with data in that FY), **Comparison modes**
  (`fiscal_day` vs `calendar_date`, from the `comparison_mode` field descriptions in
  `backend/app/schemas/treasury.py`), **Known limits** (Treasury revisions are not re-fetched;
  days without totals are skipped).
- `frontend/src/routes/terms.tsx` and `frontend/src/routes/privacy.tsx`: short plain pages
  (`Header`/`Main`). Terms: informational only, not financial advice, no warranty, data is
  public-domain U.S. Treasury data. Privacy: no accounts, no cookies, anonymous aggregate page
  analytics via Vercel Web Analytics, server logs kept by Vercel.
- `frontend/src/components/data-disclaimer.tsx`: one line "Not financial advice · Source: U.S.
  Treasury" with links to `/terms` and `/privacy`; replaces the sidebar footer `<p>` in
  `app-sidebar.tsx` (still hidden in the collapsed rail).
- `frontend/index.html`: add `<meta name="description" content="Daily U.S. Treasury cash flows, net transfers, and year-over-year comparisons from the Daily Treasury Statement." />`.

### 7. Docs

- `docs/launch-checklist.md`: the §1 audit commands, plus: every sidebar link loads in light and
  dark mode on a 375 px viewport, Lighthouse (Chrome DevTools, mobile) Performance ≥ 80 and
  Accessibility ≥ 90 on `/` and `/yoy/net-transfers`, healthcheck green for the last 3 business
  days, rate-limit rule in 429 mode, Sentry received a test event.
- `docs/operations.md`: add Rate limiting, Sentry, and Analytics sections.

## Verification

- [ ] Every item in `docs/launch-checklist.md` is checked off with the date it was checked.
- [ ] `for i in $(seq 1 320); do curl -s -o /dev/null -w '%{http_code}\n' "https://dts-webapp.vercel.app/api/v1/lookups/fiscal-years?x=$i"; done | sort | uniq -c`
      (unique URLs force misses) → shows `429`s once the rule is active.
- [ ] Temporarily add a route that raises (local branch only, deployed as a preview with
      `APP_SENTRY_DSN` set for preview) → the exception appears in Sentry; remove the route.
- [x] `curl -sI https://dts-webapp.vercel.app/ | grep -i -E "x-frame-options|x-content-type-options"` → both present
      (checked on the preview deploy; re-run on production after merge).
- [x] `/methodology`, `/terms`, `/privacy` load; sidebar footer shows the disclaimer with both
      links; `pnpm typecheck && pnpm test && pnpm build` and backend `uv run pytest -q` pass.

## Notes

- **Code done 2026-10-19** (branch `feat/launch-hygiene`): content pages, disclaimer, meta
  description, security headers, Sentry init (inert until `APP_SENTRY_DSN` is set), Web
  Analytics component, `Main` as a `div`, `docs/launch-checklist.md`, operations sections.
  Left for the owner: Firewall rule, Sentry project + env var, enabling Web Analytics, and the
  checklist items that need a few days of runs.
- **Top-level `headers` work in services mode** — they apply to both services (checked on a
  preview: `/`, `/terms`, `/api/health`, `/api/v1/meta/build`), so no FastAPI middleware.
- **Hashed assets were served `max-age=0`** in production: services mode doesn't add Vercel's
  usual Vite asset caching. A `/assets/(.*)` rule in `vercel.json` sets
  `public, max-age=31536000, immutable`.
- **The audit as first written couldn't pass:** Vercel strips `s-maxage` and
  `stale-while-revalidate` from the client-facing header (data routes show
  `public, max-age=300`), and FastAPI answers `HEAD` with 405, so `curl -I` is useless on
  `/api/*`. The checklist checks `x-vercel-cache: HIT` with `GET` instead.
- Previews have Vercel Deployment Protection; `vercel curl <path> --deployment <url>` reaches
  them (it created a protection-bypass token for the project the first time).
- **The app does set one cookie:** shadcn's `SidebarProvider` writes `sidebar_state` when the
  sidebar is toggled (meant for server rendering; nothing here reads it). The privacy page names
  it instead of claiming "no cookies". It doesn't affect CDN caching — Vercel's cache key
  ignores request cookies. Nothing else writes cookies or `localStorage` (no theme toggle).
- Found in Phase 6: every page nests two `<main>` landmarks (shadcn `SidebarInset` renders one
  and `components/layout/main.tsx` another — FAM has the same). `Main` is now a `<div>`; each page
  has one `<main>`.
