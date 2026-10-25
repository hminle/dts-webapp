# Phase 4: Rolling averages & combined figures — ⬜ Not Started

**Goal**:
- **Rolling averages.** A 10-statement rolling average of daily withdrawals, with its
  projected monthly rate (× 20), and of unemployment benefits. They are shown on a new
  "Leading flows" page and on the weekly snapshot.
- **Combined figures.** Two figures made from existing categories: interest income transfers
  (interest on Treasury securities + T-bill interest) and net customs receipts (customs
  deposits − CBP payments). They are shown on the weekly snapshot.

Branch: `feat/rolling-and-combined`. It depends on two earlier phases:
- Phase 2: the `Unemployment Benefits` and `Customs Refunds (CBP)` categories.
- Phase 3: `category_fytd`, `_source_for` and the snapshot.

## Scope

In scope:
- `GET /api/v1/rolling/daily`, `GET /api/v1/categories/combined`.
- New snapshot fields and cards.
- The `/daily/leading-flows` page.
- Formula copy, worked examples and tests.

Out of scope:
- Rolling averages of other line items. The metric enum is closed, so a new metric is a new
  enum value plus a test.
- Combined figures on the YoY pages, and a daily chart for combined figures.
- Cash balance (Phase 5).

## Implementation

### 1. Rolling service — create `backend/app/services/rolling.py`

```python
"""Rolling averages of daily amounts, counted in statements."""

RollingMetric = Literal["total_withdrawals", "unemployment_benefits"]

# About 20 business days a month: the newsletter's monthly projection.
MONTHLY_MULTIPLIER = 20
```

Each metric's daily series is one SQL subquery:

| Metric | Daily series |
|---|---|
| `total_withdrawals` | `SELECT record_date, total_withdrawals_today AS value FROM daily_net_transfers` |
| `unemployment_benefits` | `SELECT record_date, SUM(transaction_today_amt) AS value FROM deposits_withdrawals WHERE transaction_type = 'Withdrawals' AND transaction_catg IN (<CATEGORY_REGISTRY["Unemployment Benefits"].components>) GROUP BY record_date` |

The query:

```sql
WITH series AS (<subquery>),
w AS (
  SELECT record_date, value,
         AVG(value) OVER win AS avg_w,
         COUNT(*)  OVER win AS n_w
  FROM series
  WHERE record_date <= ?
  WINDOW win AS (ORDER BY record_date ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW)
)
SELECT record_date, value, CASE WHEN n_w = {window} THEN avg_w END AS rolling_average
FROM w
WHERE record_date >= ?
ORDER BY record_date
```

`{window}` is interpolated because DuckDB does not take a parameter in a frame clause. It is
safe: `RollingAverageRequest.window` is a validated `int` (2–60). Say so in a comment.

Public functions:
- `get_daily(cur, request) -> RollingAverageResponse`:
  - The default `end_date` is the latest `daily_net_transfers.record_date`. The default
    `start_date` is `end_date − 365 days`. `start_date > end_date` raises
    `ValueError("start_date must be on or before end_date")`.
  - No rows raises `HTTPException(404)`.
  - `projected_monthly = rolling_average × MONTHLY_MULTIPLIER` for `total_withdrawals`, and
    `None` for `unemployment_benefits`.
- `rolling_on(cur, metric, window, day: str) -> float | None`: the rolling average on one
  date, through the same query with `start = end = day`.

### 2. Rolling router — create `backend/app/api/routers/rolling.py`; register it in `main.py`

`APIRouter(prefix="/api/v1/rolling", tags=["rolling"], dependencies=[Depends(cache_public)])`.
The route is `@router.get("/daily", response_model=RollingAverageResponse) def get_daily(...)`
and its operation id is `rolling_get_daily`.

Schemas in `backend/app/schemas/treasury.py`:

```python
class RollingAverageRequest(BaseModel):
    metric: RollingMetric = Field(..., description="Daily amount to average")
    window: int = Field(10, ge=2, le=60, description="Statements per average")
    start_date: date | None = Field(None, description="First date returned; default a year before end_date")
    end_date: date | None = Field(None, description="Last date returned; default latest")


class RollingPoint(BaseModel):
    record_date: str
    value: float = Field(..., description="That statement's amount")
    rolling_average: float | None = Field(..., description="Mean of the last `window` statements; null until there are that many")
    projected_monthly: float | None = Field(..., description="rolling_average × 20, withdrawals only")


class RollingAverageResponse(BaseModel):
    metric: RollingMetric
    window: int
    monthly_multiplier: int | None
    start_date: str
    end_date: str
    points: list[RollingPoint]
```

Import `RollingMetric` from `app.services.rolling`. If that creates an import cycle, move the
`Literal` to `app/schemas/treasury.py` and import it into the service instead.

### 3. Combined figures — `backend/app/constants/categories.py`, `services/categories.py`

Add after `CATEGORY_REGISTRY`:

```python
@dataclass(frozen=True)
class CombinedTerm:
    """One registry category inside a combined figure, added or subtracted."""

    category: str
    sign: Literal[1, -1]


@dataclass(frozen=True)
class CombinedCategoryDef:
    """A figure made of registry categories; comparable once every term is."""

    name: str
    terms: tuple[CombinedTerm, ...]

    @property
    def available_from(self) -> date:
        return max(CATEGORY_REGISTRY[t.category].available_from for t in self.terms)


COMBINED_CATEGORIES: tuple[CombinedCategoryDef, ...] = (
    CombinedCategoryDef(
        name="Interest Income Transfers",
        terms=(
            CombinedTerm("Interest on Treasury Securities", 1),
            CombinedTerm("T-Bill Interest", 1),
        ),
    ),
    CombinedCategoryDef(
        name="Net Customs Receipts",
        terms=(
            CombinedTerm("Customs & Duties (Tariffs)", 1),
            CombinedTerm("Customs Refunds (CBP)", -1),
        ),
    ),
)
```

The available-from dates work out as follows:
- Interest Income Transfers: 2022-09-12, the T-Bill date.
- Net Customs Receipts: 2020-05-11, the CBP date.

In `backend/app/services/categories.py` add:

```python
def combined_fytd(cur: duckdb.DuckDBPyConnection, comb: CombinedCategoryDef, day: str) -> float | None:
    """Σ sign × category_fytd over the terms; None if any term is None."""


def get_combined(cur: duckdb.DuckDBPyConnection, request: MajorSpendingCategoriesRequest) -> CombinedCategoriesResponse:
    """Combined figures with YoY change, on the spending source's dates."""
```

`get_combined` follows the pattern of the other category endpoints:
1. It validates the request with `_validate_yoy_request`.
2. It resolves dates with `_resolve_yoy_dates(cur, _SPENDING_SOURCE, …)`.
3. For each combined figure and each date it calls `category_fytd` per term and builds
   `CombinedTermValue`s. The totals go through `nullable_yoy`.

Schemas:

```python
class CombinedTermValue(BaseModel):
    category_name: str
    sign: int = Field(..., description="1 adds the category, -1 subtracts it")
    current_fytd: float | None
    previous_fytd: float | None


class CombinedCategory(BaseModel):
    name: str
    available_from: str
    current_fytd: float | None
    previous_fytd: float | None
    yoy_change: float | None
    yoy_percent_change: float | None
    terms: list[CombinedTermValue]


class CombinedCategoriesResponse(BaseModel):
    current_fiscal_year: int
    previous_fiscal_year: int
    current_date: str
    previous_date: str
    comparison_mode: str
    categories: list[CombinedCategory]
```

Router `backend/app/api/routers/categories.py`:
`@router.get("/combined", response_model=CombinedCategoriesResponse) def get_combined(cur, req: Annotated[MajorSpendingCategoriesRequest, Query()])`,
with the docstring "Figures made of several categories, with YoY change." The operation id is
`categories_get_combined`.

