---
name: year-over-year
description: How the app lines up two fiscal years, computes the difference and percent change, and compares weeks.
formulas: [yoy-difference, yoy-percent, yoy-summary, comparison-modes, weekly-comparison]
---

# Year over year

## Lining up two years

Compare day N of the current fiscal year with day N of the previous one, using
`day_of_fiscal_year` (see `data-model`), not the calendar date. Weekends and holidays fall on
different dates each year, and a FYTD figure is only comparable at the same point of the year.

The API also offers `comparison_mode="calendar_date"`, which matches the same month and day
instead. Last year may have no statement on that date; let the API handle that rather than
reimplementing it.

## The formula

```
Difference = current − previous
% change   = (current − previous) ÷ |previous| × 100
previous = 0 → no percent
```

Dividing by |previous| keeps the sign meaningful: going from
{{example:yoy_negative_base.previous}} to {{example:yoy_negative_base.current}} is a difference
of {{example:yoy_negative_base.difference}} and +{{example:yoy_negative_base.percent_change}} %,
an improvement. A small previous value makes the percent huge; read the difference too.

## Worked example

FYTD net transfers on day {{example:yoy.day_of_fiscal_year}}:

| | Date | FYTD net transfers |
|---|---|---|
| Current, FY{{example:yoy.current.fiscal_year}} | {{example:yoy.current.date}} | {{example:yoy.current.value}} |
| Previous, FY{{example:yoy.previous.fiscal_year}} | {{example:yoy.previous.date}} | {{example:yoy.previous.value}} |

Difference {{example:yoy.difference}}; percent change {{example:yoy.percent_change}} %.

## Summary figures

Over the days shown: latest = the last day's difference; average = Σ differences ÷ number of
days; largest = max(differences); smallest = min(differences). Largest means most positive, not
largest in size: a −80 day is smaller than a +5 day.

## Weekly comparison

FYTD net transfers on each Friday, or the closest earlier statement up to 5 days before when
Friday had none, for two fiscal years. Week N is the Nth Friday on or after October 1, and weeks
are matched by week number. The second year stops at the first year's last week, so a year
still in progress is compared with the same stretch of the other.

## Getting it

- `call_api("yoy_get_daily_comparison", {"current_fiscal_year": 2027, "previous_fiscal_year": 2026, "metric": "net_flow"})`:
  day-by-day comparison. `metric` is `net_flow`, `total_withdrawals`, `total_deposits` or a
  category name.
- `call_api("yoy_get_category_comparison", ...)`: any line items (`category_descriptions`).
- `call_api("weekly_get_comparison", {"first_fiscal_year": 2026, "second_fiscal_year": 2027})`.

In SQL, aligned by day number:

```sql
SELECT
    c.day_of_fiscal_year,
    c.record_date AS current_date,
    p.record_date AS previous_date,
    c.net_flow_fytd AS current_fytd,
    p.net_flow_fytd AS previous_fytd,
    c.net_flow_fytd - p.net_flow_fytd AS difference,
    round((c.net_flow_fytd - p.net_flow_fytd) / nullif(abs(p.net_flow_fytd), 0) * 100, 2)
        AS percent_change
FROM daily_net_transfers c
JOIN daily_net_transfers p
  ON p.record_fiscal_year = c.record_fiscal_year - 1
 AND p.day_of_fiscal_year = c.day_of_fiscal_year
WHERE c.record_fiscal_year = (SELECT max(record_fiscal_year) FROM daily_net_transfers)
ORDER BY c.day_of_fiscal_year
```
