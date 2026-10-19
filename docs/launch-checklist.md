# Launch checklist

Run before sharing the app publicly, and again after any change to `vercel.json`, caching, or
the backend's response headers. Write the date next to each item when it is checked.

## 1. Cache and header audit

Vercel's CDN consumes `s-maxage` / `stale-while-revalidate` and strips them from the header the
client sees, so a data route shows `cache-control: public, max-age=300`; caching is proven by
`x-vercel-cache: HIT` on the second request. FastAPI routes don't answer `HEAD`, so use `GET`
(`-o /dev/null -D -`), never `curl -I`.

```bash
U=https://dts-webapp.vercel.app
FY=$(curl -s $U/api/v1/lookups/fiscal-years | python3 -c 'import json,sys; print(json.load(sys.stdin)[0])'); PREV=$((FY - 1))
# zsh: don't name the loop variable `path`; it is tied to $PATH.
for u in meta/stats meta/build meta/record-counts lookups/fiscal-years lookups/categories \
         "data/date/2026-10-15" "net-transfers/fiscal-year/$FY" \
         "weekly/comparison?first_fiscal_year=$FY&second_fiscal_year=$PREV" \
         "yoy/daily-comparison?current_fiscal_year=$FY&previous_fiscal_year=$PREV&metric=net_flow" \
         "categories/major-spending?current_fiscal_year=$FY&previous_fiscal_year=$PREV"; do
  curl -s -o /dev/null "$U/api/v1/$u"
  echo "$u: $(curl -s -o /dev/null -D - "$U/api/v1/$u" | grep -iE 'x-vercel-cache|set-cookie' | tr -d '\r' | paste -sd' ')"
done
curl -s -o /dev/null -D - $U/api/health | grep -i cache-control
JS=$(curl -s $U/ | grep -o '/assets/index-[^"]*\.js' | head -1); curl -sI $U$JS | grep -i cache-control
curl -sI $U/ | grep -iE 'x-frame-options|x-content-type-options|referrer-policy|permissions-policy'
```

- [ ] Every data route prints `x-vercel-cache: HIT` and no `set-cookie` (Vercel never caches a
      response that sets a cookie).
- [ ] `/api/health` is `public, max-age=0, must-revalidate` (no CDN caching).
- [ ] The JS bundle is `public, max-age=31536000, immutable` (the `/assets/(.*)` rule in
      `vercel.json`; services mode doesn't add it on its own).
- [ ] `/` carries all four security headers.

## 2. Pages

- [ ] Every sidebar link loads in light and dark mode at a 375 px viewport, with no sideways
      scroll; the sidebar footer shows the disclaimer with Terms and Privacy links.
- [ ] `/methodology`, `/terms`, `/privacy` load.
- [ ] Lighthouse (Chrome DevTools → Lighthouse, Mobile) on `/` and `/yoy/net-transfers`:
      Performance ≥ 80, Accessibility ≥ 90.

## 3. Operations

- [ ] healthchecks.io `dts-ingest` green for the last 3 business days.
- [ ] Firewall rule `api-per-ip` in **429** mode (after a day in Log mode), and the 320-request
      loop in the Phase 7 plan returns some `429`s.
- [ ] Sentry received a test event from production (see `docs/operations.md` → Sentry).
- [ ] Vercel Web Analytics shows page views.
