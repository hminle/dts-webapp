import type {
  IrsRefundComponent,
  IrsRefunds,
  MajorReceipts,
  MajorSpending,
  SubcategoryBreakdown,
  TBillInterest,
  TBillInterestComponent,
  YoYCategoryComparison,
  YoYDailyDataPoint,
} from './api'

// ── Summary of a daily YoY series ──────────────────────────────────────

export type YoYSummary = {
  latestDifference: number
  latestPercentChange: number | null
  latestCurrentValue: number
  latestPreviousValue: number
  averageDifference: number
  maxDifference: number
  minDifference: number
}

/** Latest / average / max / min of the year-over-year difference. */
export function summarize(points: YoYDailyDataPoint[]): YoYSummary | null {
  if (points.length === 0) return null
  const latest = points[points.length - 1]
  const differences = points.map((p) => p.difference)
  return {
    latestDifference: latest.difference,
    latestPercentChange: latest.percent_change ?? null,
    latestCurrentValue: latest.current_value,
    latestPreviousValue: latest.previous_value,
    averageDifference: differences.reduce((s, d) => s + d, 0) / points.length,
    maxDifference: Math.max(...differences),
    minDifference: Math.min(...differences),
  }
}

// ── Category cards ────────────────────────────────────────────────────

export type CategoryKind = 'spending' | 'receipt' | 'tbill' | 'irs_refund'
export type CategoryAccent = 'increase' | 'decrease' | 'receipt'

export type CategoryCardData = {
  name: string
  /** Null when the date predates `availableFrom`. */
  current_fytd: number | null
  previous_fytd: number | null
  yoy_change: number | null
  yoy_percent_change: number | null
  /** First date (ISO) the category's lines have their current shape. */
  availableFrom: string
  subcategories?: SubcategoryBreakdown[]
  tbillComponents?: TBillInterestComponent[]
  irsRefundComponents?: IrsRefundComponent[]
  categoryType: CategoryKind
  accent: CategoryAccent
}

// Spending: more is drawn as the primary series color, less as a warning. A
// change that cannot be computed gets the neutral border.
const spendingAccent = (delta: number | null): CategoryAccent =>
  delta === null || delta >= 0 ? 'increase' : 'decrease'

/** Spending cards: the major categories, then T-bill interest, then IRS refunds. */
export function spendingCards(
  spending: MajorSpending | undefined,
  tbill: TBillInterest | undefined,
  irs: IrsRefunds | undefined
): CategoryCardData[] {
  const cards: CategoryCardData[] = (spending?.categories ?? []).map((cat) => ({
    name: cat.name,
    current_fytd: cat.current_fytd,
    previous_fytd: cat.previous_fytd,
    yoy_change: cat.yoy_change,
    yoy_percent_change: cat.yoy_percent_change ?? null,
    availableFrom: cat.available_from,
    subcategories: cat.subcategories,
    categoryType: 'spending',
    accent: spendingAccent(cat.yoy_change),
  }))
  if (tbill) {
    cards.push({
      name: 'T-Bill Interest',
      current_fytd: tbill.total_current_fytd,
      previous_fytd: tbill.total_previous_fytd,
      yoy_change: tbill.total_yoy_change,
      yoy_percent_change: tbill.total_yoy_percent_change ?? null,
      availableFrom: tbill.available_from,
      tbillComponents: tbill.components,
      categoryType: 'tbill',
      accent: spendingAccent(tbill.total_yoy_change),
    })
  }
  if (irs) {
    cards.push({
      name: 'IRS Tax Refunds',
      current_fytd: irs.total_current_fytd,
      previous_fytd: irs.total_previous_fytd,
      yoy_change: irs.total_yoy_change,
      yoy_percent_change: irs.total_yoy_percent_change ?? null,
      availableFrom: irs.available_from,
      irsRefundComponents: irs.components,
      categoryType: 'irs_refund',
      accent: spendingAccent(irs.total_yoy_change),
    })
  }
  return cards
}

export function receiptCards(
  receipts: MajorReceipts | undefined
): CategoryCardData[] {
  return (receipts?.categories ?? []).map((cat) => ({
    name: cat.name,
    current_fytd: cat.current_fytd,
    previous_fytd: cat.previous_fytd,
    yoy_change: cat.yoy_change,
    yoy_percent_change: cat.yoy_percent_change ?? null,
    availableFrom: cat.available_from,
    subcategories: cat.subcategories,
    categoryType: 'receipt',
    accent: 'receipt',
  }))
}

