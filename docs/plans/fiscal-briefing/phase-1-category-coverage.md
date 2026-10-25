# Phase 1: Category coverage — ⬜ Not Started

**Goal**: Every category knows the first date it can be compared from. A total for an earlier
date is `null`, not a silent `0`. Renamed Treasury lines whose FYTD carries forward are summed
under every name they have had.

Branch: `fix/category-coverage`.

## Scope

In scope:
- `CategoryDef.available_from` for the 8 existing categories, plus the two verified old names
  (`Medicaid`, `Customs and Certain Excise Taxes`).
- Nullable totals and `available_from` in the four "major" responses and in the daily YoY
  response.
- The cards, detail dialog and breakdown table show "—" and "Comparable from <date>" for
  `null`.
- Formula copy, Methodology, the MCP categories skill and tests.

Out of scope:
- New categories (Phase 2).
- Reading `federal_tax_deposits` to extend tax categories before 2023-02-14. The category
  stays not comparable before then.
- The category comparison page (`/yoy/categories`, `yoy_get_category_comparison`). It works on
  raw line items the user picks, not on registry categories, so coverage does not apply.
- Any change to net-transfer formulas.

## Implementation

### 1. Registry — `backend/app/constants/categories.py`

Add `from datetime import date` and the field. Keep `frozen=True`.

```python
# First statement in the artifact; a category comparable from here has no gap.
DATA_START = date(2005, 10, 3)


@dataclass(frozen=True)
class CategoryDef:
    """A single named bucket and its component upstream identifiers.

    ``available_from`` is the first date the bucket means the same thing it
    means today. Before it the Treasury split, merged or moved the lines, so
    a total would compare different things; services return ``None`` instead.
    """

    name: str
    kind: CategoryKind
    components: tuple[str, ...]
    available_from: date
```

Set the values exactly as below. Component order: today's name(s) first, old names after.

| Category | `components` | `available_from` |
|---|---|---|
| Social Security Benefits | unchanged (3 lines) | `date(2021, 7, 19)` |
| Medicare | unchanged (3 lines) | `date(2020, 3, 9)` |
| Medicaid | `("HHS - Grants to States for Medicaid", "Medicaid")` | `DATA_START` |
| Interest on Treasury Securities | unchanged | `DATA_START` |
| Employment & Withholding Tax | unchanged | `date(2023, 2, 14)` |
| Customs & Duties (Tariffs) | `("DHS - Customs Duties, Taxes, and Fees", "DHS - Customs and Certain Excise Taxes", "Customs and Certain Excise Taxes")` | `DATA_START` |
| T-Bill Interest | unchanged | `date(2022, 9, 12)` |
| IRS Tax Refunds | unchanged | `date(2023, 2, 14)` |

Above each non-`DATA_START` value, add a one-line comment giving the reason (for example
`# SSI and SSA misc became separate lines on 2021-07-19.`). Phase 0's "Treasury line history"
table has the reasons. The existing customs comment about the November 2025 rename stays.
Extend it to mention the May 2020 rename.

**Customs component order changes**: today it is `(OLD_CUSTOMS, NEW_CUSTOMS)`. The new order
puts today's name first. Update the test constant usage accordingly (see §6).

### 2. Coverage helper — `backend/app/utils/yoy.py`

Add, after `yoy_change`:

```python
def covered(available_from: date, day: str | None) -> bool:
    """Whether ``day`` (ISO date) is on or after ``available_from``.

    An empty or missing day is never covered.
    """
    return bool(day) and date.fromisoformat(day) >= available_from


def nullable_yoy(
    current: float | None, previous: float | None
) -> tuple[float | None, float | None]:
    """``yoy_change`` that passes ``None`` through when either side is missing."""
    if current is None or previous is None:
        return None, None
    return yoy_change(current, previous)
```

Import `date` from `datetime`.

### 3. Schemas — `backend/app/schemas/treasury.py`

Change **only** these fields; descriptions get "null when the date is before
`available_from`":

- `MajorSpendingCategory` and `MajorReceiptCategory`: `current_fytd: float | None`,
  `previous_fytd: float | None`, `yoy_change: float | None`; add
  `available_from: str = Field(..., description="First comparable date (ISO)")`.
- `TBillInterestResponse` and `IrsRefundResponse`: `total_current_fytd`,
  `total_previous_fytd`, `total_yoy_change` become `float | None`; add `available_from: str`.
- `CategoryDailyYoYDataPoint`: `current_fytd`, `previous_fytd`, `yoy_change` become
  `float | None`.
- `CategoryDailyYoYResponse`: add `available_from: str`.

