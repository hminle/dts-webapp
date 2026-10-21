# Phase 3: In-Context Explanations — ⬜ Not Started

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

- [ ] `pnpm typecheck && pnpm test && pnpm build` → pass.
- [ ] `grep -rn "TGA total withdrawals − public debt\|total withdrawals − total deposits" frontend/src/features --include='*.tsx'`
      → no output (formula text only comes from the registry).
- [ ] Mounted test `frontend/src/components/formula-hint.test.tsx`: render `<FormulaHint id='net-transfers' />`
      in the router, click the button → the summary and a link with `href` ending
      `/methodology#net-transfers` appear; Escape closes it.
- [ ] Browser, 1280 px and 375 px, light and dark: each placement in the table shows the button;
      tapping a category card's hint opens the popover without opening the dialog; the popover
      never overflows the viewport; "Read the full explanation" lands on the right section.
- [ ] No console errors; no horizontal scroll on any page.
- [ ] Production after merge: same checks on `https://dts-webapp.vercel.app`.

## Notes

(record placements that needed a different id or layout)
