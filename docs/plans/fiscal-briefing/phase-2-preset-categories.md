# Phase 2: Preset categories — ⬜ Not Started

**Goal**: Add 14 categories that the newsletter tracks and the app lacks: 10 spending and
4 receipt. Each gets the same card, detail dialog and year-over-year treatment as the major
categories. They appear in an "Other categories" grid under the major grid on the
Withdrawals and Deposits YoY pages.

Branch: `feat/preset-categories`. Depends on Phase 1 (`available_from`).

## Scope

In scope:
- Two registry tuples, two endpoints, two frontend sections, formula copy, tests.

Out of scope:
- Combined figures such as interest income transfers or net customs (Phase 4).
- Changing the four major spending or two major receipt categories.
- Reproducing the newsletter's HUD/SNAP change bug. Our change always uses the same lines as
  our total.

## Implementation

### 1. Registry — `backend/app/constants/categories.py`

Add after `MAJOR_RECEIPT_CATEGORIES` (exact names, components, dates; component order as
written):

```python
# ── Other spending (withdrawals) ──────────────────────────────────────
OTHER_SPENDING_CATEGORIES: tuple[CategoryDef, ...] = (
    CategoryDef(
        name="Department of Defense",
        kind="spending",
        components=("Dept of Defense (DoD) - misc",),
        # FY2024 split "Defense Vendor Payments (EFT)" into DoD misc, health and pay.
        available_from=date(2023, 10, 2),
    ),
    CategoryDef(
        name="Military Pay",
        kind="spending",
        components=("DoD - Military Active Duty Pay", "DoD - Military Retirement"),
        available_from=date(2023, 10, 2),
    ),
    CategoryDef(
        name="Federal Salaries",
        kind="spending",
        components=("Federal Salaries (EFT)",),
        available_from=DATA_START,
    ),
    CategoryDef(
        name="Healthcare Subsidies (Marketplace)",
        kind="spending",
        components=("HHS - Marketplace Payments", "Marketplace Payments"),
        # The line starts with the ACA marketplace payments in FY2015.
        available_from=date(2014, 10, 1),
    ),
    CategoryDef(
        name="Department of Education",
        kind="spending",
        components=("Dept of Education (ED)", "Education Department programs"),
        available_from=DATA_START,
    ),
    CategoryDef(
        name="Housing & Urban Development",
        kind="spending",
        components=(
            "Dept of Housing & Urban Dev (HUD) - misc",
            "HUD - Federal Housing Admin (FHA)",
            "Housing and Urban Development programs",
        ),
        available_from=DATA_START,
    ),
    CategoryDef(
        name="SNAP & WIC",
        kind="spending",
        components=(
            "USDA - Supp Nutrition Assist Prog (SNAP)",
            "USDA - Supp Nutrition Assist Prog (WIC)",
        ),
        # WIC became its own line on 2020-11-16; before, it sat in a misc USDA line.
        available_from=date(2020, 11, 16),
    ),
    CategoryDef(
        name="Veterans Benefits",
        kind="spending",
        components=("VA - Benefits",),
        available_from=date(2020, 1, 13),
    ),
    CategoryDef(
        name="Unemployment Benefits",
        kind="spending",
        components=("DOL - Unemployment Benefits", "Unemployment Insurance Benefits"),
        available_from=DATA_START,
    ),
    CategoryDef(
        name="Customs Refunds (CBP)",
        kind="spending",
        components=("DHS - Customs & Border Protection (CBP)",),
        # All CBP payments; since 2026 they are mostly tariff refunds.
        available_from=date(2020, 5, 11),
    ),
)

# ── Other receipts (deposits) ─────────────────────────────────────────
OTHER_RECEIPT_CATEGORIES: tuple[CategoryDef, ...] = (
    CategoryDef(
        name="Individual Income Taxes",
        kind="receipt",
        components=(
            "Taxes - Non Withheld Ind/SECA Electronic",
            "Taxes - Non Withheld Ind/SECA Other",
        ),
        available_from=date(2023, 2, 14),
    ),
    CategoryDef(
        name="Corporate Income Taxes",
        kind="receipt",
        components=("Taxes - Corporate Income",),
        available_from=date(2023, 2, 14),
    ),
    CategoryDef(
        name="Education Receipts (Student Loans)",
        kind="receipt",
        components=("Dept of Education (ED)", "Education Department programs"),
        available_from=DATA_START,
    ),
    CategoryDef(
        name="Public Debt Cash Issues",
        kind="receipt",
        components=(
            "Public Debt Cash Issues (Table IIIB)",
            "Public Debt Cash Issues (Table III-B)",
        ),
        available_from=DATA_START,
    ),
)
```

Add both tuples to `CATEGORY_REGISTRY` (after the major tuples). Names must stay unique: the
registry is keyed by name. `Department of Education` and `Education Receipts (Student
Loans)` share component strings but differ by `kind`, which selects the withdrawals or
deposits side.

### 2. Service — `backend/app/services/categories.py`

Refactor `get_major_spending` and `get_major_receipts` into one private worker, then add two
thin public functions:

```python
def _category_yoy(
    cur: duckdb.DuckDBPyConnection,
    request: MajorSpendingCategoriesRequest | MajorReceiptCategoriesRequest,
    source: FYTDSource,
    defs: tuple[CategoryDef, ...],
    label: str,
) -> tuple[str, str, ComparisonMode, list[dict]]:
    """Validate, resolve dates and build one dict per category (Phase 1 coverage rules)."""
```

It returns the fields shared by `MajorSpendingCategory` and `MajorReceiptCategory`. The public
functions wrap the dicts into their model and build the response:

- `get_major_spending(cur, request)`: `_SPENDING_SOURCE`, `MAJOR_SPENDING_CATEGORIES`.
- `get_other_spending(cur, request)`: `_SPENDING_SOURCE`, `OTHER_SPENDING_CATEGORIES`, returns
  `MajorSpendingCategoriesResponse`.
- `get_major_receipts(cur, request)`: `_RECEIPT_SOURCE`, `MAJOR_RECEIPT_CATEGORIES`.
- `get_other_receipts(cur, request)`: `_RECEIPT_SOURCE`, `OTHER_RECEIPT_CATEGORIES`, returns
  `MajorReceiptCategoriesResponse`.

Log lines keep today's shape, with the label ("Major spending", "Other spending", …).
Behaviour of the two existing functions must not change: their existing tests stay green
untouched.

### 3. Router — `backend/app/api/routers/categories.py`

Add after `get_major_receipts`:

```python
@router.get("/other-spending", response_model=MajorSpendingCategoriesResponse)
def get_other_spending(
    cur: CursorDep, req: Annotated[MajorSpendingCategoriesRequest, Query()]
) -> MajorSpendingCategoriesResponse:
    """FYTD spending of the other preset categories, with YoY change."""
    return categories.get_other_spending(cur, req)


@router.get("/other-receipts", response_model=MajorReceiptCategoriesResponse)
def get_other_receipts(
    cur: CursorDep, req: Annotated[MajorReceiptCategoriesRequest, Query()]
) -> MajorReceiptCategoriesResponse:
    """FYTD receipts of the other preset categories, with YoY change."""
    return categories.get_other_receipts(cur, req)
```

The operation ids become `categories_get_other_spending` and `categories_get_other_receipts`.

### 4. Backend tests

`backend/tests/test_formula_categories.py`:
- `test_the_other_category_groups`: assert `{c.name: (c.components, c.available_from)}` for
  both new tuples equals the table in §1, written out literally.
- `test_registry_names_are_unique`:
  `len(CATEGORY_REGISTRY) == len(MAJOR_SPENDING_CATEGORIES) + len(MAJOR_RECEIPT_CATEGORIES) + len(OTHER_SPENDING_CATEGORIES) + len(OTHER_RECEIPT_CATEGORIES) + 2`.
- `test_other_spending_sums_both_snap_lines`: seed SNAP = 17,542 and WIC = 1,261 withdrawals on
  2025-12-04 (FY2026), SNAP = 19,412 and WIC = 1,356 on 2024-12-04 (FY2025). Assert
  SNAP & WIC `current_fytd == 18,803`, `previous_fytd == 20,768`, `yoy_change == -1,965`.
  These are the real statement values. The newsletter printed −1.9 because it used SNAP only
  (17,542 − 19,412 = −1,870).
- `test_education_reads_each_side`: seed `Dept of Education (ED)` as a withdrawal of 25,834
  and a deposit of 11,852 on the same date. Assert `Department of Education` (other spending)
  is 25,834 and `Education Receipts (Student Loans)` (other receipts) is 11,852.
- `test_other_receipts_are_none_before_2023_02_14`: Individual Income Taxes, FY2027 vs FY2023,
  with the previous date 2023-02-10, gives `previous_fytd is None`.

`backend/tests/test_analysis_api.py`: add the two routes to the `test_analysis_routes_answer`
parametrize list with `YEARS`.

### 5. Frontend

`frontend/src/features/yoy/api.ts`: add `useOtherSpending(pair)` and `useOtherReceipts(pair)`,
copies of `useMajorSpending` / `useMajorReceipts`:
- query keys `['yoy', 'other-spending', pair]` and `['yoy', 'other-receipts', pair]`
- paths `/api/v1/categories/other-spending` and `/other-receipts`
- error messages `'Could not load other spending categories'` / `'…receipt categories'`

`frontend/src/features/yoy/lib.ts`:
- `CategoryCardData` gains `formula: FormulaId` (import the type from
  `@/features/methodology/formulas`).
- `spendingCards` sets `'major-spending'` on major cards, `'tbill-interest'` on T-bill and
  `'irs-refunds'` on IRS. `receiptCards` sets `'major-receipts'`.
- New `otherSpendingCards(data: MajorSpending | undefined)` builds cards with
  `categoryType: 'spending'`, `formula: 'other-spending'` and the spending accent.
- New `otherReceiptCards(data: MajorReceipts | undefined)` builds cards with
  `categoryType: 'receipt'`, `formula: 'other-receipts'` and `accent: 'receipt'`.

