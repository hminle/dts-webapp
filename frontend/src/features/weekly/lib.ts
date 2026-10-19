import type { WeeklyComparison, WeeklyDataPoint } from './api'

export type WeekRow = {
  week: number
  firstDate: string
  secondDate: string
  firstFytd: number
  secondFytd: number
  difference: number
}

/**
 * One row per week of the first year, joined to the second year on
 * `week_number`. The reference paired the two lists by array position, so a
 * week missing from one year shifted every later week onto the wrong partner.
 * A week the second year lacks counts as 0 with no date.
 */
export function weekRows(data: WeeklyComparison): WeekRow[] {
  const second = new Map(
    (data.second_year_data ?? []).map((p) => [p.week_number, p] as const)
  )
  return (data.first_year_data ?? []).map((firstPoint: WeeklyDataPoint) => {
    const secondPoint = second.get(firstPoint.week_number)
    const firstFytd = firstPoint.net_transfer_fytd || 0
    const secondFytd = secondPoint?.net_transfer_fytd || 0
    return {
      week: firstPoint.week_number,
      firstDate: firstPoint.record_date,
      secondDate: secondPoint?.record_date ?? '',
      firstFytd,
      secondFytd,
      difference: firstFytd - secondFytd,
    }
  })
}

export type WeeklySummary = {
  firstYearTotal: number
  secondYearTotal: number
  difference: number
  /** Percent of |secondYearTotal|; null when the second year is zero. */
  percentChange: number | null
}

/** Latest FYTD of each year and the difference between them. */
export function computeSummaryStats(
  data: WeeklyComparison
): WeeklySummary | null {
  const first = data.first_year_data ?? []
  const second = data.second_year_data ?? []
  if (first.length === 0) return null
  const firstYearTotal = first[first.length - 1]?.net_transfer_fytd || 0
  const secondYearTotal = second[second.length - 1]?.net_transfer_fytd || 0
  const difference = firstYearTotal - secondYearTotal
  return {
    firstYearTotal,
    secondYearTotal,
    difference,
    percentChange:
      secondYearTotal !== 0
        ? (difference / Math.abs(secondYearTotal)) * 100
        : null,
  }
}
