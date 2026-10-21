# Phase 1: Backend Formula Tests — ✅ Done

**Goal**: Every financial formula in `backend/app/utils` and `backend/app/services` has direct
unit tests covering its normal path and every fallback branch, and the Methodology worked
examples are proven by running them through the real code.

## Scope

- In scope: new test files, new fixture builders, `worked-examples.json`.
- Out of scope: changing any formula or its output (if a test exposes a bug, record it in Notes
  and pin the current behavior with a `# current behavior:` comment — fixing it is a separate
  `fix/` branch); API-level tests (already exist); frontend tests.

Branch: `test/formula-unit-tests`.

## Implementation

### 1. Fixtures — `backend/tests/fixtures.py`

Add, next to `dw_day`:

- `dw_row(day, fy, *, account_type, transaction_type, transaction_catg=None, today, mtd=None, fytd=None)`
  → one-row `DataFrame`; `mtd`/`fytd` default to `today * 10` / `today * 100` like `_amounts`.
- `apd_row(day, fy, *, adj_type, fytd)` → one `adjustment_public_debt` row (`adj_fytd_amt`).
- `itr_row(day, fy, *, tax_refund_type, fytd)` → one `income_tax_refunds` row
  (`tax_refund_fytd_amt`).
- `formula_db(frames: dict[str, list[pd.DataFrame]]) -> duckdb.DuckDBPyConnection`: in-memory
  `duckdb.connect(":memory:")`, `create_schema`, then `insert_frame` each frame into its table.
  Callers that need `daily_net_transfers` call `populate_fiscal_years` themselves.

Read `backend/app/core/schema.py` for the exact column names before writing the builders.

### 2. `test_formula_net_transfers.py` — `calculate_daily_net_transfers`

One test each:

1. Pre-aggregated totals: deposits 32,776 / issues 1,023 / withdrawals 16,223 / redemptions
   1,225 → total deposits 31,753, total withdrawals 14,998, net −16,755; `leading_flow` 14,998.
2. MTD and FYTD use the same subtraction (use `dw_day`'s ×10 / ×100 amounts and assert all nine
   `total_*`/`net_flow_*` fields).
3. No pre-aggregated total rows → sums every `Treasury General Account (TGA)` row of that
   transaction type (two deposit rows 100 + 50 → TGA deposits 150).
4. No TGA rows either → sums `Federal Reserve Account` rows (pre-2015 statements).
5. Debt rows only under `Federal Reserve Account` → still subtracted.
6. Debt rows absent → treated as 0 (net = TGA withdrawals − TGA deposits).
7. Empty frame → `None`; deposits present but no withdrawals rows anywhere → `None`
   (`dw_day_without_totals`).
8. Sign: withdrawals > deposits → positive net (outflow); the reverse → negative.

### 3. `test_formula_day_of_fiscal_year.py`

1. `compute_daily_records` on three dates where the middle one has no totals → rows for days 1
   and 3 only (day 3 keeps number 3).
2. The category query's `DENSE_RANK` (`get_category_comparison` in `app/services/yoy.py`) gives
   the same numbering for the same three dates.
3. `fiscal_day_for_date` counts distinct dates ≤ the date (returns 0 for an FY with no rows);
   `date_for_fiscal_day` is its inverse; Day N beyond the last date → `None`.

### 4. `test_formula_yoy.py` — `app/utils/yoy.py`

1. `yoy_change(108932, 94000)` → `(14932, ≈15.885)`; `(−30, −50)` → `(20, 40.0)`;
   `(5, 0)` → `(5, None)`; `(0, 0)` → `(0, None)`.
2. `find_aligned_previous_date`, `fiscal_day` mode: Day 2 of FY2027 → Day 2 of FY2026; current
   date with no rows (day 0) → latest of previous FY; Day N the previous FY doesn't reach →
   latest of previous FY.
3. `calendar_date` mode: exact MM-DD present → that date; MM-DD absent (Sunday) → latest
   previous-FY date ≤ it; nothing ≤ it → latest of previous FY.
