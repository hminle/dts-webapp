import { describe, expect, it } from 'vitest'
import type { CashBalancePoint } from './api'
import { latestChange } from './lib'

const point = (record_date: string, closing_balance: number) =>
  ({ record_date, closing_balance }) as CashBalancePoint

describe('latestChange', () => {
  const points = [
    point('2026-08-20', 935077),
    point('2026-08-21', 940000),
    point('2026-08-24', 921000),
    point('2026-08-25', 930000),
    point('2026-08-26', 944000),
    point('2026-08-27', 950804),
  ]

  it('compares with the point five statements earlier', () => {
    expect(latestChange(points)).toEqual({
      latest: points[5],
      previous: points[0],
      change: 15727,
    })
  })

  it('is null without enough points', () => {
    expect(latestChange(points.slice(1))).toBeNull()
    expect(latestChange([])).toBeNull()
  })
})