// ── Breakdown table in the category dialog ────────────────────────────

export type BreakdownRow = {
  key: string
  name: string
  /** The Treasury's own code for the component, when it has one. */
  code?: string
  current: number
  previous: number
  change: number
}

/**
 * One row shape for subcategories, T-bill components and IRS components. A
 * row that is 0 in both years is an old line name absent from both, so it is
 * dropped.
 */
export function breakdownRows(card: CategoryCardData): BreakdownRow[] {
  return componentRows(card).filter(
    (row) => row.current !== 0 || row.previous !== 0
  )
}

function componentRows(card: CategoryCardData): BreakdownRow[] {
  if (card.tbillComponents?.length) {
    return card.tbillComponents.map((c) => ({
      key: c.adj_type,
      name: c.name,
      code: c.adj_type,
      current: c.current_fytd,
      previous: c.previous_fytd,
      change: c.yoy_change,
    }))
  }
  if (card.irsRefundComponents?.length) {
    return card.irsRefundComponents.map((c) => ({
      key: c.tax_refund_type,
      name: c.name,
      code: c.tax_refund_type,
      current: c.current_fytd,
      previous: c.previous_fytd,
      change: c.yoy_change,
    }))
  }
  return (card.subcategories ?? []).map((s) => ({
    key: s.category_name,
    name: s.category_name,
    current: s.current_fytd,
    previous: s.previous_fytd,
    change: s.yoy_change,
  }))
}

// ── Category comparison page ──────────────────────────────────────────

/**
 * Per-day (current FYTD − previous FYTD) for each category, on the days both
 * years have. Joined on `day_of_fiscal_year`, never on array position.
 */
export function categoryDiffSeries(
  data: YoYCategoryComparison
): Record<string, number>[] {
  const previousByCategory = new Map(
    (data.previous_year_data ?? []).map((cat) => [
      cat.category_description,
      new Map(
        (cat.data_points ?? []).map((p) => [
          p.day_of_fiscal_year,
          p.transaction_fytd_amt,
        ])
      ),
    ])
  )
  const byDay = new Map<number, Record<string, number>>()
  for (const cat of data.current_year_data ?? []) {
    const previous = previousByCategory.get(cat.category_description)
    if (!previous) continue
    for (const point of cat.data_points ?? []) {
      const prior = previous.get(point.day_of_fiscal_year)
      if (prior === undefined) continue
      const row = byDay.get(point.day_of_fiscal_year) ?? {
        day: point.day_of_fiscal_year,
      }
      row[cat.category_description] = point.transaction_fytd_amt - prior
      byDay.set(point.day_of_fiscal_year, row)
    }
  }
  return [...byDay.values()].sort((a, b) => a.day - b.day)
}

export type ComparisonRow = {
  day: number
  category: string
  currentDate: string
  previousDate: string | null
  currentFytd: number
  previousFytd: number
  difference: number
  /** Percent of |previous|; null when the previous year has nothing to compare. */
  percentChange: number | null
}

/**
 * Every current-year day of every category beside the same day last year. A
 * day the previous year lacks counts as 0 there, as in the reference.
 */
export function comparisonRows(data: YoYCategoryComparison): ComparisonRow[] {
  const rows: ComparisonRow[] = []
  for (const cat of data.current_year_data ?? []) {
    const previous = new Map(
      (
        (data.previous_year_data ?? []).find(
          (c) => c.category_description === cat.category_description
        )?.data_points ?? []
      ).map((p) => [p.day_of_fiscal_year, p])
    )
    for (const point of cat.data_points ?? []) {
      const prior = previous.get(point.day_of_fiscal_year)
      const previousFytd = prior?.transaction_fytd_amt ?? 0
      const difference = point.transaction_fytd_amt - previousFytd
      rows.push({
        day: point.day_of_fiscal_year,
        category: cat.category_description,
        currentDate: point.record_date,
        previousDate: prior?.record_date ?? null,
        currentFytd: point.transaction_fytd_amt,
        previousFytd,
        difference,
        percentChange:
          previousFytd !== 0
            ? (difference / Math.abs(previousFytd)) * 100
            : null,
      })
    }
  }
  return rows.sort(
    (a, b) => a.day - b.day || a.category.localeCompare(b.category)
  )
}