4. `fetch_component_fytd` with `extra_filters={"transaction_type": "Withdrawals"}` ignores a
   Deposits row with the same `transaction_catg`; missing key → 0.0.
5. `fetch_components_daily` sums several keys per date, ordered by date; empty keys → `[]`.
6. `get_daily_comparison` (needs `daily_net_transfers`): `fiscal_day` stops at the shorter
   year's last day; `calendar_date` keeps only MM-DD present in both years; percent `None` when
   previous is 0.

### 5. `test_formula_categories.py` — `app/services/categories.py`

For each, build the smallest `formula_db` that exercises it and call the service function with
its `*Request` schema (read `app/schemas/treasury.py` for field names):

1. `get_major_spending`: Medicare = sum of its 3 components (28,951 + 42,077 + 10,505 =
   81,533 vs 72,231 → +9,302, +12.88 %); a Deposits row with a spending component's name is not
   counted; categories with no rows report 0 and `None` percent.
2. `get_major_receipts`: Customs sums both names — current year only the new name (3,870),
   previous only the old (4,715) → −845, −17.92 %. Pin that dropping either name would break it
   (assert both names are in `MAJOR_RECEIPT_CATEGORIES`).
3. `get_tbill_interest`: 17,006 + 3,745 = 20,751 vs 13,738 + 127 = 13,865 → +6,886, +49.66 %;
   other `adj_type` rows ignored.
4. `get_irs_tax_refunds`: four types sum to 10,558; a `TREAS - IRS Refunds for Puerto Rico`
   row in `deposits_withdrawals` is not counted (source is `income_tax_refunds`).
5. `get_daily_yoy` for one spending category: per-day FYTD sums and the day pairing.
6. Calendar-date mode on a card: current date's MM-DD missing in the previous FY → previous
   value read from the latest earlier statement.

### 6. `test_formula_weekly.py` — `app/services/weekly.py`

1. `_weekly_fridays(2025-10-01, 2025-10-31)` → Oct 3, 10, 17, 24, 31; a range with no Friday → `[]`.
2. `_fiscal_year_dates` clips the end to today (monkeypatch-free: assert `end <= datetime.now()`
   and `start == datetime(fy-1, 10, 1)`).
3. `_build_weekly_points`: a Friday holiday uses Thursday; Friday + 5 earlier days all empty →
   week skipped (no point, week numbers of later weeks unchanged).
4. `get_comparison`: second year truncated to the first year's number of points; same year twice
   → `ValueError`.

### 7. `worked-examples.json` + `test_formula_examples.py`

Create `frontend/src/features/methodology/worked-examples.json` with exactly the Phase 0
worked-example numbers, shaped:

```json
{
  "net_transfers": {
    "date": "2026-10-19", "fiscal_year": 2027, "day_of_fiscal_year": 12,
    "inputs": { "today": { "tga_deposits": 32776, "debt_issues": 1023, "tga_withdrawals": 16223, "debt_redemptions": 1225 },
                "fytd":  { "tga_deposits": 1949405, "debt_issues": 1659685, "tga_withdrawals": 1968406, "debt_redemptions": 1569754 } },
    "outputs": { "today": { "total_deposits": 31753, "total_withdrawals": 14998, "net_transfers": -16755 },
                 "fytd":  { "total_deposits": 289720, "total_withdrawals": 398652, "net_transfers": 108932 } }
  },
  "yoy": { "current": { "date": "2026-10-19", "value": 108932 }, "previous": { "date": "2025-10-17", "value": 94000 },
           "difference": 14932, "percent_change": 15.89 },
  "yoy_negative_base": { "current": -30, "previous": -50, "difference": 20, "percent_change": 40.0 },
  "categories": {
    "medicare":  { "current": [28951, 42077, 10505], "previous": [26849, 38413, 6969], "difference": 9302, "percent_change": 12.88 },
    "customs":   { "current": { "DHS - Customs Duties, Taxes, and Fees": 3870 }, "previous": { "DHS - Customs and Certain Excise Taxes": 4715 }, "difference": -845, "percent_change": -17.92 },
    "tbill":     { "current": { "Bills (-)": 17006, "Bonds and Notes (-)": 3745 }, "previous": { "Bills (-)": 13738, "Bonds and Notes (-)": 127 }, "difference": 6886, "percent_change": 49.66 },
    "irs_refunds": { "table_v": { "Taxes - Individual Tax Refunds (EFT)": 4394, "Taxes - Individual Tax Refunds (Checks)": 1788, "Taxes - Business Tax Refunds (EFT)": 827, "Taxes - Business Tax Refunds (Checks)": 3549 }, "table_ii_eft_only": 5221 }
  }
}
```