`frontend/src/features/yoy/components/category-card.tsx` and `category-detail-dialog.tsx`:
replace `CATEGORY_FORMULA[category.categoryType]` with `category.formula`. Delete the
`CATEGORY_FORMULA` export. `grep -rn CATEGORY_FORMULA frontend/src` must then return nothing.

Create `frontend/src/features/yoy/components/other-spending-section.tsx`. Copy
`receipt-categories-section.tsx` and change:
- the hook → `useOtherSpending`
- the cards → `otherSpendingCards`
- the title → `'Other spending categories'`
- `periodDescription('spending', …)`

Create `other-receipts-section.tsx` the same way:
- the hook → `useOtherReceipts`
- the cards → `otherReceiptCards`
- the title → `'Other receipt categories'`
- `periodDescription('receipts', …)`

`withdrawals-page.tsx`: `renderCategoriesSection={(pair) => (<><SpendingCategoriesSection pair={pair} /><OtherSpendingSection pair={pair} /></>)}`.
`deposits-page.tsx`: same with `ReceiptCategoriesSection` + `OtherReceiptsSection`.
If `YoYAnalysisLayout` wraps the render result in a flex column, the two grids stack with its
gap. If it does not, wrap them in `<div className='flex flex-col gap-6'>`.

`frontend/src/features/yoy/lib.test.ts`:
- `it('builds other spending cards with their own formula')`
- `it('sets the formula on every major card')`

### 6. Formula copy

`frontend/src/features/methodology/formulas.ts`:
- Add `'other-spending'` and `'other-receipts'` to `FormulaId`. In `FORMULA_ORDER` they go
  after `'major-receipts'`.
- `other-spending`:
  - title `'Other spending categories'`
  - summary `'Ten more groups of withdrawal line items, each the sum of the items’ fiscal-year-to-date amounts.'`
  - expression `['Category FYTD = Σ FYTD of its withdrawal line items']`
  - `terms`: one `{ term, meaning }` per component, in §1 order, every component string exactly
    as in Python
  - pitfalls:
    - `'Customs Refunds (CBP) is every Customs and Border Protection payment; since 2026 most of it is tariff refunds.'`
    - `'Department of Defense is the DoD misc line only; military pay and DoD health are separate lines.'`
  - `source: DEPOSITS_TABLE`
- `other-receipts`: the same shape, with summary `'Four more groups of deposit line items.'`
  and pitfall `'Public debt cash issues is borrowing, not revenue; net transfers exclude it.'`.
- Update the `major-spending` summary from "Four groups…" to "The four largest groups…" so
  the two read as a pair.

`frontend/src/features/methodology/formulas.test.ts`: add `'other-spending'` and
`'other-receipts'` to the `ids` array in `category line items match the backend`.

`frontend/src/features/methodology/methodology-page.tsx`:
- In section `spending-categories`, after the existing `FormulaBlock`, add a paragraph "Ten more
  spending groups are shown below the major ones:" and `<FormulaBlock id='other-spending' />`.
- Do the same in `receipt-categories` with `other-receipts`.

### 7. Contract

```bash
cd backend && uv run python -m scripts.export_openapi
cd ../frontend && pnpm gen:api
```

## Verification

- [ ] `cd backend && uv run pytest` green, including 5 new tests and 2 new route params.
- [ ] `uv run ruff check . && uv run ruff format --check .` clean.
- [ ] `jq '.paths | keys[]' docs/contracts/openapi.json | grep other-` lists both new paths.
- [ ] `cd frontend && pnpm typecheck && pnpm test` green; `grep -rn CATEGORY_FORMULA src` empty.
- [ ] Against the real artifact:
      `curl -s 'localhost:8000/api/v1/categories/other-spending?current_fiscal_year=2026&previous_fiscal_year=2025' | jq '.categories[] | {name, current_fytd, yoy_change}'`
      returns 10 categories. These must match the FY2026 year-end figures
      (`current_date` 2026-09-30): run
      `SELECT SUM(transaction_fytd_amt) FROM deposits_withdrawals WHERE record_date='2026-09-30' AND transaction_type='Withdrawals' AND transaction_catg IN ('DoD - Military Active Duty Pay','DoD - Military Retirement')`
      through the MCP `run_query` and compare with the Military Pay card.
- [ ] `/yoy/withdrawals` shows the "Other spending categories" grid with 10 cards. Clicking
      "SNAP & WIC" opens the dialog with a daily chart and a 2-row breakdown.
- [ ] `/yoy/deposits` shows 4 other receipt cards. FY2027 vs FY2023 shows "Comparable from
      Feb 14, 2023" on Individual and Corporate Income Taxes.
- [ ] MCP `get_skills("categories")` lists all 22 registry categories.

## Notes

- The detail chart works for the new categories without new code: `get_daily_yoy` looks
  them up in `CATEGORY_REGISTRY`.
- Several new categories go back to 2005 only because of the old names in `components`.
  If the Treasury renames a line again, add the new name first in the tuple and add a row to
  Phase 0's history table.
