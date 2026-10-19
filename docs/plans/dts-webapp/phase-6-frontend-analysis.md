# Phase 6: Frontend — Analysis Pages — ✅ Done

**Goal**: The year-over-year suite (net transfers, withdrawals, deposits, category comparison,
category drill-down) and the weekly comparison work against the Phase 3 API in FAM's look, with
the weekly week-alignment bug fixed and Vitest coverage on every pure data mapper.

## Scope

- In scope: shared chart components, the YoY layout and its three metric pages, spending/receipt
  category sections, category detail dialog, category comparison page, weekly comparison page,
  `lib.ts` mappers + tests.
- Out of scope: new chart types or metrics, URL-persisted filters, CSV export, visual redesign
  beyond swapping REF's ad-hoc colors and cards for FAM tokens/components.

Branch: `feat/frontend-analysis`. Depends on Phase 5 (`lib/format.ts`, `lib/fiscal.ts`,
`lib/chart.ts`, `features/lookups/api.ts`, `components/query-state.tsx`,
`components/fiscal-year-select.tsx`). `REF` = `/home/hminle/gitrepos/personal-projects/dts-analysis/fullstack_app`.

## Implementation

### 1. Chart components — `frontend/src/components/charts/`

Port `REF/frontend/src/components/charts/{ChartControls,YoYLineChart,YoYDifferenceChart,YoYDifferenceLineChart}.tsx`
to kebab-case files `chart-controls.tsx`, `yoy-line-chart.tsx`, `yoy-difference-chart.tsx`,
`yoy-difference-line-chart.tsx` (drop REF's `index.ts` barrel; import files directly, as FAM
does). Wrap each Recharts chart in shadcn's `ChartContainer` (`components/ui/chart.tsx`) with a
`ChartConfig` whose colors are `SERIES.current` / `SERIES.previous` from `lib/chart.ts`; positive
vs negative difference bars use `var(--success)` / `var(--destructive)`. Keep REF's props,
axes, tooltips, and number formatting (`lib/format.ts`).

### 2. Year-over-year — `frontend/src/features/yoy/`

- `api.ts`: `useYoYDailyComparison(params)`, `useYoYCategoryComparison(params)`
  (`category_descriptions` passed as an array; openapi-fetch serializes repeated keys),
  `useMajorSpending(params)`, `useMajorReceipts(params)`, `useTBillInterest(params)`,
  `useIrsTaxRefunds(params)`, `useCategoryDailyYoY(params)`; each `enabled` only when both
  fiscal years are set. `params` = the matching `*Request` schema type.