`backend/tests/test_formula_examples.py` loads it from
`Path(__file__).resolve().parents[2] / "frontend/src/features/methodology/worked-examples.json"`
and, for each block, builds rows from `inputs` (via the Phase 1 builders), runs the real function
(`calculate_daily_net_transfers`, `yoy_change`, the category services), and asserts every
`outputs`/`difference` exactly and `percent_change` to 2 decimals. The CI `backend` job checks out
the whole repo, so the path exists there.

## Verification

- [x] `cd backend && uv run pytest -q` → all pass; `uv run pytest -q tests/test_formula_*.py`
      runs ≥ 35 tests.
- [x] `uv run ruff check . && uv run ruff format --check .` → clean.
- [x] Mutation spot-check (local only, revert after): change `abs(previous)` to `previous` in
      `app/utils/yoy.py` → `test_formula_yoy.py` and `test_formula_examples.py` fail; change
      `- debt_issues_today` to `+` in `deposits_withdrawals.py` → net-transfer tests fail.
- [x] Editing any number in `worked-examples.json` makes `test_formula_examples.py` fail.
- [x] `git diff --stat main -- backend/app` → empty (no behavior change).

## Notes

- **52 formula tests** across the six files (108 in the suite), all passing; `backend/app` is
  unchanged. Mutation checks: dropping `abs()` from `yoy_change` fails 3 tests; turning
  `− debt_issues_today` into `+` fails 5; changing Medicare's difference in the JSON fails
  `test_medicare_example`.
- Fixtures added: `dw_row`, `catg_row` (a TGA line item carrying only FYTD), `apd_row`,
  `itr_row`, `formula_db`. The JSON stores components as name → amount maps (not arrays as first
  sketched) so the test can seed the right `transaction_catg`.
- **Three calendar-date rules, all pinned** (Phase 2 must explain each where it shows):
  1. Daily comparison chart (`services/yoy.py:get_daily_comparison`): keeps only MM-DD present
     in both years.
  2. Category cards (`utils/yoy.py:find_aligned_previous_date`): a missing MM-DD uses the latest
     earlier statement (2025-10-19 → 2025-10-17).
  3. Category detail chart (`services/categories.py:get_daily_yoy`): keeps the current date and
     compares it with 0, percent `None`.
- **Day numbering differs by query, pinned:** `daily_net_transfers` numbers every statement date
  (a day without totals keeps its number); category queries rank only the dates on which the
  chosen line items appear (`DENSE_RANK` over the filtered rows, and `get_daily_yoy`'s own
  counter). In real data the line items appear on every statement, so the numbers agree; the
  Methodology should state the rule without alarming readers.
- **Weekly truncation counts points, not weeks (pinned in
  `test_a_skipped_first_year_week_shortens_the_second_year`):** if the first year has no
  statement within 5 days of a Friday, its weeks are e.g. 1, 2, 4, and the second year is cut to
  its first 3 Fridays, so first-year week 4 pairs with nothing. Only possible after a 6-day gap in
  statements; worth a `fix/` branch (cut by the first year's last `week_number`) — not done here.
- Fallback sums include the debt rows before subtracting them, so borrowing cancels out on old
  statements too (`test_line_item_sums_include_the_debt_rows_before_subtracting_them`).
