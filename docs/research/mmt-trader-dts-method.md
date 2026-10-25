# MMT Trader newsletter: how its DTS figures are computed

This note explains how the weekly *MMT Trader* newsletter computes the Daily Treasury
Statement (DTS) figures in its **Fiscal Snapshot**, **Net Gov't Transfers** and **Fiscal
Flows** sections. It also lists the errors that keep recurring.

We rebuilt each figure from the app's DuckDB data through the `dts-public` MCP server. The
newsletter has no published methodology, so the definitions below are reverse-engineered.
A definition counts as confirmed only when it reproduces his figures to the decimal across
several issues.

| Issue | Data date he uses |
|---|---|
| Dec 8–12, 2025 (Vol X, 502) | Thu 2025-12-04 |
| Dec 15–19, 2025 (Vol X, 503) | Thu 2025-12-11 |
| Dec 22–26, 2025 (Vol X, 504) | Thu 2025-12-18 |
| Aug 2026 (Vol XI, 535; file `mmttrader08172026`) | Thu 2026-08-13 |
| Oct 12–16, 2026 (Vol XI, 540) | Tue 2026-10-06 (exception, see below) |

All amounts are millions of dollars in the data and billions in the newsletter.

---

## 1. Formulas

### 1.1 Data date: the Thursday statement

Each issue uses the DTS for the **Thursday** before the issue's Monday. The Oct 12, 2026
issue is the only exception: its main totals come from Oct 6, and its 10-day average from
Oct 7. See §2.4.

### 1.2 Total withdrawals, total deposits, net transfers

These are the same as the app's `net-transfers` formula. Borrowing is removed from both sides:

```
Total deposits    = TGA total deposits    − Public Debt Cash Issues (Table IIIB)
Total withdrawals = TGA total withdrawals − Public Debt Cash Redemp. (Table IIIB)
Net transfers     = total withdrawals − total deposits     (positive = deficit)
```

He reports all three as fiscal year to date (FYTD). In the app they are
`daily_net_transfers.total_withdrawals_fytd`, `total_deposits_fytd` and `net_flow_fytd`.

### 1.3 Year-over-year: same business day of the previous fiscal year

Each figure is compared with the previous fiscal year **on the same business day of the
fiscal year**, not on the same calendar date. The app's equivalent is
`yoy_get_daily_comparison` with `comparison_mode = "fiscal_day"`.

In December 2025 the two methods compare the same two dates, so those issues can't tell
them apart. Aug 13, 2026 can: there, matching by business day reproduces his figures and
matching by calendar date does not.

| Aug 13, 2026 | Newsletter | By business day (vs 2025-08-14) | By calendar date (vs 2025-08-13) |
|---|---|---|---|
| Withdrawals | +423.5 | **+423.5** | +437.9 |
| Deposits | +380.9 | **+380.9** | +390.4 |
| Net transfers | +42.6 | **+42.6** | +47.5 |
| Withholding tax | +119.0 | **+119.0** | +121.8 |

The Aug 27, 2026 figures on page 9 of the Oct 12 issue match the same way (+389.3, +436.5,
+126.1 by business day; +397.2, +454.2, +129.1 by calendar date).

### 1.4 Month-to-date lines

"Withdrawals for <month> through <date>" and "Net gov't transfers for <month>" are the
**month-to-date** versions of the totals in §1.2 (`total_withdrawals_mtd`, `net_flow_mtd`).

| Date | Withdrawals MTD | Net transfers MTD |
|---|---|---|
| 2025-12-04 | 200.2 ✅ | 120.8 ✅ |
| 2025-12-11 | 333.4 ✅ | 163.9 ✅ |
| 2025-12-18 | 459.3 ✅ | 129.4 ✅ |
| 2026-08-13 | 217.9 ✅ | 50.9 ✅ |

### 1.5 10-day average of withdrawals and the "monthly rate"

```
10-day average  = mean of total_withdrawals_today over the last 10 statements
Monthly rate    = 10-day average × 20
```

The 20 stands for roughly 20 business days in a month.

| Date | 10-day average | ×20 | Newsletter |
|---|---|---|---|
| 2025-12-04 | 35.6 | 712 | 35.6 → 712.2 ✅ |
| 2025-12-11 | 34.7 | 694 | 34.7 → 694.0 ✅ |
| 2025-12-18 | 25.9 | 518 | 25.9 → 518.2 ✅ |
| 2026-08-13 | 37.1 | 742 | 37.1 → 741.5 ✅ |