MCP skill `backend/app/mcp_server/skills/categories.md`: add a section "Combined figures"
that lists the two definitions in words, and a pitfall that a combined figure is `null` if
any term is.

### 4. Snapshot additions — `backend/app/services/snapshot.py`, schema

`WeeklySnapshotResponse` gains:

```python
withdrawals_10d_average: float | None
projected_monthly_withdrawals: float | None
unemployment_10d_average: float | None
interest_income_fytd: SnapshotFigure
net_customs_fytd: SnapshotFigure
```

Fill them with `rolling_on(cur, "total_withdrawals", 10, record_date)` (× 20 for the
projection), `rolling_on(cur, "unemployment_benefits", 10, record_date)`, and
`combined_fytd` on `record_date` / `previous_date`.

### 5. Backend tests

Create `backend/tests/test_formula_rolling.py`, using `dnt_row` from Phase 3 with
`withdrawals_today`:
- `test_average_counts_statements_not_days`: seed the 10 real values for 2025-11-20 …
  2025-12-04 (Phase 0), whose dates skip the weekends and Thanksgiving. The 2025-12-04 point
  has `rolling_average == 35608.8` and `projected_monthly == 712176.0`.
- `test_average_is_null_until_the_window_is_full`: the first 9 points have
  `rolling_average is None`.
- `test_start_date_after_end_date_is_400` (through `client`, or `ValueError` through the
  service).
- `test_unemployment_sums_its_lines_and_has_no_projection`: seed 10 `DOL - Unemployment
  Benefits` withdrawal rows with the real 2025-11-20 … 2025-12-04 today amounts
  (78, 63, 193, 241, 353, 56, 212, 269, 164, 107). Use `dw_row` with `today=`. Assert
  `rolling_average == 173.6` and `projected_monthly is None`.
- `test_window_bounds_are_422` (through `client`): `window=1` and `window=61`.

Create `backend/tests/test_formula_combined.py`:
- `test_interest_income_adds_tbill_interest`: interest 141,720; Bills 49,128; Bonds and Notes
  1,749 on 2025-12-04; 120,038 / 53,521 / 4,122 on 2024-12-04. The result is 192,597 vs
  177,681, change 14,916.
- `test_net_customs_subtracts_cbp_payments`: customs deposit 68,584 and CBP withdrawal 3,180 on
  2025-12-04; old-name customs 17,730 and CBP 1,807 on 2024-12-04. The result is 65,404 vs
  15,923, change 49,481.
- `test_combined_is_null_before_its_latest_term`: interest-income previous date 2022-09-09
  gives `previous_fytd is None`.
- `test_combined_available_from`: assert 2022-09-12 and 2020-05-11.

`backend/tests/test_formula_snapshot.py`: extend `test_thursday_snapshot_pairs_the_same_fiscal_day`
with the new fields (seed the 10 withdrawals and unemployment rows and the interest and customs
lines).

`backend/tests/test_analysis_api.py` parametrize list: add
`("/api/v1/rolling/daily", {"metric": "total_withdrawals", "window": 2})`. The seed has only 3
statements per FY, so `window=2` returns at least one non-null average. Also add
`("/api/v1/categories/combined", YEARS)`.

### 6. Worked examples

Add to both `worked-examples.json` copies (identical bytes):

```json
"rolling": {
  "end_date": "2025-12-04",
  "window": 10,
  "withdrawals_today": [19815, 31192, 16793, 19998, 54507, 13595, 125763, 13764, 44733, 15928],
  "withdrawals_dates": ["2025-11-20", "2025-11-21", "2025-11-24", "2025-11-25", "2025-11-26", "2025-11-28", "2025-12-01", "2025-12-02", "2025-12-03", "2025-12-04"],
  "withdrawals_average": 35608.8,
  "projected_monthly": 712176,
  "unemployment_today": [78, 63, 193, 241, 353, 56, 212, 269, 164, 107],
  "unemployment_average": 173.6
},
"combined": {
  "current_date": "2025-12-04",
  "previous_date": "2024-12-04",
  "interest_income": {"current": {"Interest on Treasury Securities": 141720, "Bills (-)": 49128, "Bonds and Notes (-)": 1749}, "previous": {"Interest on Treasury Securities": 120038, "Bills (-)": 53521, "Bonds and Notes (-)": 4122}, "current_total": 192597, "previous_total": 177681, "difference": 14916, "percent_change": 8.39},
  "net_customs": {"current": {"customs": 68584, "cbp": 3180}, "previous": {"customs": 17730, "cbp": 1807}, "current_total": 65404, "previous_total": 15923, "difference": 49481, "percent_change": 310.75}
}
```

