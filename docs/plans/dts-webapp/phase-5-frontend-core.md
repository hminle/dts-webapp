# Phase 5: Frontend — Core Pages — ⬜ Not Started

**Goal**: The Overview, Data status, Single date, Daily net transfers, and Fiscal year pages
work against the Phase 3 API in FAM's look, and the shared frontend building blocks (formatters,
fiscal helper, lookups hooks, loading/error states) exist for Phase 6.

## Scope

- In scope: shared libs and hooks, five pages ported from REF with page splits, Vitest tests for
  pure helpers and one mounted page.
- Out of scope: YoY / category / weekly pages (Phase 6), methodology/legal (Phase 7),
  URL-persisted filters, REF's Database admin page (not ported — ingestion replaced it).

Branch: `feat/frontend-core`. `REF` = `/home/hminle/gitrepos/personal-projects/dts-analysis/fullstack_app`.
Use the `shadcn` and `minimalist-ui` skills for every component written in this phase.

## Implementation

### 1. Shared libs

- `frontend/src/lib/format.ts` ← every export of `REF/frontend/src/lib/utils.ts` **except `cn`**
  (`formatCurrency`, `formatNumber`, `formatDate`, `formatShortDate`, `formatTreasuryValue`,
  `formatBillions`, `formatMillions`, `formatPercent`, `formatSignedPercent`) verbatim, converted
  to this repo's style (single quotes, no semicolons). `cn` stays in `src/lib/utils.ts` (FAM's).
- `frontend/src/lib/format.test.ts` — pin current behavior: read each implementation, then
  assert its output for `0`, a negative, `> 1e12`, and a non-integer (one `it` per function).
- `frontend/src/lib/fiscal.ts` — `currentFiscalYear(today: Date = new Date()): number`
  (`month >= 9` zero-based October → `year + 1`). Replace every REF inline copy
  (`grep -rn "getCurrentFiscalYear\|getMonth() >= 9" REF/frontend/src`) with an import of it as
  pages are ported.
- `frontend/src/lib/fiscal.test.ts` — `new Date(2026, 8, 30)` → 2026; `new Date(2026, 9, 1)` → 2027.
- `frontend/src/lib/chart.ts` ← `REF/frontend/src/lib/chart.ts` (`CHART_COLORS`, 8 categorical
  hex values — the one sanctioned place for raw colors, Invariant 8). Add
  `export const SERIES = { current: 'var(--chart-1)', previous: 'var(--chart-2)' } as const`
  for two-series current-vs-previous charts.
- `frontend/src/test/api.ts` — `mockApi(routes: Record<string, unknown>)`: replaces
  `globalThis.fetch` with a `vi.fn` that matches `new URL(request.url).pathname` against
  `routes` and returns `Response.json(body)`, or a 404 `{ detail: 'not mocked: <path>' }`.

### 2. Query hooks

Pattern for every hook (FAM's `features/categories/api.ts` style, but keep the backend's
`detail` — it carries "no data for this date" messages users need to see):

```ts
export function useFiscalYears() {
  return useQuery({
    queryKey: ['lookups', 'fiscal-years'],
    queryFn: async () => {
      const { data, error } = await api.GET('/api/v1/lookups/fiscal-years')
      if (error) throw new Error(errorMessage(error, 'Could not load fiscal years'))
      return data
    },
  })
}
```

- `frontend/src/features/lookups/api.ts`: `useFiscalYears`, `useDataSources`,
  `useAccountTypes(dataSource?: string)`, `useCategories` + type aliases from
  `components['schemas'][...]` (e.g. `CategoryListResponse`).
- `frontend/src/features/meta/api.ts`: `useStats`, `useRecordCounts`, `useRecordCountsByYear`,
  `useBuildInfo`; types `DatabaseStats`, `BuildInfo`.
- `frontend/src/features/daily/api.ts`: `useDataByDate(date: string | null)` (`enabled: !!date`),
  `useNetTransfersForDate(date)`, `useNetTransfersForFiscalYear(fy: number | null)`; types
  `TreasuryDataResponse`, `DailyNetTransfer`.
- `frontend/src/features/fiscal-year/api.ts`: `useFiscalYearData({ fiscalYear, dataSource,
  page, pageSize })` → `GET /api/v1/data` with `fiscal_year`, `data_source` (omitted when
  `'all'`), `page`, `page_size`; `placeholderData: keepPreviousData` so paging doesn't flash.

Query keys start with the feature name (`['daily', 'by-date', date]`) — no profile scoping here.

### 3. Shared components

- `frontend/src/components/query-state.tsx` — `QueryState({ query, children })`: pending →
  `<Skeleton className='h-32 w-full' />`; error → `<Alert variant='destructive'>` with
  `query.error.message`; success → `children(query.data)`.
