# Phase 5: Cash balance — ⬜ Not Started

**Goal**: Show the Treasury General Account (TGA) closing balance, the Treasury's cash at the
Federal Reserve, as a daily series back to 2005:
- on a new "Cash balance" page
- as a card on the weekly snapshot, with its change since last week and since the same
  business day a year earlier

Branch: `feat/cash-balance`. Depends on Phase 3 (the snapshot). It can run in parallel with
Phase 4: the two phases touch different snapshot fields.

## Scope

In scope:
- A constant table of the three storage eras.
- `GET /api/v1/cash-balance/daily`.
- The `/cash-balance` page, the snapshot card, formula copy, the worked example and tests.

Out of scope:
- Tax and Loan Note account balances before 2012.
- The Supplementary Financing Program account.
- Short-term cash investments.
- Any change to ingestion. The table is already in the artifact.

## Implementation

### 1. Eras — create `backend/app/constants/cash_balance.py`

```python
"""Where the TGA closing balance lives in ``operating_cash_balance``, by era.

The Treasury moved the balance between rows twice. Since 2022-04-18 the
closing balance row carries the amount in ``open_today_bal``; its
``close_today_bal`` is NULL. Each era's last close equals the next era's
first open (checked on 2021-09-30/10-01 and 2022-04-15/04-18).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BalanceRow:
    account_type: str
    column: str  # the column holding the closing balance


CLOSING_BALANCE_ROWS: tuple[BalanceRow, ...] = (
    BalanceRow("Federal Reserve Account", "close_today_bal"),  # to 2021-09-30
    BalanceRow("Treasury General Account (TGA)", "close_today_bal"),  # 2021-10-01 – 2022-04-15
    BalanceRow("Treasury General Account (TGA) Closing Balance", "open_today_bal"),  # 2022-04-18 on
)
```

### 2. Service — create `backend/app/services/cash_balance.py`

Build the SQL from `CLOSING_BALANCE_ROWS`. The column names come from that constant, never
from input, so interpolating them is safe; say so in a comment.

```sql
SELECT record_date,
       CASE account_type
         WHEN 'Federal Reserve Account' THEN close_today_bal
         WHEN 'Treasury General Account (TGA)' THEN close_today_bal
         WHEN 'Treasury General Account (TGA) Closing Balance' THEN open_today_bal
       END AS closing_balance
FROM operating_cash_balance
WHERE account_type IN (?, ?, ?)
  AND record_date BETWEEN ? AND ?
ORDER BY record_date
```

Public functions:
- `get_daily(cur, request) -> CashBalanceResponse`. The defaults are the same as the rolling
  endpoint: `end_date` is the latest `record_date` in `operating_cash_balance`, and
  `start_date` is `end_date − 365 days`. `start_date > end_date` raises `ValueError`, and no
  rows raises `HTTPException(404)`.
- `balance_on(cur, day: str) -> float | None`: one date through the same query.

**No silent fallback.** If any returned `closing_balance` is NULL, raise
`RuntimeError(f"No TGA closing balance on {record_date}")`. A NULL means the Treasury moved
the balance again and `CLOSING_BALANCE_ROWS` needs a new era.

### 3. Schemas and router

```python
class CashBalanceRequest(BaseModel):
    start_date: date | None = Field(None, description="Default a year before end_date")
    end_date: date | None = Field(None, description="Default the latest statement")


class CashBalancePoint(BaseModel):
    record_date: str
    closing_balance: float = Field(..., description="TGA closing balance, millions of dollars")


class CashBalanceResponse(BaseModel):
    start_date: str
    end_date: str
    points: list[CashBalancePoint]
```

Create `backend/app/api/routers/cash_balance.py`:

```python
router = APIRouter(
    prefix="/api/v1/cash-balance", tags=["cash_balance"], dependencies=[Depends(cache_public)]
)


@router.get("/daily", response_model=CashBalanceResponse)
def get_daily(cur: CursorDep, req: Annotated[CashBalanceRequest, Query()]) -> CashBalanceResponse:
    """The TGA closing balance on each statement date."""
    return cash_balance.get_daily(cur, req)
```

The operation id is `cash_balance_get_daily`. Register the router in `backend/app/main.py`'s
loop tuple.

### 4. Snapshot card — `backend/app/services/snapshot.py`, schema