`SubcategoryBreakdown`, `TBillInterestComponent` and `IrsRefundComponent` stay `float`. They
are raw per-line values.

### 4. Service — `backend/app/services/categories.py`

- `_build_subcategory_breakdown` keeps returning raw sums. Add a wrapper used by the four
  endpoints:

```python
def _covered_totals(
    cat: CategoryDef,
    current_date: str,
    previous_date: str,
    total_current: float,
    total_previous: float,
) -> tuple[float | None, float | None]:
    """The totals, or ``None`` for a side whose date predates the category."""
    return (
        total_current if covered(cat.available_from, current_date) else None,
        total_previous if covered(cat.available_from, previous_date) else None,
    )
```

- In `get_major_spending` / `get_major_receipts`, after `_build_subcategory_breakdown`,
  call `_covered_totals`, then `nullable_yoy`. Pass `available_from=cat.available_from.isoformat()`.
- In `get_tbill_interest` / `get_irs_tax_refunds`, apply the same to the totals with
  `TBILL_INTEREST_CATEGORY` / `IRS_REFUND_CATEGORY`. Note that `previous_date == ""` (no
  aligned date) now yields `None`, where today it yields `0.0`.
- In `get_daily_yoy`:
  - Each data point: `curr_fytd` becomes `None` when `not covered(cat_info.available_from,
    curr_date)`.
  - `prev_fytd` becomes `None` when `prev_date is None` or not covered.
  - `yoy_delta, yoy_percent = nullable_yoy(curr_fytd, prev_fytd)`. Replace the two inline
    percent computations.
  - Add `available_from=cat_info.available_from.isoformat()` to the response.

### 5. MCP skill

- `backend/app/mcp_server/skills.py` `_render_categories()`: under each category heading add
  the line `Comparable from: <available_from ISO>` before the component list.
- `backend/app/mcp_server/skills/categories.md`: add a pitfall bullet:
  "A category is compared only from its first comparable date. Before it the Treasury
  restructured the lines, so API totals are `null`, not 0. Renamed lines are summed under all
  their names; on any one date only one name exists."

### 6. Backend tests

`backend/tests/test_formula_categories.py`:
- `test_the_category_groups_match_the_methodology`:
  - Update the Medicaid and customs tuples to the new orders and names.
  - Add an `available_from` assertion dict for all 8 categories with the dates in §1.
  - Add `"Customs and Certain Excise Taxes"` as `OLDEST_CUSTOMS`.
- New `test_a_total_before_available_from_is_none`:
  - Seed Employment & Withholding Tax on CUR = 2026-10-19 (FY2027) and on a previous date
    2023-02-10 (FY2023, before 2023-02-14).
  - Call `get_major_receipts` with `current_fiscal_year=2027, previous_fiscal_year=2023`.
  - Assert `previous_fytd is None`, `yoy_change is None`, `yoy_percent_change is None`,
    `available_from == "2023-02-14"`.
  - Assert `current_fytd` equals the seeded value.
- New `test_medicaid_sums_its_old_name`: seed `Medicaid` (withdrawal) on a FY2020 date before
  2020-03-09, and `HHS - Grants to States for Medicaid` on a FY2021 date. Compare
  FY2021 vs FY2020 and assert both totals are non-null and equal the seeded values.
- New `test_customs_compares_across_the_2020_rename`: same pattern with
  `Customs and Certain Excise Taxes` (FY2019) vs `DHS - Customs and Certain Excise Taxes`
  (FY2020).
- Rename `test_category_detail_calendar_mode_compares_a_missing_date_with_zero` to
  `test_category_detail_calendar_mode_has_no_previous_for_a_missing_date`. Assert
  `previous_fytd is None` and `yoy_change is None` where it asserted 0.
- New `test_category_detail_is_none_before_available_from`: daily YoY for T-Bill Interest
  with a previous-year point dated 2022-09-09. Assert that point's `previous_fytd is None`.

`backend/tests/test_mcp_skills.py::test_categories_placeholder`: assert the rendered text
contains `Comparable from: 2021-07-19`.

`backend/tests/test_formula_examples.py`: the worked examples (FY2027 vs FY2026) are after
every `available_from`, so they must stay green unchanged. Do not edit them.

### 7. Frontend

`frontend/src/features/yoy/lib.ts`:
- `CategoryCardData`: `current_fytd: number | null`, `previous_fytd: number | null`,
  `yoy_change: number | null`, add `availableFrom: string`.
- `spendingCards` / `receiptCards`: map `available_from` → `availableFrom`; for T-bill and IRS
  use `tbill.available_from` / `irs.available_from`.
- `breakdownRows`: drop rows where `current === 0 && previous === 0` (an old line name absent
  in both years). Keep every other row.
