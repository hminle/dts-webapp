import { describe, expect, it } from 'vitest'
import { currentFiscalYear } from './fiscal'

describe('currentFiscalYear', () => {
  it('keeps September in the same fiscal year', () => {
    expect(currentFiscalYear(new Date(2026, 8, 30))).toBe(2026)
  })

  it('moves October into the next fiscal year', () => {
    expect(currentFiscalYear(new Date(2026, 9, 1))).toBe(2027)
  })
})