`weekly_snapshot` gains:
- `"withdrawals_10d_average": 35608.8`
- `"projected_monthly_withdrawals": 712176`
- `"unemployment_10d_average": 173.6`
- `"interest_income_fytd": {"current": 192597, "previous": 177681, "change": 14916, "percent_change": 8.39}`
- `"net_customs_fytd": {"current": 65404, "previous": 15923, "change": 49481, "percent_change": 310.75}`

`backend/tests/test_formula_examples.py` gets three new tests:
- `test_rolling_example`
- `test_interest_income_example`
- `test_net_customs_example`

Each one feeds the JSON inputs through the real functions. Extend
`test_weekly_snapshot_example` with the new fields.

`frontend/src/features/methodology/formulas.test.ts` `worked examples add up`: add
`it('rolling average')` (Σ ÷ 10 and × 20) and `it('combined figures')` (signed sums and
`pct`).

### 7. Frontend

`frontend/src/features/daily/api.ts`:
- `export type RollingAverage = components['schemas']['RollingAverageResponse']`.
- `useRollingAverage(metric, startDate: string)`: query key
  `['rolling', metric, startDate]`; `api.GET('/api/v1/rolling/daily', { params: { query: { metric, window: 10, start_date: startDate } } })`;
  error message `'Could not load the rolling average'`.

Create `frontend/src/features/daily/components/rolling-chart.tsx`:
- Props: `RollingChart({ points, dataKey, label, format })` with
  `dataKey: 'rolling_average' | 'projected_monthly'`.
- It draws one `Line` with `stroke='var(--chart-1)'`, inside `ChartContainer` + `LineChart`
  like `category-detail-dialog.tsx`.
- `XAxis dataKey='record_date' tickFormatter={formatShortDate}`; `YAxis tickFormatter={format}`.
- The tooltip shows the date, the value and that day's amount (`value`).
- `null` points leave gaps.

Create `frontend/src/features/daily/leading-flows-page.tsx`:
1. A controls `Card` with a `ToggleGroup` labelled "Range": `6 months` (183 days),
   `1 year` (365, default), `3 years` (1095), `5 years` (1826).
   `startDate = isoDate(today − days)`. Put a pure helper `rangeStart(days, today)` in
   `frontend/src/features/daily/lib.ts`, with a test.
2. `StatCard`s:
   - "10-day average of withdrawals": `formatBillions`, `hint='rolling-average'`
   - "Projected monthly rate": `formatBillions`, note "10-day average × 20"
   - "Unemployment benefits, 10-day average": `formatTreasuryValue` (173.6 → "$174M"; `formatMillions` expects raw dollars, not millions)

   Each uses the last non-null point.
3. A `Card` "Projected monthly withdrawals" with `RollingChart dataKey='projected_monthly' format={formatBillions}`.
4. A `Card` "Unemployment benefits, 10-day average" with
   `RollingChart dataKey='rolling_average' format={formatTreasuryValue}`.

Create `frontend/src/routes/daily/leading-flows.tsx`:
`createFileRoute('/daily/leading-flows')` with `<Page title='Leading flows'>`.
`sidebar-data.ts`: under Daily add `{ title: 'Leading flows', url: '/daily/leading-flows' }`
after Net transfers.

Snapshot page (`frontend/src/features/snapshot/snapshot-page.tsx`), after the "Fiscal year to
date" section:
- A section "Leading flows" with three `StatCard`s, the same as the leading-flows page but
  read from the snapshot fields. A link `Link to='/daily/leading-flows'` reads "See the trend".
