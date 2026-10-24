# Phase 3: In-Context Explanations — ✅ Done

**Goal**: Next to every computed figure in the app there is a small "How is this calculated?"
button that opens the formula's one-line summary and expression from the registry, with a link
to its Methodology section.

## Scope

- In scope: `FormulaHint`, a `hint` prop on `StatCard`, hints on the placements below, rewording
  of page descriptions that restate formulas by hand.
- Out of scope: new formulas, tooltips on chart points, onboarding tours, changes to the
  Methodology page beyond fixing anchors.

Branch: `feat/formula-hints`. Depends on Phase 2.

## Implementation

### 1. `frontend/src/components/formula-hint.tsx`

```tsx
export function FormulaHint({ id }: { id: FormulaId }) // uses FORMULAS[id]
```

- Trigger: shadcn `Button` `variant='ghost' size='icon-xs'` (check `components/ui/button.tsx` for
  the smallest icon size; use it) with lucide `CircleHelp`, `aria-label={`How is ${title} calculated?`}`.
- Content (`PopoverContent`, `w-80 max-w-[calc(100vw-2rem)]`): `title` (font-medium), `summary`,
  `expression` lines in a `font-mono text-xs bg-muted/40 rounded p-2` block, then
  `<Link to='/methodology' hash={id}>Read the full explanation</Link>`.
- Works with keyboard (Popover handles focus and Escape) and touch (tap opens).

### 2. `StatCard` — optional `hint?: FormulaId`

Render `<FormulaHint id={hint} />` after the title inside `CardHeader` (keep the icon on the
right). No other prop changes.

### 3. Placements

| Screen | File | Figure → `FormulaId` |
|---|---|---|
| Single date | `features/daily/components/net-transfers-summary.tsx` | Net flow (today) → `net-transfers`; Leading flow → `leading-flow`; Net flow (FYTD) → `today-mtd-fytd`; Total deposits → `total-deposits`; Total withdrawals → `total-withdrawals`. Keep the existing "How are these numbers calculated?" toggle (it shows the day's own numbers) and add a "Read the full explanation" link at its end |
| Daily net transfers | `features/daily/components/fiscal-year-table.tsx` | Card title → `net-transfers`; "Day" column header → `day-of-fiscal-year` |
| YoY pages | `features/yoy/yoy-analysis-layout.tsx` | Latest YoY change → `yoy-percent`; Average / Largest / Smallest → `yoy-summary`; FY latest FYTD / same point → `comparison-modes` |
| YoY page intros | `net-transfers-page.tsx`, `withdrawals-page.tsx`, `deposits-page.tsx` | Replace hand-written formula text in `description` / `infoAlert` with `FORMULAS[...].summary` + `FormulaHint` (`net-transfers`, `total-withdrawals`, `total-deposits`) |
| Compare-by control | `components/charts/chart-controls.tsx` | Next to the "Compare by" label → `comparison-modes` |
| Category cards | `features/yoy/components/category-card.tsx` (`kind` → id: spending `major-spending`, receipt `major-receipts`, tbill `tbill-interest`, irs_refund `irs-refunds`) | The hint button must not trigger the card's own click (`onClick={(e) => e.stopPropagation()}` on the trigger) |
| Category dialog | `features/yoy/components/category-detail-dialog.tsx` | Dialog title → same id as the card |
| Category comparison | `features/yoy/category-comparison-page.tsx` | Chart card title → `category-comparison` |
| Weekly | `features/weekly/components/summary-stats.tsx` | Latest weekly net transfers FYTD → `weekly-comparison`; Weekly YoY difference → `yoy-difference`; Change → `yoy-percent` |
| Overview | `features/overview/overview-page.tsx` | A "New to Treasury data? Start with the Methodology" link card → `/methodology#start-here` (add `id='start-here'` in Phase 2's chapter 1 if missing) |

## Verification

- [x] `pnpm typecheck && pnpm test && pnpm build` → pass (61 tests).
- [x] `grep -rn "TGA total withdrawals − public debt\|total withdrawals − total deposits" frontend/src/features --include='*.tsx'`
      → no output (formula text only comes from the registry).
- [x] Mounted test `frontend/src/components/formula-hint.test.tsx`: render `<FormulaHint id='net-transfers' />`
      in the router, click the button → the summary and a link with `href` ending
      `/methodology#net-transfers` appear; Escape closes it.
- [x] Browser, 1280 px and 375 px, light and dark: each placement in the table shows the button;
      tapping a category card's hint opens the popover without opening the dialog; the popover
      never overflows the viewport; "Read the full explanation" lands on the right section.
- [x] No console errors; no horizontal scroll on any page.
- [x] Production after merge: same checks on `https://dts-webapp.vercel.app` (2026-10-23,
      bundle `index-CAPG0-uV.js`, same hint counts as local on every page). The only console
      error is `/_vercel/insights/script.js` served as HTML: Vercel Web Analytics is not enabled
      in the dashboard yet (an on-hold launch step), unrelated to the hints.

## Notes

- **Hint label.** `aria-label` is `"<title>: how is this calculated?"`, not
  `"How is <title> calculated?"`: lowercasing the title broke "IRS" and "T-Bill", and plural
  titles ("Major spending categories") read badly in the question form.
- **Category card.** Not `stopPropagation`: a hint button inside a `role='button'` card is a
  nested interactive control (axe `nested-interactive`). The card is now a plain `Card`; the
  category name is a real `<button data-card-open>` whose `::after` stretches over the card, and
  the hint sits beside it with `relative z-10`. The focus ring moved to
  `has-[[data-card-open]:focus-visible]`. `CATEGORY_FORMULA` (kind → id) is exported from
  `category-card.tsx` and reused by the dialog.
- **Daily net transfers.** `fiscal-year-table.tsx` has no card title, so both hints went to
  `YearColumn` in `features/daily/net-transfers-page.tsx`: `net-transfers` next to the `FY ####`
  title and `day-of-fiscal-year` next to the "N days of data" description. The "Day of FY" column
  header got none — its click sorts the column.
- **YoY intros.** `YoYAnalysisLayout` takes `formula: FormulaId` instead of `infoAlert`; every
  YoY page now shows the registry summary plus the hint in one `Alert` (inline, so it wraps with
  the sentence on phones). The descriptions dropped their hand-written formula text.
- **Single date.** The toggle's closing link goes to the `#surplus-or-deficit` chapter rather
  than `#net-transfers`, because the toggle covers deposits, withdrawals and net flow together.
- **Category comparison.** The hint is on `components/comparison-chart.tsx`'s title, which only
  renders once a compared category has rows (Agriculture has none in FY2027 yet; Medicare does).
- **Popover.** `collisionPadding={16}` keeps it 16 px from the screen edge at 375 px.
- **Lighthouse accessibility** on `/yoy/withdrawals` 95, `/weekly` 93, `/daily/net-transfers` 89.
  Every failure predates this phase and none is a hint: `text-success` (#00bc7d on white, 2.47:1)
  fails `color-contrast`; the data grid's page-size select has no name (`button-name`); the
  weekly summary's `h3` skips a level (`heading-order`). All three were fixed afterwards on
  `fix/a11y-contrast`; every page now scores 100.
