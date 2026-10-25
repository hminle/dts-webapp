---
name: start-here
description: Which tool to use for which question, the units and fiscal year, the limits, and the other guides.
formulas: [today-mtd-fytd, fiscal-year]
---

# Start here

This server serves the U.S. Treasury Daily Treasury Statement (DTS): the cash that entered
and left the Treasury General Account (TGA) each business day, from 2005 on. The data is
public domain and is refreshed once per business day.

## The tools

| Tool | Use it for |
|---|---|
| `list_api(query)` | Find an API operation. `query` filters by id, path or summary. |
| `describe_api(operation_id)` | See an operation's parameters and response schema before calling it. |
| `call_api(operation_id, params)` | Get a figure the app shows. Use this first: its numbers are the app's numbers. |
| `run_query(sql, max_rows)` | Anything the API doesn't answer. One DuckDB `SELECT`, read-only. |
| `get_skills(name)` | These guides. Read the one for your question before computing a figure yourself. |

Prefer `call_api` for net transfers, year-over-year comparisons, weekly comparisons and the
major categories: the app's formulas have details (line items, alignment, sign) that are easy
to get wrong in hand-written SQL. Use `run_query` for custom cuts: other line items, other
date ranges, aggregates the app doesn't show.

## Units and dates

- Amounts are **millions of U.S. dollars**, stored as floats. `32776` means $32.776 billion.
- The federal **fiscal year** runs October 1 to September 30 and is named for the year it ends
  in: FY2027 starts on October 1, 2026. FY of a date = its year + 1 if the month is October or
  later, its year otherwise. Every table has `record_fiscal_year`.
- Each table has one row per Treasury line per business day. There are no rows for weekends
  and holidays.
- Every statement line has three amounts: today (that day alone), MTD (the month so far) and
  FYTD (the fiscal year so far). The Treasury publishes all three; read them rather than adding
  up days yourself. Compare a FYTD figure only with a FYTD figure from the same point of
  another year.

## Limits

- `run_query` returns 200 rows unless you pass `max_rows` (at most 2000). `truncated: true`
  means rows were cut off: aggregate in SQL instead of raising `max_rows`.
- A query is stopped after 10 seconds. Filter by `record_fiscal_year` or `record_date`, and
  aggregate.
- Two queries run at a time. A "retry in a few seconds" error means wait and retry.
- A tool response over 256 KB fails. For `call_api`, use a smaller `page_size` or a date
  range; for `run_query`, select fewer columns or lower `max_rows`.
- SQL cannot read files, reach the network, change settings or write anything.

## The other guides

- `data-model`: every table, what it holds, and its columns.
- `net-transfers`: total deposits, total withdrawals and net transfers, with SQL.
- `year-over-year`: lining up two fiscal years and the percent change.
- `categories`: the major spending and receipt categories, T-bill interest and IRS refunds.