The unemployment 10-day average is computed the same way over `DOL - Unemployment Benefits`
daily amounts, but his figures differ from ours by $0.1–0.4 million. See §2.5.

### 1.6 Category definitions

Every category is the sum of the FYTD amounts (`transaction_fytd_amt`) of these lines in
`deposits_withdrawals`, unless noted otherwise.

**Withdrawals (government spending)**

| Newsletter label | Treasury line(s) |
|---|---|
| Social Security benefits | `SSA - Benefits Payments` + `SSA - Supplemental Security Income` + `Social Security Admin (SSA) - misc` |
| Medicare | `HHS - Federal Hospital Insr Trust Fund` + `HHS - Federal Supple Med Insr Trust Fund` + `HHS - Medicare Prescription Drugs` |
| Medicaid | `HHS - Grants to States for Medicaid` |
| Interest on Treasury securities | `Interest on Treasury Securities` |
| Department of Defense | `Dept of Defense (DoD) - misc` only |
| Military pay (active and retired) | `DoD - Military Active Duty Pay` + `DoD - Military Retirement` |
| Federal salaries | `Federal Salaries (EFT)` |
| Healthcare subsidies | `HHS - Marketplace Payments` |
| Department of Education | `Dept of Education (ED)` (withdrawal side) |
| HUD | `Dept of Housing & Urban Dev (HUD) - misc` + `HUD - Federal Housing Admin (FHA)` ⚠️ see §2.1 |
| SNAP | `USDA - Supp Nutrition Assist Prog (SNAP)` + `USDA - Supp Nutrition Assist Prog (WIC)` ⚠️ see §2.1 |
| Veterans benefits | `VA - Benefits` |
| Tariff rebates | `DHS - Customs & Border Protection (CBP)` (**withdrawal** side) |
| Unemployment benefits | `DOL - Unemployment Benefits` |
| IRS tax refunds | `income_tax_refunds.tax_refund_fytd_amt`, all four refund types |

**Deposits (government receipts)**

| Newsletter label | Treasury line(s) |
|---|---|
| Employment and withholding tax | `Taxes - Withheld Individual/FICA` |
| Individual income taxes | `Taxes - Non Withheld Ind/SECA Electronic` + `Taxes - Non Withheld Ind/SECA Other` |
| Corporation income taxes | `Taxes - Corporate Income` |
| Customs and excise taxes (tariffs) | `DHS - Customs Duties, Taxes, and Fees` (the pre-Nov-2025 name is `DHS - Customs and Certain Excise Taxes`) |
| Department of Education (student loans) | `Dept of Education (ED)` (deposit side) |
| Public debt cash issues | `Public Debt Cash Issues (Table IIIB)` |

**Interest**

| Newsletter label | Formula |
|---|---|
| T-bill interest | `adjustment_public_debt.adj_fytd_amt` for `Bills (-)` + `Bonds and Notes (-)` |
| Interest income transfers, change | change in interest on Treasury securities + change in T-bill interest |
| Total interest income transfers | interest on Treasury securities + T-bill interest |

Example, Dec 4, 2025: interest 141.7 (+21.7), T-bill 50.9 (−6.8). His interest-income change
is 21.7 − 6.8 = +14.9 and his total is 141.7 + 50.9 = 192.6, both exact.

### 1.7 Commentary figures

- **"% of GDP"**: net transfers ÷ an annual GDP of roughly $30.5–31T (475.5 → 1.54%,
  1.51T → 4.95%).
- **"Trending to $600 bln a year"**: the year-over-year gap scaled up linearly to a full year
  (Dec 4: −112.1 × 250/46 business days ≈ −609). He kept saying "$600 bln" a week later,
  when the same scaling gives about −667.

---

## 2. Error patterns

### 2.1 HUD and SNAP: the total and the change use different lines (every issue)

The **total** adds both lines, but the **year-over-year change** uses only the first one
(HUD misc, or SNAP without WIC). It looks like a spreadsheet change formula that was never
extended to the second line.

