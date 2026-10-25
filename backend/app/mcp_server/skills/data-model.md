---
name: data-model
description: Every table in the artifact, what it holds, how day_of_fiscal_year is numbered, and every column.
formulas: [day-of-fiscal-year, cash-balance]
---

# Data model

The artifact is one DuckDB file. Nine tables hold Treasury statement rows exactly as the
Treasury Fiscal Data API returns them (one row per line per business day); one table is
derived from them at ingestion; `metadata` describes the build.

## Tables

| Table | Holds |
|---|---|
| `operating_cash_balance` | Operating Cash Balance (Table I) |
| `deposits_withdrawals` | Deposits & Withdrawals of Operating Cash (Table II) |
| `public_debt_transactions` | Public Debt Transactions (Table IIIA) |
| `adjustment_public_debt` | Public Debt Adjustments to cash basis (Table IIIB) |
| `debt_subject_to_limit` | Debt Subject to Limit (Table IIIC) |
| `inter_agency_tax_transfers` | Inter-Agency Tax Transfers (Table IV) |
| `income_tax_refunds` | Income Tax Refunds Issued (Table V) |
| `federal_tax_deposits` | Federal Tax Deposits |
| `short_term_cash_investments` | Short-Term Cash Investments |
| `daily_net_transfers` | Derived: one row per date with total deposits, total withdrawals and net transfers (today, MTD, FYTD) |
| `metadata` | `key`/`value` pairs: `build_date`, `latest_record_date`, `source`, `schema_version` |

In `deposits_withdrawals`, `transaction_type` is `Deposits` or `Withdrawals`,
`transaction_catg` is the line item name, and the `account_type` value
`Treasury General Account Total Deposits` (or `... Total Withdrawals`) marks the day's total row
(from 2022-04-18 on; see `net-transfers`).

In `operating_cash_balance`, the Treasury General Account (TGA) closing balance has lived on
three rows. **Since 2022-04-18 the closing balance is in `open_today_bal`**; that row's
`close_today_bal` is NULL.

| Dates | `account_type` | Column holding the closing balance |
|---|---|---|
| 2005-10-03 to 2021-09-30 | `Federal Reserve Account` | `close_today_bal` |
| 2021-10-01 to 2022-04-15 | `Treasury General Account (TGA)` | `close_today_bal` |
| 2022-04-18 on | `Treasury General Account (TGA) Closing Balance` | `open_today_bal` |

Each era's last close equals the next era's first open. `call_api("cash_balance_get_daily", {})`
returns the series with the eras already joined.

## Day of the fiscal year

Day N is the Nth business day with a statement since October 1. Weekends and holidays are not
counted, so day 12 is not October 12. It is numbered within each fiscal year of
`deposits_withdrawals` as:

```
day_of_fiscal_year = DENSE_RANK() OVER (PARTITION BY record_fiscal_year ORDER BY record_date)
```

`daily_net_transfers.day_of_fiscal_year` holds it. A statement without totals keeps its day
number but has no net-transfer figures.

Business days per fiscal year:

```sql
SELECT record_fiscal_year, count(DISTINCT record_date) AS business_days
FROM deposits_withdrawals
GROUP BY record_fiscal_year
ORDER BY record_fiscal_year
```

## Columns

{{schema}}