```python
class SnapshotCashBalance(BaseModel):
    closing: float | None = Field(..., description="On record_date; null if the statement has no balance row")
    previous_week: float | None = Field(..., description="On previous_week_date")
    change_week: float | None
    year_ago: float | None = Field(..., description="On previous_date (same fiscal day)")
    change_year: float | None
    percent_change_year: float | None
```

`WeeklySnapshotResponse` gains `cash_balance: SnapshotCashBalance`. It is filled with
`balance_on` on `record_date`, `previous_week_date` and `previous_date`. Changes go through
`nullable_yoy`. `balance_on` returns `None` when the date has **no** balance row (the seeded
test artifact has none). It raises only when a row exists but its column is NULL, per §2. That
keeps Phase 3's `test_snapshot_route_answers` green.

### 5. MCP skill

`backend/app/mcp_server/skills/data-model.md`: under `operating_cash_balance`, add the three
eras table from Phase 0 and the warning that since 2022-04-18 the closing balance is in
`open_today_bal`. Test `test_skill_sql_runs` runs every SQL block in the skills. If you add an
SQL example, it must run on the seeded artifact.

### 6. Backend tests — create `backend/tests/test_formula_cash_balance.py`

Add the fixture `ocb_row(day, fy, *, account_type, open_today=None, close_today=None)` to
`backend/tests/fixtures.py`. It builds one `operating_cash_balance` row.

Tests:
- `test_each_era_reads_its_own_column`: three rows, one per era:
  - 2021-09-30 `Federal Reserve Account`, close 215,160
  - 2022-04-15 `Treasury General Account (TGA)`, close 578,473
  - 2026-08-27 `… Closing Balance`, open 950,804, close NULL

  The series is `[215160, 578473, 950804]`.
- `test_other_rows_are_ignored`: a `Treasury General Account (TGA) Opening Balance` row and a
  `Short-Term Cash Investments (Table V)` row on the same date do not appear.
- `test_a_null_balance_raises`: a `… Closing Balance` row with `open_today_bal` NULL raises
  `RuntimeError`.
- `test_default_range_is_a_year`.
- `test_start_after_end_is_400`.

`backend/tests/test_formula_snapshot.py`: seed balances on the snapshot, previous-week and
previous-year dates, and assert `cash_balance`.

`backend/tests/test_analysis_api.py`: add `("/api/v1/cash-balance/daily", {})`. The seed's
`endpoint_row` rows for `operating_cash_balance` have a NULL `account_type`, so the route
returns 404 there. Parametrize it as an expected 404 in a separate test
`test_cash_balance_without_rows_is_404`, rather than in the 200 list.

### 7. Worked example

Both `worked-examples.json` copies:

```json
"cash_balance": {
  "record_date": "2026-08-27",
  "closing": 950804,
  "previous_week_date": "2026-08-20",
  "previous_week": 935077,
  "change_week": 15727,
  "year_ago_date": "2025-08-28",
  "year_ago": 609660,
  "change_year": 341144,
  "percent_change_year": 55.96,
  "eras": [
    {"date": "2021-09-30", "account_type": "Federal Reserve Account", "column": "close_today_bal", "value": 215160},
    {"date": "2021-10-01", "account_type": "Treasury General Account (TGA)", "column": "open_today_bal", "value": 215160},
    {"date": "2022-04-15", "account_type": "Treasury General Account (TGA)", "column": "close_today_bal", "value": 578473},
    {"date": "2022-04-18", "account_type": "Treasury General Account (TGA) Opening Balance", "column": "open_today_bal", "value": 578473}
  ]
}
```

`backend/tests/test_formula_examples.py::test_cash_balance_example`: seed the three dates and
assert the closing, week and year figures through `balance_on`.

### 8. Frontend

Create `frontend/src/features/cash-balance/api.ts`:
- Export `type CashBalance = components['schemas']['CashBalanceResponse']`.
- `useCashBalance(startDate: string | null)`: query key `['cash-balance', startDate]`;
  `start_date` is omitted when `null` ("All" range uses `'2005-10-03'`).

Create `frontend/src/features/cash-balance/lib.ts`, plus `lib.test.ts`:
- `latestChange(points, back = 5)` returns `{ latest, previous, change }` against the point
  `back` statements earlier, or `null` when there are fewer points. Five statements is about
  one week.
