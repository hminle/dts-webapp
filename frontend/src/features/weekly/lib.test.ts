import { describe, expect, it } from 'vitest'
import type { WeeklyComparison } from './api'
import { computeSummaryStats, weekRows } from './lib'

const year = (weeks: [number, number][], fy: number) =>
  weeks.map(([week, fytd]) => ({
    week_number: week,
    record_date: `${fy}-wk${week}`,
    net_transfer_fytd: fytd,
  }))

const data = (first: [number, number][], second: [number, number][]) =>
  ({
    first_fiscal_year: 2026,
    second_fiscal_year: 2025,
    first_year_data: year(first, 2026),
    second_year_data: year(second, 2025),
    comparison_weeks: first.length,
  }) as unknown as WeeklyComparison

describe('weekRows', () => {
  it('pairs aligned weeks', () => {
    const rows = weekRows(
      data(
        [
          [1, 100],
          [2, 250],
        ],
        [
          [1, 90],
          [2, 200],
        ]
      )
    )
    expect(rows.map((r) => r.difference)).toEqual([10, 50])
  })

  it('joins on week number when a week is missing (the reference shifted every later week)', () => {
    const rows = weekRows(
      data(
        [
          [1, 100],
          [2, 200],
          [3, 300],
          [4, 400],
        ],
        [
          [1, 10],
          [2, 20],
          [4, 40],
        ]
      )
    )

    expect(rows[2]).toMatchObject({
      week: 3,
      secondFytd: 0,
      secondDate: '',
      difference: 300,
    })
    expect(rows[3]).toMatchObject({
      week: 4,
      secondFytd: 40,
      secondDate: '2025-wk4',
      difference: 360,
    })
  })

  it('treats an empty second year as zero everywhere', () => {
    const rows = weekRows(
      data(
        [
          [1, 100],
          [2, 250],
        ],
        []
      )
    )
    expect(rows.map((r) => r.difference)).toEqual([100, 250])
  })
})

describe('computeSummaryStats', () => {
  it('uses |second| as the percent denominator', () => {
    const s = computeSummaryStats(data([[1, 150]], [[1, -100]]))!
    expect(s.difference).toBe(250)
    expect(s.percentChange).toBe(250)
  })

  it('has no percent change when the second year is zero', () => {
    expect(computeSummaryStats(data([[1, 150]], []))!.percentChange).toBeNull()
  })

  it('is null without first-year data', () => {
    expect(computeSummaryStats(data([], [[1, 5]]))).toBeNull()
  })
})
