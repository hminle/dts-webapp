# Phase 2: Formula Registry & Methodology — ⬜ Not Started

**Goal**: Every formula is defined once in a typed registry, and `/methodology` becomes a
long-form, beginner-friendly explainer built from that registry, with a table of contents, one
anchored section per formula, and the tested worked examples.

## Scope

- In scope: `formulas.ts` + test, `FormulaBlock`, `MethodologyToc`, the rewritten Methodology
  page, removal of the category-comparison `MethodologyCard`, a `CLAUDE.md` note.
- Out of scope: hints on other pages (Phase 3), charts/diagrams beyond simple HTML/CSS boxes
  (no new chart library), MDX or a CMS, translations.

Branch: `feat/formula-methodology`. Depends on Phase 1 (`worked-examples.json` exists and its
test passes). Use the `shadcn` and `minimalist-ui` skills.

## Implementation

### 1. Registry — `frontend/src/features/methodology/formulas.ts`

```ts
export type FormulaId =
  | 'total-deposits' | 'total-withdrawals' | 'net-transfers' | 'leading-flow'
  | 'today-mtd-fytd' | 'fiscal-year' | 'day-of-fiscal-year'
  | 'yoy-difference' | 'yoy-percent' | 'yoy-summary' | 'comparison-modes'
  | 'major-spending' | 'major-receipts' | 'tbill-interest' | 'irs-refunds'
  | 'category-comparison' | 'weekly-comparison'

export type FormulaDef = {
  id: FormulaId            // also the Methodology anchor (#net-transfers)
  title: string            // "Net transfers"
  summary: string          // one sentence, used by hints (≤ 160 chars)
  expression: string[]     // one line per step, using − × ÷ |x| Σ
  terms?: { term: string; meaning: string }[]
  pitfalls?: string[]      // what readers usually get wrong
  source: string           // "Deposits & Withdrawals table (Table II)"
}
export const FORMULAS: Record<FormulaId, FormulaDef>
export const FORMULA_ORDER: FormulaId[]   // Methodology order
```

