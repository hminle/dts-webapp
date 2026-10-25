---
name: categories
description: The major and other spending and receipt categories, T-bill interest and IRS refunds: which Treasury lines each sums, with SQL.
formulas: [major-spending, major-receipts, other-spending, other-receipts, tbill-interest, irs-refunds, category-coverage, category-comparison]
---

# Categories

A category is the sum of the **FYTD** amounts of a fixed list of Treasury line items on one
date. Compare it with the previous fiscal year at the aligned date (see `year-over-year`).

| Kind | Table | Line item column | Amount column | Filter |
|---|---|---|---|---|
| spending | `deposits_withdrawals` | `transaction_catg` | `transaction_fytd_amt` | `transaction_type = 'Withdrawals'` |
| receipt | `deposits_withdrawals` | `transaction_catg` | `transaction_fytd_amt` | `transaction_type = 'Deposits'` |
| tbill | `adjustment_public_debt` | `adj_type` | `adj_fytd_amt` | |
| irs_refund | `income_tax_refunds` | `tax_refund_type` | `tax_refund_fytd_amt` | |

Pitfalls:

- Only the matching side is read: a spending line with the same name on the deposits side is
  ignored.
- Interest on Treasury Securities is cash interest on notes and bonds. Bills pay no cash
  interest; their discount is T-bill interest, which never appears as a cash withdrawal.
- The Treasury renamed the customs line in May 2020 and November 2025; customs sums all three
  names so years on either side of a rename compare.
- A category is compared only from its first comparable date ("Comparable from" below). Before
  it the Treasury restructured the lines, so API totals are `null`, not 0. Renamed lines are
  summed under all their names; on any one date only one name exists.
- `deposits_withdrawals` lists only the EFT refund lines, so adding them up there misses every
  refund paid by check. IRS refunds come from `income_tax_refunds`.

## The categories

{{categories}}

## Worked example: Medicare

On {{example:categories.current_date}}, FYTD:

| Line item | Current | Previous ({{example:categories.previous_date}}) |
|---|---|---|
| HHS - Federal Hospital Insr Trust Fund | {{example:categories.medicare.current.HHS - Federal Hospital Insr Trust Fund}} | {{example:categories.medicare.previous.HHS - Federal Hospital Insr Trust Fund}} |
| HHS - Federal Supple Med Insr Trust Fund | {{example:categories.medicare.current.HHS - Federal Supple Med Insr Trust Fund}} | {{example:categories.medicare.previous.HHS - Federal Supple Med Insr Trust Fund}} |
| HHS - Medicare Prescription Drugs | {{example:categories.medicare.current.HHS - Medicare Prescription Drugs}} | {{example:categories.medicare.previous.HHS - Medicare Prescription Drugs}} |
| **Medicare** | **{{example:categories.medicare.current_total}}** | **{{example:categories.medicare.previous_total}}** |

Difference {{example:categories.medicare.difference}}; percent change
{{example:categories.medicare.percent_change}} %.

## Getting it

- `call_api("categories_get_major_spending", {"current_fiscal_year": 2027, "previous_fiscal_year": 2026})`,
  and likewise `categories_get_major_receipts`, `categories_get_tbill_interest`,
  `categories_get_irs_tax_refunds`.
- `call_api("categories_get_daily_yoy", ...)`: one category day by day for two years.
- `call_api("yoy_get_category_comparison", ...)`: any line items day by day. Day numbers there
  count only the days on which the chosen line item appears.

In SQL, Medicare FYTD on the latest date:

```sql
SELECT record_date, sum(transaction_fytd_amt) AS medicare_fytd
FROM deposits_withdrawals
WHERE transaction_type = 'Withdrawals'
  AND transaction_catg IN (
      'HHS - Federal Hospital Insr Trust Fund',
      'HHS - Federal Supple Med Insr Trust Fund',
      'HHS - Medicare Prescription Drugs')
  AND record_date = (
      SELECT max(record_date) FROM deposits_withdrawals
      WHERE transaction_type = 'Withdrawals')
GROUP BY record_date
```