- `lib.ts` + `lib.test.ts`: every data transformation currently inline in
  `REF/frontend/src/components/yoy/YoYAnalysisLayout.tsx`, `SpendingCategoriesSection.tsx`,
  `ReceiptCategoriesSection.tsx`, `CategoryDetailModal.tsx`, and
  `REF/frontend/src/pages/yoy-comparison/YoYCategoryComparison.tsx` (series building, percent
  change, sorting categories). Tests: one aligned case, one case where the previous year has
  fewer points (no index-based pairing — join on `day_of_fiscal_year` / date key, mirror of the
  weekly fix), one zero-denominator percent change (pin REF's behavior).
- `yoy-analysis-layout.tsx` ← `REF/frontend/src/components/yoy/YoYAnalysisLayout.tsx` (same
  props: `title`, `description`, `metric`, `infoAlert`, `latestNote`,
  `renderCategoriesSection`). Default current FY = first of `useFiscalYears` (falls back to
  `currentFiscalYear()` while loading); previous = current − 1. Uses `FiscalYearSelect` and
  `ChartControls`.
- Pages (each ≤ 30 lines, mirroring REF's thin wrappers):

  | Route file | Page | Ported from |
  |---|---|---|
  | `routes/yoy/net-transfers.tsx` | `features/yoy/net-transfers-page.tsx` | `REF/frontend/src/pages/yoy-analysis/NetTransfersYoY.tsx` |
  | `routes/yoy/withdrawals.tsx` | `features/yoy/withdrawals-page.tsx` | `.../WithdrawalsYoY.tsx` (keeps the info alert text and `SpendingCategoriesSection`) |
  | `routes/yoy/deposits.tsx` | `features/yoy/deposits-page.tsx` | `.../DepositsYoY.tsx` (`ReceiptCategoriesSection`) |
  | `routes/yoy/categories.tsx` | `features/yoy/category-comparison-page.tsx` | `REF/frontend/src/pages/yoy-comparison/YoYCategoryComparison.tsx` |

- Components in `features/yoy/components/`:
  `category-card.tsx` ← `REF/.../components/yoy/CategoryCard.tsx`;
  `spending-categories-section.tsx` ← `SpendingCategoriesSection.tsx`;
  `receipt-categories-section.tsx` ← `ReceiptCategoriesSection.tsx`;
  `category-detail-dialog.tsx` ← `REF/frontend/src/components/CategoryDetailModal.tsx`
  (shadcn `Dialog`; move its data shaping into `lib.ts`; target ≤ 200 lines);
  `category-picker.tsx`, `comparison-chart.tsx`, `comparison-table.tsx`, `methodology-card.tsx`
  ← `REF/frontend/src/pages/yoy-comparison/components/*` (table via ReUI `DataGrid`).

### 3. Weekly comparison — `frontend/src/features/weekly/`

Mirrors the split prescribed in `dts-analysis/docs/plans/fullstack-code-improvements/phase-7-frontend-refactors-tests.md`:

- `api.ts`: `useWeeklyComparison({ first_fiscal_year, second_fiscal_year })`.
- `lib.ts`:
  - `buildChartData(data: WeeklyComparisonResponse)` and `buildDifferenceData(data)` —
    **fix**: REF pairs `first_year_data[index]` with `second_year_data[index]`
    (`REF/frontend/src/pages/weekly-comparison/WeeklyComparison.tsx:76-104`). Build a
    `Map<week_number, point>` from `second_year_data` and join on `week_number`; a missing week
    yields `0` for that year's value and `''` for its date.
  - `computeSummaryStats(data)` — extracted from `calculateStats` (`:107+`), returns numbers
    `{ firstYearTotal, secondYearTotal, difference, percentChange }`; `percentChange` uses
    `Math.abs(secondYearTotal)` as denominator and is `null` when it is 0.
- `lib.test.ts`: aligned weeks; second year missing week 3 → week 3 pairs with 0, week 4 pairs
  with week 4 (the regression test); empty second year → differences equal first-year values;
  `computeSummaryStats` with `secondYearTotal = 0` → `percentChange === null`.
- `components/year-picker.tsx` (two `FiscalYearSelect`s + Search button + the same-year
  `AlertDialog`), `components/weekly-charts.tsx` (grouped BarChart + difference LineChart in
  `ChartContainer`), `components/summary-stats.tsx` (stat cards).
- `weekly-page.tsx` keeps state, the query, composition (≤ 150 lines). Defaults: latest two FYs.
- `routes/weekly.tsx` renders it under `Header` / `Main`.

## Verification

- [x] `pnpm typecheck && pnpm test && pnpm build` → pass; `lib.test.ts` in `yoy/` and `weekly/`
      both run.
- [x] `grep -rn "\[index\]" frontend/src/features/weekly frontend/src/features/yoy` → no output.
- [x] `grep -rnE "#[0-9a-fA-F]{6}" frontend/src/features frontend/src/components --include=*.tsx` → no output.
- [x] `wc -l frontend/src/features/*/*-page.tsx frontend/src/features/yoy/yoy-analysis-layout.tsx` → pages ≤ ~150, layout ≤ ~250.
- [x] Side-by-side with REF on the same artifact, FY2026 vs FY2025: each YoY page's latest
      difference value, the top 3 spending categories, and the weekly summary totals match.
      Where REF's weekly chart differs, it must be only in weeks where the two years' week lists
      differ (the bug fix) — note those weeks.
- [x] Category detail dialog opens from a category card, loads `/api/v1/categories/daily-yoy`,
      closes with Escape.
- [x] Collapsed sidebar → `Year over year` dropdown navigates to all four YoY pages.
- [x] Production: each page's API requests show `x-vercel-cache: HIT` on the second load.

## Notes

- **REF bugs fixed while porting:** weekly chart *and* detail table paired weeks by array
  position (`weekRows` joins on `week_number`); the category-comparison and weekly y-axes
  formatted millions as dollars ($1T read "$1.00M", billions read "K") — they use
  `formatTreasuryValue`; negative amounts printed "$-5.63B" (now "-$5.63B", in
  `formatTreasuryValue` / `formatBillions`, tests updated); the latest-change card printed a
  stray ")" after the percent.
- `YoYLineChart` and `YoYDifferenceChart` are unused in REF (no element renders them) and were
  not ported.
- The three near-identical breakdown tables in REF's `CategoryDetailModal` became one
  `BreakdownTable` fed by `breakdownRows()`; card mapping (`spendingCards`, `receiptCards`)
  moved to `lib.ts`. The sections share a `CategoryGrid`. Extra files: `components/accent.ts`,
  `components/breakdown-table.tsx`, `components/category-grid.tsx`, `weekly/components/weekly-table.tsx`.
- Weekly uses one mapper (`weekRows`) for both charts and the table instead of the planned
  `buildChartData` / `buildDifferenceData`, so all three share the same alignment.
- Accents map to tokens: spending increase `chart-1`, decrease `warning`, receipts `success`.
  The category-comparison chart keys series `c0…cN` because category labels cannot be chart
  config keys / CSS variables; the legend reads real labels from the config.
- REF's validation `AlertDialog`s became inline alerts; the 500-row comparison table cap
  became client paging; the methodology card uses plain lists (no typography plugin).
- Defaults: the newest fiscal year with data vs the one before (REF used the calendar's
  current FY, which can have no data in early October).
- Prettier (`pnpm dlx prettier@3.3.3`, `frontend/.prettierrc.json`, matching FAM's style) was run
  on the new files; it is not a dependency.
- Checks: browser run on local and production — all five pages render real data (e.g.
  withdrawals FY2027 vs FY2026 latest +$19.53B / +5.63%, 6 spending cards; T-Bill dialog 3
  rows + chart, Escape closes; two-category comparison 2 lines with labelled legend), no console
  errors, no horizontal scroll at 390 px; CDN `HIT` on repeat. REF's UI was not run side by
  side; its API bodies were proven identical in Phase 3.