- Reuse `rangeStart` from `frontend/src/features/daily/lib.ts` (Phase 4). If Phase 5 lands
  first, create `rangeStart` there and let Phase 4 reuse it.

Create `frontend/src/features/cash-balance/cash-balance-page.tsx`:
1. A controls `Card` with a range `ToggleGroup`: `1 year` (default), `5 years`, `All`.
2. `StatCard`s:
   - "Closing balance": `formatBillions(latest)`, note `formatDate(latest date)`,
     `hint='cash-balance'`
   - "Change over 5 statements": signed `formatBillions`, `changeClass`
3. A `Card` "Treasury General Account, closing balance" with a `LineChart` of
   `closing_balance` over `record_date`. Use `stroke='var(--chart-1)'` and
   `YAxis tickFormatter={formatBillions}`. Below the chart, a muted note: "Cash the Treasury
   holds at the Federal Reserve. Before 2012 the Treasury also held cash in Tax and Loan
   accounts, not shown."

Create `frontend/src/routes/cash-balance.tsx` with `createFileRoute('/cash-balance')` and
`<Page title='Cash balance'>`. `sidebar-data.ts`: add
`{ title: 'Cash balance', url: '/cash-balance', icon: Landmark }` after Weekly comparison.

Snapshot page: a section "Cash balance" with one card, "Treasury cash balance":
- the value `formatBillions(cash_balance.closing)`
- the note "<signed change_week> since <previous_week_date> · <signed change_year>
  (<signed %>) vs a year ago"
- `hint='cash-balance'`

### 9. Formula copy

`formulas.ts`: `'cash-balance'`, placed after `'rolling-average'` in `FORMULA_ORDER`:
- title `'Treasury cash balance'`
- summary `'The Treasury General Account’s closing balance at the Federal Reserve on each statement date.'`
- expression `['Closing balance = opening balance + deposits − withdrawals (Table I)']`
- pitfalls:
  - `'Unlike net transfers, the balance includes borrowing: debt sales raise it, redemptions lower it.'`
  - `'Since April 2022 the Treasury reports the closing balance on its own row.'`
- `source: 'Operating Cash Balance (Table I)'`

`methodology-page.tsx`: add a new `ProseSection id='cash-balance' title='13. Treasury cash balance'`
before `known-limits`. Renumber the later sections' titles (13 → 14, and so on) **and** their
TOC entries. Its content:
- a paragraph from `examples.cash_balance`
- `<FormulaBlock id='cash-balance' />`

Add `{ id: 'cash-balance', title: 'Treasury cash balance' }` to the TOC list before
`known-limits`.

### 10. Contract and routes

```bash
cd backend && uv run python -m scripts.export_openapi
cd ../frontend && pnpm gen:api && pnpm build
```

## Verification

- [ ] `cd backend && uv run pytest` green: 5 cash-balance tests, the extended snapshot test,
      `test_cash_balance_example`, and the 404 route test.
- [ ] Ruff clean; the two JSON copies are identical.
- [ ] `cd frontend && pnpm typecheck && pnpm test && pnpm build` green.
- [ ] Real artifact:
  - `curl -s 'localhost:8000/api/v1/cash-balance/daily?start_date=2021-09-29&end_date=2022-04-19' | jq '[.points[] | select(.record_date=="2021-09-30" or .record_date=="2021-10-01" or .record_date=="2022-04-15" or .record_date=="2022-04-18")]'`
    → 4 points, no NULLs.
  - `curl -s 'localhost:8000/api/v1/cash-balance/daily?start_date=2005-10-03' | jq '.points | length'`
    is about 5,300, and the request does not error.
  - `curl -s 'localhost:8000/api/v1/snapshot/weekly?anchor_weekday=thursday&as_of=2026-08-27' | jq .cash_balance`
    → closing 950804, change_week 15727, change_year 341144.
- [ ] `/cash-balance` with "All" draws an unbroken line from 2005. The 2021 and 2022
      switch-over dates show no jump.
- [ ] `/snapshot` shows the Cash balance section.

## Notes

- The balance changes by net transfers **plus** net borrowing, so it is not a fiscal-stance
  measure. The formula's first pitfall says so, because readers often confuse the two.
