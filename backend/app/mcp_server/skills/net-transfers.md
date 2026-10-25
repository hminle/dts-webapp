---
name: net-transfers
description: How the app computes daily TGA total deposits, total withdrawals and net transfers, with SQL and a worked example.
formulas: [total-deposits, total-withdrawals, net-transfers, leading-flow]
---

# Net transfers

## The formula

```
Total deposits    = TGA total deposits    − public debt cash issues
Total withdrawals = TGA total withdrawals − public debt cash redemptions
Net transfers     = total withdrawals − total deposits
Leading flow      = total withdrawals (today)
```

Borrowing is removed on both sides, so a day of heavy debt sales does not look like a day of
high tax receipts. Interest on the debt stays in withdrawals; only the repayment of principal
is removed.

**Sign:** positive means more went out than came in (a deficit day); negative means receipts
exceeded spending (a surplus day). This is the opposite of a bank balance. One day can be a
surplus while the fiscal year to date is a deficit; tax receipts arrive in large, uneven
batches.

## The four Treasury lines

All four are in `deposits_withdrawals`:

| Input | `account_type` | `transaction_catg` |
|---|---|---|
| TGA total deposits | `Treasury General Account Total Deposits` | |
| TGA total withdrawals | `Treasury General Account Total Withdrawals` | |
| Public debt cash issues | `Treasury General Account (TGA)` | `Public Debt Cash Issues (Table IIIB)` |
| Public debt cash redemptions | `Treasury General Account (TGA)` | `Public Debt Cash Redemp. (Table IIIB)` |

The two total rows exist only from 2022-04-18. Before that the app adds up the day's
`Treasury General Account (TGA)` deposit or withdrawal rows instead, and statements up to
2021-09-30 report under `account_type = 'Federal Reserve Account'` rather than the TGA. The SQL
below works only from 2022-04-18; for earlier dates read `daily_net_transfers`, which ingestion
built with the same fallbacks.

## Worked example

On {{example:net_transfers.date}} (day {{example:net_transfers.day_of_fiscal_year}} of
FY{{example:net_transfers.fiscal_year}}):

| | Today | FYTD |
|---|---|---|
| TGA total deposits | {{example:net_transfers.inputs.today.tga_deposits}} | {{example:net_transfers.inputs.fytd.tga_deposits}} |
| − Public debt cash issues | {{example:net_transfers.inputs.today.debt_issues}} | {{example:net_transfers.inputs.fytd.debt_issues}} |
| = Total deposits | {{example:net_transfers.outputs.today.total_deposits}} | {{example:net_transfers.outputs.fytd.total_deposits}} |
| TGA total withdrawals | {{example:net_transfers.inputs.today.tga_withdrawals}} | {{example:net_transfers.inputs.fytd.tga_withdrawals}} |
| − Public debt cash redemptions | {{example:net_transfers.inputs.today.debt_redemptions}} | {{example:net_transfers.inputs.fytd.debt_redemptions}} |
| = Total withdrawals | {{example:net_transfers.outputs.today.total_withdrawals}} | {{example:net_transfers.outputs.fytd.total_withdrawals}} |
| **Net transfers** | **{{example:net_transfers.outputs.today.net_transfers}}** | **{{example:net_transfers.outputs.fytd.net_transfers}}** |

Millions of dollars. That day was a surplus; the fiscal year to date was a deficit.

## Getting it

The quickest way: `call_api("net_transfers_get_for_date", {"date": "YYYY-MM-DD"})` or
`call_api("net_transfers_get_for_fiscal_year", {"fiscal_year": 2027})`. In SQL,
`daily_net_transfers` already holds it (`net_flow_today`, `net_flow_mtd`, `net_flow_fytd`,
`leading_flow`):

```sql
SELECT record_date, day_of_fiscal_year, total_deposits_today, total_withdrawals_today,
       net_flow_today, net_flow_fytd
FROM daily_net_transfers
ORDER BY record_date DESC
LIMIT 5
```

Computed from `deposits_withdrawals` for the latest date:

```sql
WITH lines AS (
    SELECT
        sum(transaction_today_amt) FILTER (
            WHERE account_type = 'Treasury General Account Total Deposits') AS tga_deposits,
        sum(transaction_today_amt) FILTER (
            WHERE account_type = 'Treasury General Account Total Withdrawals') AS tga_withdrawals,
        sum(transaction_today_amt) FILTER (
            WHERE account_type = 'Treasury General Account (TGA)'
              AND transaction_catg = 'Public Debt Cash Issues (Table IIIB)') AS debt_issues,
        sum(transaction_today_amt) FILTER (
            WHERE account_type = 'Treasury General Account (TGA)'
              AND transaction_catg = 'Public Debt Cash Redemp. (Table IIIB)') AS debt_redemptions
    FROM deposits_withdrawals
    WHERE record_date = (SELECT max(record_date) FROM deposits_withdrawals)
)
SELECT
    tga_deposits - debt_issues AS total_deposits,
    tga_withdrawals - debt_redemptions AS total_withdrawals,
    (tga_withdrawals - debt_redemptions) - (tga_deposits - debt_issues) AS net_transfers
FROM lines
```

Swap `transaction_today_amt` for `transaction_fytd_amt` to get the fiscal year to date.
