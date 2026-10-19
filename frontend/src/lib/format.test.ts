import { describe, expect, it } from 'vitest'
import {
  formatBillions,
  formatCurrency,
  formatDate,
  formatMillions,
  formatNumber,
  formatPercent,
  formatShortDate,
  formatSignedPercent,
  formatText,
  formatTreasuryValue,
} from './format'

describe('formatters', () => {
  it('formatCurrency', () => {
    expect(formatCurrency(0)).toBe('$0.00')
    expect(formatCurrency(-865)).toBe('-$865.00')
    expect(formatCurrency(1.5e12)).toBe('$1,500,000,000,000.00')
    expect(formatCurrency(5889.456)).toBe('$5,889.46')
    expect(formatCurrency(null)).toBe('N/A')
  })

  it('formatNumber', () => {
    expect(formatNumber(867348)).toBe('867,348')
    expect(formatNumber(undefined)).toBe('N/A')
  })

  it('formatTreasuryValue scales millions to T / B / M', () => {
    expect(formatTreasuryValue(0)).toBe('$0M')
    expect(formatTreasuryValue(750)).toBe('$750M')
    expect(formatTreasuryValue(-1_500)).toBe('-$1.50B')
    expect(formatTreasuryValue(-750)).toBe('-$750M')
    expect(formatTreasuryValue(1_500_000)).toBe('$1.50T')
    expect(formatTreasuryValue(2e12)).toBe('$2000000.00T')
  })

  it('formatBillions and formatMillions', () => {
    expect(formatBillions(95_010)).toBe('$95.01B')
    expect(formatBillions(-865)).toBe('-$0.86B')
    expect(formatMillions(2_500_000)).toBe('$2.50M')
    expect(formatMillions(0)).toBe('$0.00M')
  })

  it('percent formatters', () => {
    expect(formatPercent(3.1415)).toBe('3.14%')
    expect(formatSignedPercent(3.14)).toBe('+3.14%')
    expect(formatSignedPercent(-2.5)).toBe('-2.50%')
    expect(formatSignedPercent(0)).toBe('+0.00%')
  })

  it('reads a bare date as a calendar day, not UTC midnight', () => {
    // The reference showed "October 14, 2026" for this in U.S. time zones.
    expect(formatDate('2026-10-15')).toBe('October 15, 2026')
    expect(formatShortDate('2026-10-15')).toBe('Oct 15, 2026')
    expect(formatDate('')).toBe('N/A')
  })

  it('formatText hides the API\'s "null" strings', () => {
    expect(formatText('null')).toBe('—')
    expect(formatText(null)).toBe('—')
    expect(formatText('Taxes - Corporate Income')).toBe('Taxes - Corporate Income')
  })
})