- A section "Combined figures" with two `FigureCard`s:
  - "Interest income transfers", `hint='interest-income-transfers'`
  - "Net customs receipts", `hint='net-customs-receipts'`

### 8. Formula copy

`formulas.ts`, with these new ids:
- `'rolling-average'`, placed after `'leading-flow'` in `FORMULA_ORDER`:
  - title `'Rolling average and monthly rate'`
  - summary `'The mean of the last 10 statements’ amounts; for withdrawals, × 20 gives a projected monthly rate.'`
  - expression `['10-day average = Σ amount over the last 10 statements ÷ 10', 'Projected monthly rate = 10-day average of withdrawals × 20']`
  - pitfalls:
    - `'It counts statements, not calendar days: weekends and holidays are skipped.'`
    - `'A window holding the 1st of the month or a mid-month interest date runs high; the rate swings with payment calendars.'`
  - `source: DEPOSITS_TABLE`
- `'interest-income-transfers'`, placed after `'tbill-interest'`:
  - title `'Interest income transfers'`
  - summary `'Cash interest on notes and bonds plus the T-bill discount: all interest the Treasury pays holders.'`
  - expression `['Interest income = Interest on Treasury Securities + T-Bill interest']`
  - `terms` naming the two categories
  - pitfall `'Comparable from 2022-09-12, when T-bill interest got its own lines.'`
- `'net-customs-receipts'`, placed after `'other-receipts'`:
  - title `'Net customs receipts'`
  - summary `'Customs deposits minus Customs and Border Protection payments, which since 2026 are mostly tariff refunds.'`
  - expression `['Net customs = Customs & Duties (Tariffs) − Customs Refunds (CBP)']`
  - pitfall `'CBP payments include more than refunds; before 2026 they are small.'`

`methodology-page.tsx`:
- Section `surplus-or-deficit`: after `<FormulaBlock id='leading-flow' />`, add a paragraph
  with the 2025-12-04 example from `examples.rolling` and `<FormulaBlock id='rolling-average' />`.
- Section `t-bill-discount`: append `<FormulaBlock id='interest-income-transfers' />` with the
  example numbers.
- Section `receipt-categories`: append `<FormulaBlock id='net-customs-receipts' />`.

### 9. Contract and routes

```bash
cd backend && uv run python -m scripts.export_openapi
cd ../frontend && pnpm gen:api && pnpm build
```

## Verification

- [ ] `cd backend && uv run pytest` green, including:
  - 5 rolling tests
  - 4 combined tests
  - the extended snapshot test
  - 3 new example tests
  - 2 new route params
- [ ] Ruff clean.
- [ ] The two `worked-examples.json` copies are identical (`diff` prints nothing).
- [ ] `cd frontend && pnpm typecheck && pnpm test && pnpm build` green.
- [ ] Real artifact:
  - `curl -s 'localhost:8000/api/v1/rolling/daily?metric=total_withdrawals&start_date=2025-12-04&end_date=2025-12-04' | jq '.points[0]'`
    → `rolling_average` 35608.8, `projected_monthly` 712176.
  - `curl -s 'localhost:8000/api/v1/categories/combined?current_fiscal_year=2026&previous_fiscal_year=2025' | jq '.categories[].name'`
    → both names.
  - `curl -s 'localhost:8000/api/v1/snapshot/weekly?as_of=2025-12-04' | jq '{withdrawals_10d_average, interest_income_fytd, net_customs_fytd}'`
    matches the worked example.
- [ ] `/daily/leading-flows` shows 3 stat cards and 2 charts. Switching the range re-queries
      (watch the network tab).
- [ ] `/snapshot` shows the Leading flows and Combined figures sections.

## Notes

- Our unemployment average for 2025-12-04 is 173.6. The newsletter printed 173.5. The
  definition here is the documented one (the last 10 statements); the newsletter's small
  differences are noted in `docs/research/mmt-trader-dts-method.md` §2.5.
