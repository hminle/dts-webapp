// Every formula the app computes, written once. The Methodology page renders
// these in FORMULA_ORDER; in-context hints reuse `summary`. Each entry is
// written from the backend code (backend/app/utils, services, constants), not
// from the reference app's docs, which drifted from its own code.

export type FormulaId =
  | 'today-mtd-fytd'
  | 'fiscal-year'
  | 'day-of-fiscal-year'
  | 'total-deposits'
  | 'total-withdrawals'
  | 'net-transfers'
  | 'leading-flow'
  | 'rolling-average'
  | 'cash-balance'
  | 'yoy-difference'
  | 'yoy-percent'
  | 'yoy-summary'
  | 'comparison-modes'
  | 'major-spending'
  | 'major-receipts'
  | 'other-spending'
  | 'other-receipts'
  | 'tbill-interest'
  | 'interest-income-transfers'
  | 'net-customs-receipts'
  | 'irs-refunds'
  | 'category-coverage'
  | 'category-comparison'
  | 'weekly-comparison'
  | 'weekly-snapshot'

export type FormulaTerm = { term: string; meaning: string }

export type FormulaDef = {
  /** Also the Methodology anchor: `/methodology#net-transfers`. */
  id: FormulaId
  title: string
  /** One sentence for hints; at most 160 characters. */
  summary: string
  /** One line per step, using − × ÷ |x| Σ. */
  expression: string[]
  /**
   * For the category formulas, `term` is the group and `meaning` is the exact
   * Treasury line name, which formulas.test.ts checks against the backend.
   */
  terms?: FormulaTerm[]
  /** What readers usually get wrong. */
  pitfalls?: string[]
  source: string
}

const DEPOSITS_TABLE = 'Deposits & Withdrawals of Operating Cash (Table II)'

