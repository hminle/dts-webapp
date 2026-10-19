import { describe, expect, it } from 'vitest'
import type { DailyNetTransfer } from './api'
import { flowDirection, formulaSteps } from './lib'

// 2026-10-15 from the bootstrap artifact (millions of dollars).
const DAY = {
  record_date: '2026-10-15',
  record_fiscal_year: 2027,
  day_of_fiscal_year: 10,
  tga_total_deposits_today: 449175,
  public_debt_issues_today: 406472,
  total_deposits_today: 42703,
  tga_total_withdrawals_today: 400307,
  public_debt_redemptions_today: 358469,
  total_withdrawals_today: 41838,
  net_flow_today: -865,
  leading_flow: 41838,
} as DailyNetTransfer

describe('flowDirection', () => {
  it('reads positive net flow as an outflow', () => {
    expect(flowDirection(5889)).toBe('outflow')
    expect(flowDirection(-865)).toBe('inflow')
    expect(flowDirection(0)).toBe('balanced')
  })
})

describe('formulaSteps', () => {
  it('lays out the three subtractions with the day values', () => {
    const steps = formulaSteps(DAY)

    expect(steps.map((s) => s.values)).toEqual([
      [42703, 449175, 406472],
      [41838, 400307, 358469],
      [-865, 41838, 42703],
    ])
    for (const [result, left, right] of steps.map((s) => s.values)) {
      expect(result).toBe(left - right)
    }
  })
})