- `frontend/src/components/fiscal-year-select.tsx` — `FiscalYearSelect({ value, onChange,
  label, years })`: shadcn `Select` listing `years` (newest first), value as number.

### 4. Pages

Each route file renders `<Header fixed><h1 className='text-base font-medium'>{title}</h1></Header>`
then `<Main>` around the feature page (as `PagePlaceholder` did). Page components keep state +
queries + composition only (target ≤ 150 lines); pieces go in `components/`, pure logic in
`lib.ts`. Tables use the ReUI `DataGrid` (`components/reui/data-grid/*`, pattern in
`FAM/frontend/src/features/overview/index.tsx`) instead of REF's `components/ui/data-table.tsx`.

| Route file | Page component | Ported from | Notes |
|---|---|---|---|
| `routes/index.tsx` | `features/overview/overview-page.tsx` | `REF/frontend/src/pages/Home.tsx` | 4 stat cards (Total records, Date range, Data sources, Last updated ← `stats.last_updated`), Available data sources, Available fiscal years. Replace the "Quick start" card's 3 items with links to Single date, Year over year → Net transfers, Weekly comparison (drop "Database Management") |
| `routes/data-status.tsx` | `features/data-status/data-status-page.tsx` | new | `useBuildInfo` + `useRecordCounts` + `useRecordCountsByYear`: "Data through {latest_record_date}", "Refreshed {build_date}" (formatted local time), a DataGrid of table → rows, and a short paragraph: updates each business day after the Treasury publishes ~4 pm ET |
| `routes/daily/single-date.tsx` | `features/daily/single-date-page.tsx` | `REF/frontend/src/pages/single-date/DepositsWithdrawals.tsx` | split: `components/date-controls.tsx` (lines 300–322: date input + Search), `components/net-transfers-summary.tsx` (345–497: key metrics, flow details, the calculation-explanation toggle), `components/transactions-table.tsx` (514–536 + the `columns` `useMemo` at 45–298); the warning card (499–512) becomes a `QueryState` error branch |
| `routes/daily/net-transfers.tsx` | `features/daily/net-transfers-page.tsx` | `REF/frontend/src/pages/single-date/CompareDailyNetTransfers.tsx` | two `FiscalYearSelect`s (default: latest two FYs from `useFiscalYears`), `components/fiscal-year-table.tsx` rendered twice side by side (`grid gap-4 lg:grid-cols-2`) |
| `routes/fiscal-year.tsx` | `features/fiscal-year/fiscal-year-page.tsx` | `REF/frontend/src/pages/fiscal-year/FiscalYear.tsx` | **default FY = first item of `useFiscalYears`** (REF hardcodes `2024` at line 16); data-source select from `useDataSources` plus `all`; server pagination via `page`/`page_size` |

`features/daily/lib.ts` holds the pure pieces pulled out of the single-date page (row grouping,
the metric rows the summary renders); `features/daily/lib.test.ts` tests them with one fixture
`DailyNetTransfer` object.

### 5. Mounted page test

`frontend/src/features/overview/overview-page.test.tsx`: `mockApi` with `/api/v1/meta/stats`
(record_count 12345, fiscal_years [2026, 2025], data_sources 9 names, last_updated an ISO
string); render the app router at `/`; assert the formatted record count, both fiscal years, and
a link named `Weekly comparison` pointing to `/weekly`.

## Verification

- [ ] `pnpm typecheck && pnpm test && pnpm build` → pass.
- [ ] `grep -rn "fetch(" frontend/src --include=*.ts --include=*.tsx | grep -v -e lib/api/client.ts -e src/test/` → no output.
- [ ] `grep -rnE "#[0-9a-fA-F]{6}" frontend/src/features frontend/src/components --include=*.tsx` → no output (colors via tokens / `lib/chart.ts` only).
- [ ] `wc -l frontend/src/features/*/*-page.tsx` → each ≤ ~150.
- [ ] `scripts/dev.sh` with the bootstrap artifact: each of the five pages loads real data;
      Single date for a known business day (e.g. the `latest_record_date`) shows the summary and
      table; a weekend date shows the backend's 404 detail text, not a blank page; Fiscal year
      paging to page 2 keeps the previous rows visible until the new page arrives.
- [ ] Side-by-side with REF (`REF/fullstack_app/start-dev.sh`): Overview numbers, Single date
      metrics for the same date, and Fiscal year totals match.
- [ ] Dark mode (add `class="dark"` on `<html>` in DevTools): all five pages readable, no
      hard-coded white backgrounds.
- [ ] Production deploy: same five pages work at `https://dts-webapp.vercel.app`; a second load
      of each page's API calls shows `x-vercel-cache: HIT` in DevTools.

## Notes

(fill in during execution)