export const FORMULAS: Record<FormulaId, FormulaDef> = {
  'today-mtd-fytd': {
    id: 'today-mtd-fytd',
    title: 'Today, month to date, fiscal year to date',
    summary:
      'Every statement line has three amounts: that day alone, the month so far, and the fiscal year so far.',
    expression: [
      'Today = the amount on that one business day',
      'MTD = Σ Today from the 1st of the month to that day',
      'FYTD = Σ Today from October 1 to that day',
    ],
    terms: [
      { term: 'MTD', meaning: 'Month to date' },
      { term: 'FYTD', meaning: 'Fiscal year to date' },
    ],
    pitfalls: [
      'The Treasury publishes all three columns; the app reads them rather than adding up days itself.',
      'A FYTD figure grows all year, so compare it only with a FYTD figure from the same point of another year.',
    ],
    source: 'Every Daily Treasury Statement table',
  },
  'fiscal-year': {
    id: 'fiscal-year',
    title: 'Fiscal year',
    summary:
      'The federal fiscal year runs October 1 to September 30 and is named for the year it ends in: FY2027 starts on October 1, 2026.',
    expression: [
      'FY of a date = its year + 1 if the month is October or later',
      'FY of a date = its year otherwise',
    ],
    pitfalls: [
      'FY2027 is mostly calendar year 2027, but its first quarter is October–December 2026.',
    ],
    source: 'record_fiscal_year column of each statement',
  },
  'day-of-fiscal-year': {
    id: 'day-of-fiscal-year',
    title: 'Day of the fiscal year',
    summary:
      'Day N is the Nth business day with a statement since October 1. Weekends and holidays are not counted.',
    expression: [
      'Day N = rank of the statement date among the fiscal year’s statement dates',
    ],
    pitfalls: [
      'Day 12 is not October 12: weekends and holidays push it later.',
      'A statement without totals keeps its day number but has no net-transfer figures.',
    ],
    source: `${DEPOSITS_TABLE}, record_date`,
  },
  'total-deposits': {
    id: 'total-deposits',
    title: 'Total deposits',
    summary:
      'Cash the government took in, minus money raised by selling new Treasury securities.',
    expression: [
      'Total deposits = TGA total deposits − public debt cash issues',
    ],
    terms: [
      {
        term: 'TGA total deposits',
        meaning:
          'Every dollar that entered the Treasury General Account that day',
      },
      {
        term: 'Public debt cash issues',
        meaning:
          'Cash received from selling bills, notes and bonds (new borrowing)',
      },
    ],
    pitfalls: [
      'Borrowing is removed so that a day of heavy debt sales does not look like a day of high tax receipts.',
    ],
    source: DEPOSITS_TABLE,
  },
  'total-withdrawals': {
    id: 'total-withdrawals',
    title: 'Total withdrawals',
    summary:
      'Cash the government paid out, minus money spent repaying Treasury securities that matured.',
    expression: [
      'Total withdrawals = TGA total withdrawals − public debt cash redemptions',
    ],
    terms: [
      {
        term: 'TGA total withdrawals',
        meaning: 'Every dollar that left the Treasury General Account that day',
      },
      {
        term: 'Public debt cash redemptions',
        meaning: 'Cash paid to holders of maturing bills, notes and bonds',
      },
    ],
    pitfalls: [
      'Interest on the debt stays in withdrawals; only the repayment of principal is removed.',
    ],
    source: DEPOSITS_TABLE,
  },
  'net-transfers': {
    id: 'net-transfers',
    title: 'Net transfers',
    summary:
      'Withdrawals minus deposits, both without borrowing. Positive means more went out than came in: a deficit day.',
    expression: ['Net transfers = total withdrawals − total deposits'],
    terms: [
      {
        term: 'Positive',
        meaning: 'Net outflow: spending exceeded receipts (deficit)',
      },
      {
        term: 'Negative',
        meaning: 'Net inflow: receipts exceeded spending (surplus)',
      },
    ],
    pitfalls: [
      'The sign is the opposite of a bank balance: a positive number is money leaving.',
      'One day can be a surplus while the fiscal year to date is a deficit; tax receipts arrive in large, uneven batches.',
    ],
    source: DEPOSITS_TABLE,
  },
  'leading-flow': {
    id: 'leading-flow',
    title: 'Leading flow',
    summary:
      'The day’s total withdrawals, shown as the size of the day’s spending.',
    expression: ['Leading flow = total withdrawals (today)'],
    source: DEPOSITS_TABLE,
  },
  'yoy-difference': {
    id: 'yoy-difference',
    title: 'Year-over-year difference',
    summary:
      'This year’s figure minus last year’s at the same point. Positive means this year is higher.',
    expression: ['Difference = current − previous'],
    terms: [
      { term: 'YoY', meaning: 'Year over year' },
      { term: 'Current', meaning: 'The newer fiscal year being compared' },
      {
        term: 'Previous',
        meaning: 'The older fiscal year, at the aligned date',
      },
    ],
    source: 'Computed by the app',
  },
  'yoy-percent': {
    id: 'yoy-percent',
    title: 'Year-over-year percent change',
    summary:
      'The difference divided by the size of last year’s figure. No percent is shown when last year was zero.',
    expression: [
      '% change = (current − previous) ÷ |previous| × 100',
      'previous = 0 → no percent',
    ],
    pitfalls: [
      'Dividing by |previous| keeps the sign meaningful: going from −50 to −30 is +40 %, an improvement.',
      'A small previous value makes the percent huge; read the difference too.',
    ],
    source: 'Computed by the app',
  },
  'yoy-summary': {
    id: 'yoy-summary',
    title: 'Latest, average, largest and smallest change',
    summary:
      'Summary cards over the days shown: the last day’s difference, the mean difference, and the highest and lowest difference.',
    expression: [
      'Latest = difference on the last day shown',
      'Average = Σ differences ÷ number of days',
      'Largest = max(differences)   Smallest = min(differences)',
    ],
    pitfalls: [
      'Largest means most positive, not largest in size: a −80 day is smaller than a +5 day.',
    ],
    source: 'Computed by the app from the daily comparison',
  },
  'comparison-modes': {
    id: 'comparison-modes',
    title: 'Lining up two years',
    summary:
      'Fiscal day compares day N with day N; calendar date compares the same month and day, falling back when last year had no statement.',
    expression: [
      'Fiscal day: current day N ↔ previous day N',
      'Calendar date: current MM-DD ↔ previous MM-DD',
    ],
    pitfalls: [
      'In calendar-date mode a weekend or holiday last year has no statement; each page handles that differently (see below).',
    ],
    source: 'Computed by the app',
  },
  'major-spending': {
    id: 'major-spending',
    title: 'Major spending categories',
    summary:
      'The four largest groups of withdrawal line items, each the sum of the items’ fiscal-year-to-date amounts.',
    expression: ['Category FYTD = Σ FYTD of its withdrawal line items'],
    terms: [
      { term: 'Social Security Benefits', meaning: 'SSA - Benefits Payments' },
      {
        term: 'Social Security Benefits',
        meaning: 'SSA - Supplemental Security Income',
      },
      {
        term: 'Social Security Benefits',
        meaning: 'Social Security Admin (SSA) - misc',
      },
      { term: 'Medicare', meaning: 'HHS - Federal Hospital Insr Trust Fund' },
      { term: 'Medicare', meaning: 'HHS - Federal Supple Med Insr Trust Fund' },
      { term: 'Medicare', meaning: 'HHS - Medicare Prescription Drugs' },
      { term: 'Medicaid', meaning: 'HHS - Grants to States for Medicaid' },
      { term: 'Medicaid', meaning: 'Medicaid' },
      {
        term: 'Interest on Treasury Securities',
        meaning: 'Interest on Treasury Securities',
      },
    ],
    pitfalls: [
      'Only the withdrawals side is read; a line with the same name on the deposits side is ignored.',
      'Interest on Treasury Securities is cash interest on notes and bonds. Bills pay no cash interest; see T-Bill interest.',
    ],
    source: DEPOSITS_TABLE,
  },
  'major-receipts': {
    id: 'major-receipts',
    title: 'Major receipt categories',
    summary:
      'Two groups of deposit line items. Customs sums every name its line has had, so years on either side of a rename compare.',
    expression: ['Category FYTD = Σ FYTD of its deposit line items'],
    terms: [
      {
        term: 'Employment & Withholding Tax',
        meaning: 'Taxes - Withheld Individual/FICA',
      },
      {
        term: 'Customs & Duties (Tariffs)',
        meaning: 'DHS - Customs Duties, Taxes, and Fees',
      },
      {
        term: 'Customs & Duties (Tariffs)',
        meaning: 'DHS - Customs and Certain Excise Taxes',
      },
      {
        term: 'Customs & Duties (Tariffs)',
        meaning: 'Customs and Certain Excise Taxes',
      },
    ],
    pitfalls: [
      'The Treasury renamed the customs line in May 2020 and November 2025; reading only one name would make customs look like it vanished.',
    ],
    source: DEPOSITS_TABLE,
  },
  'other-spending': {
    id: 'other-spending',
    title: 'Other spending categories',
    summary:
      'Ten more groups of withdrawal line items, each the sum of the items’ fiscal-year-to-date amounts.',
    expression: ['Category FYTD = Σ FYTD of its withdrawal line items'],
    terms: [
      {
        term: 'Department of Defense',
        meaning: 'Dept of Defense (DoD) - misc',
      },
      { term: 'Military Pay', meaning: 'DoD - Military Active Duty Pay' },
      { term: 'Military Pay', meaning: 'DoD - Military Retirement' },
      { term: 'Federal Salaries', meaning: 'Federal Salaries (EFT)' },
      {
        term: 'Healthcare Subsidies (Marketplace)',
        meaning: 'HHS - Marketplace Payments',
      },
      {
        term: 'Healthcare Subsidies (Marketplace)',
        meaning: 'Marketplace Payments',
      },
      { term: 'Department of Education', meaning: 'Dept of Education (ED)' },
      {
        term: 'Department of Education',
        meaning: 'Education Department programs',
      },
      {
        term: 'Housing & Urban Development',
        meaning: 'Dept of Housing & Urban Dev (HUD) - misc',
      },
      {
        term: 'Housing & Urban Development',
        meaning: 'HUD - Federal Housing Admin (FHA)',
      },
      {
        term: 'Housing & Urban Development',
        meaning: 'Housing and Urban Development programs',
      },
      {
        term: 'SNAP & WIC',
        meaning: 'USDA - Supp Nutrition Assist Prog (SNAP)',
      },
      {
        term: 'SNAP & WIC',
        meaning: 'USDA - Supp Nutrition Assist Prog (WIC)',
      },
      { term: 'Veterans Benefits', meaning: 'VA - Benefits' },
      { term: 'Unemployment Benefits', meaning: 'DOL - Unemployment Benefits' },
      {
        term: 'Unemployment Benefits',
        meaning: 'Unemployment Insurance Benefits',
      },
      {
        term: 'Customs Refunds (CBP)',
        meaning: 'DHS - Customs & Border Protection (CBP)',
      },
    ],
    pitfalls: [
      'Customs Refunds (CBP) is every Customs and Border Protection payment; since 2026 most of it is tariff refunds.',
      'Department of Defense is the DoD misc line only; military pay and DoD health are separate lines.',
    ],
    source: DEPOSITS_TABLE,
  },
  'other-receipts': {
    id: 'other-receipts',
    title: 'Other receipt categories',
    summary: 'Four more groups of deposit line items.',
    expression: ['Category FYTD = Σ FYTD of its deposit line items'],
    terms: [
      {
        term: 'Individual Income Taxes',
        meaning: 'Taxes - Non Withheld Ind/SECA Electronic',
      },
      {
        term: 'Individual Income Taxes',
        meaning: 'Taxes - Non Withheld Ind/SECA Other',
      },
      { term: 'Corporate Income Taxes', meaning: 'Taxes - Corporate Income' },
      {
        term: 'Education Receipts (Student Loans)',
        meaning: 'Dept of Education (ED)',
      },
      {
        term: 'Education Receipts (Student Loans)',
        meaning: 'Education Department programs',
      },
      {
        term: 'Public Debt Cash Issues',
        meaning: 'Public Debt Cash Issues (Table IIIB)',
      },
      {
        term: 'Public Debt Cash Issues',
        meaning: 'Public Debt Cash Issues (Table III-B)',
      },
    ],
    pitfalls: [
      'Public debt cash issues is borrowing, not revenue; net transfers exclude it.',
    ],
    source: DEPOSITS_TABLE,
  },
  'rolling-average': {
    id: 'rolling-average',
    title: 'Rolling average and monthly rate',
    summary:
      'The mean of the last 10 statements’ amounts; for withdrawals, × 20 gives a projected monthly rate.',
    expression: [
      '10-day average = Σ amount over the last 10 statements ÷ 10',
      'Projected monthly rate = 10-day average of withdrawals × 20',
    ],
    pitfalls: [
      'It counts statements, not calendar days: weekends and holidays are skipped.',
      'A window holding the 1st of the month or a mid-month interest date runs high; the rate swings with payment calendars.',
    ],
    source: DEPOSITS_TABLE,
  },
  'cash-balance': {
    id: 'cash-balance',
    title: 'Treasury cash balance',
    summary:
      'The Treasury General Account’s closing balance at the Federal Reserve on each statement date.',
    expression: [
      'Closing balance = opening balance + deposits − withdrawals (Table I)',
    ],
    pitfalls: [
      'Unlike net transfers, the balance includes borrowing: debt sales raise it, redemptions lower it.',
      'Since April 2022 the Treasury reports the closing balance on its own row.',
    ],
    source: 'Operating Cash Balance (Table I)',
  },
  'interest-income-transfers': {
    id: 'interest-income-transfers',
    title: 'Interest income transfers',
    summary:
      'Cash interest on notes and bonds plus the T-bill discount: all interest the Treasury pays holders.',
    expression: [
      'Interest income = Interest on Treasury Securities + T-Bill interest',
    ],
    terms: [
      {
        term: 'Interest on Treasury Securities',
        meaning: 'Cash interest on notes and bonds (withdrawals)',
      },
      {
        term: 'T-Bill Interest',
        meaning: 'Bills (−) + Bonds and Notes (−) discount (adjustments)',
      },
    ],
    pitfalls: [
      'Comparable from 2022-09-12, when T-bill interest got its own lines.',
    ],
    source:
      'Tables II and IIIB: Deposits & Withdrawals, and Adjustment of Public Debt Transactions',
  },
  'net-customs-receipts': {
    id: 'net-customs-receipts',
    title: 'Net customs receipts',
    summary:
      'Customs deposits minus Customs and Border Protection payments, which since 2026 are mostly tariff refunds.',
    expression: [
      'Net customs = Customs & Duties (Tariffs) − Customs Refunds (CBP)',
    ],
    pitfalls: [
      'CBP payments include more than refunds; before 2026 they are small.',
      'Comparable from 2020-05-11, when the CBP line starts.',
    ],
    source: DEPOSITS_TABLE,
  },
  'tbill-interest': {
    id: 'tbill-interest',
    title: 'T-Bill interest',
    summary:
      'Bills are sold below face value; the discount is their interest. The app sums the two discount lines of the public-debt adjustments.',
    expression: ['T-Bill interest FYTD = Bills (−) + Bonds and Notes (−)'],
    terms: [
      { term: 'Discount on bills', meaning: 'Bills (-)' },
      { term: 'Discount on notes and bonds', meaning: 'Bonds and Notes (-)' },
    ],
    pitfalls: [
      'This interest never appears as a cash withdrawal, so it is not part of “Interest on Treasury Securities”.',
    ],
    source: 'Adjustment of Public Debt Transactions to Cash Basis (Table IIIB)',
  },
  'irs-refunds': {
    id: 'irs-refunds',
    title: 'IRS tax refunds',
    summary:
      'The four individual and business refund lines (EFT and check) from the Income Tax Refunds Issued table.',
    expression: ['IRS refunds FYTD = Σ FYTD of the four refund types'],
    terms: [
      {
        term: 'Individual (EFT)',
        meaning: 'Taxes - Individual Tax Refunds (EFT)',
      },
      {
        term: 'Individual (checks)',
        meaning: 'Taxes - Individual Tax Refunds (Checks)',
      },
      { term: 'Business (EFT)', meaning: 'Taxes - Business Tax Refunds (EFT)' },
      {
        term: 'Business (checks)',
        meaning: 'Taxes - Business Tax Refunds (Checks)',
      },
    ],
    pitfalls: [
      'Table II lists only the EFT refund lines, so adding them up there misses every refund paid by check.',
    ],
    source: 'Income Tax Refunds Issued (Table V)',
  },
  'category-coverage': {
    id: 'category-coverage',
    title: 'When a category can be compared',
    summary:
      'A category is compared only from the date its Treasury lines took their current shape; earlier totals are blank, not zero.',
    expression: [
      'Total on a date = Σ FYTD of its lines, if date ≥ first comparable date',
      'Otherwise: no value',
    ],
    terms: [
      { term: 'Social Security Benefits', meaning: 'Comparable from 2021-07-19' },
      { term: 'Medicare', meaning: 'Comparable from 2020-03-09' },
      { term: 'Medicaid', meaning: 'October 2005 (all data)' },
      {
        term: 'Interest on Treasury Securities',
        meaning: 'October 2005 (all data)',
      },
      {
        term: 'Employment & Withholding Tax',
        meaning: 'Comparable from 2023-02-14',
      },
      { term: 'Customs & Duties (Tariffs)', meaning: 'October 2005 (all data)' },
      { term: 'T-Bill Interest', meaning: 'Comparable from 2022-09-12' },
      { term: 'IRS Tax Refunds', meaning: 'Comparable from 2023-02-14' },
    ],
    pitfalls: [
      'A renamed line is summed under every name it has had; only one name exists on any date.',
    ],
    source: DEPOSITS_TABLE,
  },
  'category-comparison': {
    id: 'category-comparison',
    title: 'Category comparison',
    summary:
      'Any Treasury line item’s fiscal-year-to-date amount, day by day, for two fiscal years lined up by day number.',
    expression: [
      'For each day N: difference = current FYTD − previous FYTD',
      '% change = difference ÷ |previous FYTD| × 100',
    ],
    pitfalls: [
      'Day numbers here count only the days on which the chosen line item appears. Most items appear on every statement, so the numbers match the rest of the app.',
    ],
    source: DEPOSITS_TABLE,
  },
  'weekly-comparison': {
    id: 'weekly-comparison',
    title: 'Weekly comparison',
    summary:
      'Fiscal-year-to-date net transfers on each week’s anchor day, or the closest earlier statement when it had none, for two fiscal years.',
    expression: [
      'Week N = the Nth anchor day (Friday by default, or Thursday) on or after October 1',
      'Value = FYTD net transfers on that day, else up to 5 days earlier',
      'Weeks are matched by week number',
    ],
    pitfalls: [
      'The second year stops at the first year’s last week, so a year still in progress is compared with the same stretch of the other.',
    ],
    source: DEPOSITS_TABLE,
  },
  'weekly-snapshot': {
    id: 'weekly-snapshot',
    title: 'Weekly snapshot',
    summary:
      'One week’s statement against the same business day a year earlier, and how the net-transfers gap moved since the week before.',
    expression: [
      'Snapshot date = latest statement on or up to 5 days before the anchor weekday',
      'Change = FYTD(snapshot) − FYTD(same day of the previous fiscal year)',
      'Gap change = this week’s net-transfers change − last week’s',
    ],
    pitfalls: [
      'The gap change is blank in the first week of a fiscal year: last week belongs to another pair of years.',
      'After a holiday the snapshot uses the closest earlier statement, so its month-to-date covers one day less.',
    ],
    source: DEPOSITS_TABLE,
  },
}

/** The order the Methodology page presents the formulas in. */
export const FORMULA_ORDER: FormulaId[] = [
  'today-mtd-fytd',
  'fiscal-year',
  'day-of-fiscal-year',
  'total-deposits',
  'total-withdrawals',
  'net-transfers',
  'leading-flow',
  'rolling-average',
  'cash-balance',
  'yoy-difference',
  'yoy-percent',
  'yoy-summary',
  'comparison-modes',
  'major-spending',
  'major-receipts',
  'other-spending',
  'other-receipts',
  'net-customs-receipts',
  'tbill-interest',
  'interest-income-transfers',
  'irs-refunds',
  'category-coverage',
  'category-comparison',
  'weekly-comparison',
  'weekly-snapshot',
]
