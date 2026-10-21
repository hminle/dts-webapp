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
  | 'yoy-difference'
  | 'yoy-percent'
  | 'yoy-summary'
  | 'comparison-modes'
  | 'major-spending'
  | 'major-receipts'
  | 'tbill-interest'
  | 'irs-refunds'
  | 'category-comparison'
  | 'weekly-comparison'

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
      'Four groups of withdrawal line items, each the sum of the items’ fiscal-year-to-date amounts.',
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
      'Two groups of deposit line items. Customs sums the old and new line names so years on either side of the 2025 rename compare.',
    expression: ['Category FYTD = Σ FYTD of its deposit line items'],
    terms: [
      {
        term: 'Employment & Withholding Tax',
        meaning: 'Taxes - Withheld Individual/FICA',
      },
      {
        term: 'Customs & Duties (Tariffs)',
        meaning: 'DHS - Customs and Certain Excise Taxes',
      },
      {
        term: 'Customs & Duties (Tariffs)',
        meaning: 'DHS - Customs Duties, Taxes, and Fees',
      },
    ],
    pitfalls: [
      'The Treasury renamed the customs line in November 2025; reading only one name would make customs look like it vanished.',
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
      'Fiscal-year-to-date net transfers on each Friday, or the closest earlier statement when Friday had none, for two fiscal years.',
    expression: [
      'Week N = the Nth Friday on or after October 1',
      'Value = FYTD net transfers on that Friday, else up to 5 days earlier',
      'Weeks are matched by week number',
    ],
    pitfalls: [
      'The second year stops at the first year’s last week, so a year still in progress is compared with the same stretch of the other.',
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
  'yoy-difference',
  'yoy-percent',
  'yoy-summary',
  'comparison-modes',
  'major-spending',
  'major-receipts',
  'tbill-interest',
  'irs-refunds',
  'category-comparison',
  'weekly-comparison',
]