| Issue date | Item | Total reported | Change reported | Change on first line only | Correct change (both lines) |
|---|---|---|---|---|---|
| 2025-12-04 | HUD | 21.6 ✅ | +0.035 | +0.035 | **−0.007** |
| 2025-12-11 | HUD | 23.2 ✅ | +0.779 | +0.779 | +0.7 |
| 2025-12-18 | HUD | 23.9 ✅ | +0.669 | +0.669 | **+0.4** |
| 2026-08-13 | HUD | 91.2 ✅ | −1.04 | −1.04 | **−4.1** |
| 2025-12-04 | SNAP | 18.8 ✅ | −1.9 | −1.9 | −2.0 |
| 2025-12-11 | SNAP | 21.4 ✅ | −2.1 | −2.1 | **−2.3** |
| 2025-12-18 | SNAP | 23.9 ✅ | −2.3 | −2.3 | **−2.5** |
| 2026-08-13 | SNAP | 90.4 ✅ | −9.7 | −9.7 | **−10.0** |

**Fix:** use both lines for the change too.

### 2.2 Sidebar blocks left over from the previous issue

The **Fiscal Snapshot** sidebar is often not updated. It carries last week's figures while
the body text has the current ones.

| Issue | Stale block | Shown | Correct |
|---|---|---|---|
| Dec 15, 2025 | Net Government Transfers | 475.5 / 587.6 / −112.1 (from Dec 8) | **518.5 / 654.6 / −136.1** |
| Dec 22, 2025 | Withholding change | +26.3 (from Dec 15) | **+18.7**; his own figures give 734.6 − 715.9 = 18.7 |
| Oct 12, 2026 | Withholding change | +126.1 (from Aug 27) | year end: **+149.8** |
| Oct 12, 2026 | FY2026 withdrawals / net transfers | 7.66T, +486.7 / 1.72T vs 1.63T, +81.3 (early-to-mid September) | year end: **8.243T, +509.9 / 1.684T vs 1.624T, +60.4** |
| Oct 12, 2026 | Unemployment 10-day average | 151.7 (matches Aug 20) | Oct 6–7: **~124** |

**Check:** subtract the sidebar's two years yourself. When the printed change disagrees,
the block is stale.

### 2.3 Values pasted into the wrong place

- **Aug 17, 2026:** "T-Bill interest, $68.9 bln, down $13.6 bln." The real total is
  **$241.3B**. 68.9 is the interest-income change from the next sentence. His own total of
  809.2 = 567.9 + 241.3 confirms it.
- **Oct 12, 2026:** "Net government transfers through Oct. 8, 189.7 bln." 189.7 is FY2027
  **total withdrawals** through **Oct 6**. Net transfers were 103.8 on Oct 6 and 111.5 on
  Oct 8.

### 2.4 Wrong dates, and one issue that breaks his own Thursday rule

- **Dec 8, 2025:** "Net government transfers through December 6." Dec 6 was a Saturday; the
  data is from **Dec 4**.
- **Aug 17, 2026:** "Withdrawals for **Jul** through Aug 13" should say Aug. The 217.9 is
  August month to date.
- **Oct 12, 2026:** under his Thursday rule the data should be Oct 8. He used **Oct 6** for
  the totals and withholding tax, and Oct 7 for the 10-day average. That issue's "up
  $67.9 bln", "$22.1 bln" and "gap narrowed by $42.2 bln" could not be reproduced from any
  single date under either way of lining up the years.

### 2.5 Typos and small mismatches

| Issue | Printed | Correct |
|---|---|---|
| Dec 15, 2025 | Overview "down $136.4 bln" | −136.1 (as in the body) |
| Dec 22, 2025 | Customs total $76.7 bln | **$73.8B** (the +54.6 change is right) |
| Aug 17, 2026 | Withholding tax "$3127T" | $3.12T |
| Aug 17, 2026 | Turnaround since January given as $302.6B, $312.6B and $270B | three different numbers in one issue |
| All | Unemployment 10-day average (173.5, 194.2, 195.8, 151.9) | ours: 173.6, 194.3, 195.6, 151.5, probably a different window |

---

## 3. How to check a new issue

1. Find the Thursday before the issue date, and check that the FYTD withdrawals match that
   date's `total_withdrawals_fytd`. If not, try the Tuesday or Wednesday before (see §2.4).
2. Compute every year-over-year change against the same business day of the previous fiscal
   year: `call_api("yoy_get_daily_comparison", {current_fiscal_year, previous_fiscal_year,
   metric})`, or join `daily_net_transfers` on `day_of_fiscal_year`.
3. Sum the categories with the line sets in §1.6.
4. Expect HUD and SNAP changes to be off (§2.1). Recompute each sidebar change from its two
   printed years (§2.2).
5. Where a figure can't be reproduced, say so. A brute-force search over many pairs of dates
   will turn up chance matches, so don't treat those as explanations.