- `spendingAccent` takes `number | null`; `null` → `'increase'` (neutral border; the card
  shows no trend icon, see below).

`frontend/src/features/yoy/components/category-card.tsx`:
- Value: `category.current_fytd === null ? '—' : formatBillions(category.current_fytd)`.
- Change row: when `category.yoy_change === null`, render instead
  `<span className='text-xs text-muted-foreground'>Comparable from {formatDate(category.availableFrom)}</span>`.
  Show no trend icon and no percent.

`frontend/src/features/yoy/components/category-detail-dialog.tsx`:
- The four `Stat`s render `'—'` for `null` values. The YoY change stat shows no icon when
  `null`.
- Under the stats, when either total is `null`, add
  `<p className='text-sm text-muted-foreground'>This category is comparable from {formatDate(category.availableFrom)}. The Treasury reorganized its lines before that date.</p>`.
- Tooltip: `formatBillions` calls guard `null` → `'—'`, and the YoY line is
  `p.yoy_change === null ? 'YoY change: —' : …`. Recharts skips `null` points, so the line
  shows a gap. Do not set `connectNulls`.

`frontend/src/features/yoy/components/breakdown-table.tsx`: the `total` prop's three fields
become `number | null`; render `'—'` for `null`.

`frontend/src/features/yoy/lib.test.ts`:
- Update the fixtures with `available_from`.
- Add `it('passes a null total through and keeps availableFrom')`.
- Add `it('drops breakdown rows that are zero in both years')`.

`frontend/src/features/methodology/formulas.ts`:
- Add `'category-coverage'` to `FormulaId` and to `FORMULA_ORDER`, right after
  `'irs-refunds'`.
- Add the entry:
  - title `'When a category can be compared'`
  - summary (≤160 chars) `'A category is compared only from the date its Treasury lines took their current shape; earlier totals are blank, not zero.'`
  - expression `['Total on a date = Σ FYTD of its lines, if date ≥ first comparable date', 'Otherwise: no value']`
  - `terms`: one `{ term: <category name>, meaning: 'Comparable from <YYYY-MM-DD>' }` per
    category, for the 8 categories (use `'October 2005 (all data)'` for `DATA_START`)
  - pitfalls: `['A renamed line is summed under every name it has had; only one name exists on any date.']`
  - `source: DEPOSITS_TABLE`
- `major-spending` terms: add `{ term: 'Medicaid', meaning: 'Medicaid' }`.
- `major-receipts` terms: add `{ term: 'Customs & Duties (Tariffs)', meaning: 'Customs and Certain Excise Taxes' }`.

`frontend/src/features/methodology/methodology-page.tsx`, section `known-limits`:
- Replace the bullet "Category names follow the Treasury's own labels…" with: "The Treasury
  has renamed and reorganized its lines over the years. Each category is compared only from
  the date its lines took their current shape:", followed by `<FormulaBlock id='category-coverage' />`.

### 8. Contract

```bash
cd backend && uv run python -m scripts.export_openapi
cd ../frontend && pnpm gen:api
```

Then fix every TypeScript error `pnpm typecheck` reports. The nullable fields surface every
place that formats a total.

## Verification

- [ ] `cd backend && uv run pytest` passes, including the 5 new or renamed tests in
      `test_formula_categories.py`.
- [ ] `uv run ruff check . && uv run ruff format --check .` clean.
- [ ] `git diff --stat docs/contracts/openapi.json` shows the nullable fields and
      `available_from`. `grep -c available_from docs/contracts/openapi.json` returns ≥ 5.
- [ ] `cd frontend && pnpm typecheck && pnpm test` pass. `formulas.test.ts` passes with the
      new Medicaid and customs terms.
- [ ] Manual check with `scripts/dev.sh` and the real artifact (`uv run python -m
      scripts.fetch_artifact`):
  - `/yoy/withdrawals` with FY2021 vs FY2020 shows the Social Security card value but
    "Comparable from Jul 19, 2021" instead of a change.
  - FY2027 vs FY2026 shows the same numbers as before this phase.
- [ ] `curl -s 'localhost:8000/api/v1/categories/major-receipts?current_fiscal_year=2027&previous_fiscal_year=2026' | jq '.categories[] | {name, available_from, yoy_change}'`
      shows non-null changes and the two `available_from` dates `2023-02-14` and `2005-10-03`.
- [ ] MCP: `get_skills("categories")` shows `Comparable from:` lines.

## Notes

- The existing worked examples compare FY2027 with FY2026, after every coverage date, so no
  published number changes.
- `fetch_component_fytd` keeps returning `0.0` for a missing component. That is correct at
  line level. Coverage is decided at category level only.