Content rules: write each `summary`/`expression` from the code in the Phase 0 inventory, not from
the reference docs (they drifted: e.g. the reference lists "Social Security Benefits
(Checks/EFT)" but the code uses `SSA - Benefits Payments`). Category component lists come from
importing nothing backend-side — copy the names from `backend/app/constants/categories.py` and
add a test (below) that keeps them in step.

### 2. `formulas.test.ts`

1. Every `FormulaId` appears exactly once in `FORMULA_ORDER` and has a non-empty `summary` ≤ 160
   chars and ≥ 1 `expression` line.
2. Worked examples add up: for `worked-examples.json`, `tga_deposits − debt_issues ===
   total_deposits` (today and FYTD), same for withdrawals, `net = withdrawals − deposits`,
   `difference = current − previous`, `percent ≈ difference / |previous| × 100` (2 dp), Medicare
   component sums, T-Bill sums, IRS Table V sum = 10,558.
3. Component names: read `backend/app/constants/categories.py` as text with `node:fs`
   (`new URL('../../../../backend/app/constants/categories.py', import.meta.url)`) and assert
   every component string listed in `FORMULAS['major-spending' | 'major-receipts' | 'tbill-interest'
   | 'irs-refunds'].terms` occurs in it. This catches renames on either side.

### 3. Components — `frontend/src/features/methodology/components/`

- `formula-block.tsx` — `FormulaBlock({ id, example? })`: renders `expression` lines in a
  `rounded-lg bg-muted/40 p-4 font-mono text-sm` block, then optional `example` (a `ReactNode`
  table built by the page), then `pitfalls` as a short list under "Common mistakes".
- `methodology-toc.tsx` — the table of contents: on `lg:` a sticky right column
  (`lg:sticky lg:top-20`), on smaller screens a collapsible "On this page" list above the
  content. Links are `<a href='#id'>` (in-page) so the browser scrolls; each section `h2` has
  `id` and `scroll-mt-20` so the sticky header doesn't cover it.

### 4. Page — `frontend/src/features/methodology/methodology-page.tsx`

Rewrite as chapters (each a `ProseSection` with `id`), in this order. Write for a reader who
has never read a Treasury statement; define every term on first use. Render numbers from
`worked-examples.json` with `formatCurrency`/`formatTreasuryValue`/`formatSignedPercent` —
no typed-in figures.

1. **Start here** — what the Daily Treasury Statement (DTS) is; what the Treasury General
   Account (TGA) is (the government's operating account at the Federal Reserve); what the app
   lets you do; "all amounts are millions of dollars" with the scale example.
2. **Reading a statement** (`today-mtd-fytd`, `fiscal-year`, `day-of-fiscal-year`) — today /
   month-to-date / fiscal-year-to-date columns; fiscal year Oct 1–Sep 30 named for its end
   year; quarters table (Q1 Oct–Dec … Q4 Jul–Sep); Day N counts statement days, a day without
   totals keeps its number but has no figures; example: FY2027 day 10 is 2026-10-15, day 12 is
   2026-10-19 (Columbus Day and weekends skipped).
3. **Deposits, withdrawals, and why borrowing is removed** (`total-deposits`,
   `total-withdrawals`) — a simple box diagram: cash in (taxes, fees, *new borrowing*) / cash
   out (benefits, salaries, interest, *repaying debt*); why issues and redemptions are removed;
   the worked example table (today and FYTD columns).
4. **Net transfers** (`net-transfers`, `leading-flow`) — formula; sign meaning (positive = more
   went out than came in before borrowing, i.e. a deficit day; negative = surplus day); the
   2026-10-19 example is a surplus day (−16,755) while FYTD is a deficit (108,932), and why both
   can be true (tax receipts are lumpy). Show these in millions with `formatCurrency` — at
   billions `toFixed` renders 16.755 as "16.75" (binary floating point), which a reader
   checking the arithmetic would notice.
5. **Comparing with a year ago** (`yoy-difference`, `yoy-percent`, `yoy-summary`) — difference;
   percent with |previous| and the negative-base example (+40 %, not −40 %); "no percent" when
   previous is 0; latest / average / largest / smallest across the days shown.
6. **Lining up two years** (`comparison-modes`) — fiscal day vs calendar date with a two-column
   table for day 12 (2026-10-19 ↔ 2025-10-17 vs 2026-10-19 ↔ 2025-10-19 Sunday); the three
   calendar-date rules pinned in Phase 1 (the daily chart drops the date; category cards use the
   latest earlier statement; the category detail chart compares the date with 0);
   when to use which (seasonal deadlines → calendar; pace of the year → fiscal day).
7. **Major spending categories** (`major-spending`) — the four groups with their exact Treasury
   line items in a table; Medicare worked example; "Interest on Treasury Securities" is cash
   interest on notes and bonds — bills pay no cash interest, see next section.
8. **Major receipt categories** (`major-receipts`) — the two groups; the Customs rename
   (old name until 2025-11-07, new from 2025-11-10) and why both names are summed, with the
   worked example.
9. **T-Bill interest** (`tbill-interest`) — bills are sold below face value; the discount is
   their interest, recorded in the public-debt adjustment table as `Bills (-)` and
   `Bonds and Notes (-)`; worked example.
10. **IRS tax refunds** (`irs-refunds`) — four refund types from the Income Tax Refunds table
    (Table V); why not Table II (only EFT lines: $5.22B vs $10.56B on 2026-10-19).
11. **Category comparison** (`category-comparison`) — any Treasury line item, FYTD per day,
    aligned by day number; replaces the deleted `MethodologyCard` content.
12. **Weekly comparison** (`weekly-comparison`) — Friday snapshots of FYTD net transfers, up to
    5 days back for holidays, second year cut at the first year's last week number, weeks matched by
    week number.
13. **Known limits** — keep the three current bullets; add the payment-calendar effect if
    Phase 0's Social Security check is confirmed (see below).
14. **Glossary** — DTS, TGA, FY, FYTD, MTD, YoY, EFT, SSA, HHS, IRS, DHS, Table II/IIIB/V.
15. **Source & update schedule** — keep the current "Source" and "Update schedule" text.

Social Security check (do before writing chapter 13):

```bash
cd backend && uv run python -c "
import duckdb; c=duckdb.connect('data/treasury_data.duckdb', read_only=True)
for fy, a, b in ((2026,'2025-10-01','2025-10-17'), (2027,'2026-10-01','2026-10-19')):
    print(fy, c.execute(\"select record_date, transaction_today_amt from deposits_withdrawals where transaction_type='Withdrawals' and transaction_catg='SSA - Benefits Payments' and record_date between ? and ? and transaction_today_amt > 5000 order by 1\", [a, b]).fetchall())"
```

(After `uv run python -m scripts.fetch_artifact` with `APP_ARTIFACT_URL` set to the public
`latest/` URL.) If the large payments land on the second/third/fourth Wednesdays and the count
differs between the years, write the limit; otherwise leave it out and say so in Notes.

### 5. Remove the duplicate

Delete `frontend/src/features/yoy/components/methodology-card.tsx`; in
`category-comparison-page.tsx` replace `<MethodologyCard />` with a one-line link:
`<Link to='/methodology' hash='category-comparison'>How this comparison is calculated</Link>`.

### 6. `CLAUDE.md`

Under "Frontend architecture" add: "Formula copy lives in `features/methodology/formulas.ts`;
worked-example numbers live in `features/methodology/worked-examples.json`, which
`backend/tests/test_formula_examples.py` checks against the real formula code — change a formula
and both must be updated in the same commit."

## Verification

- [ ] `pnpm typecheck && pnpm test && pnpm build` → pass; `formulas.test.ts` runs.
- [ ] `grep -nE "[0-9]{1,3},[0-9]{3}" frontend/src/features/methodology/methodology-page.tsx` → no
      output (no typed-in figures).
- [ ] Browser (`scripts/dev.sh`, 1280 px and 375 px, light and dark): `/methodology` shows the
      table of contents; clicking each entry scrolls its heading into view below the sticky
      header; `/methodology#tbill-interest` opened directly lands on that section; no horizontal
      scroll.
- [ ] Every worked-example figure on the page matches `worked-examples.json`.
- [ ] Category comparison page shows the link instead of the old card; it lands on
      `#category-comparison`.
- [ ] Lighthouse Accessibility ≥ 90 on `/methodology` (heading order h1 → h2 → h3 only).

## Notes

(record the Social Security check result and any reference-doc drift found)
