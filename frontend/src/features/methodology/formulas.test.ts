import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { FORMULA_ORDER, FORMULAS } from './formulas'
import type { FormulaId } from './formulas'
import examples from './worked-examples.json'

const sum = (values: Record<string, number>) =>
  Object.values(values).reduce((s, v) => s + v, 0)

const pct = (current: number, previous: number) =>
  Math.round(((current - previous) / Math.abs(previous)) * 100 * 100) / 100

describe('formula registry', () => {
  it('orders every formula exactly once', () => {
    expect([...FORMULA_ORDER].sort()).toEqual(Object.keys(FORMULAS).sort())
    expect(new Set(FORMULA_ORDER).size).toBe(FORMULA_ORDER.length)
  })

  it.each(FORMULA_ORDER)('%s has a short summary and an expression', (id) => {
    const f = FORMULAS[id]
    expect(f.id).toBe(id)
    expect(f.summary.length).toBeGreaterThan(0)
    expect(f.summary.length).toBeLessThanOrEqual(160)
    expect(f.expression.length).toBeGreaterThan(0)
  })
})

describe('worked examples add up', () => {
  const nt = examples.net_transfers
  it.each(['today', 'fytd'] as const)('net transfers (%s)', (period) => {
    const i = nt.inputs[period]
    const o = nt.outputs[period]
    expect(i.tga_deposits - i.debt_issues).toBe(o.total_deposits)
    expect(i.tga_withdrawals - i.debt_redemptions).toBe(o.total_withdrawals)
    expect(o.total_withdrawals - o.total_deposits).toBe(o.net_transfers)
  })

  it('year over year', () => {
    const { yoy, yoy_negative_base: neg } = examples
    expect(yoy.current.value - yoy.previous.value).toBe(yoy.difference)
    expect(pct(yoy.current.value, yoy.previous.value)).toBe(yoy.percent_change)
    expect(neg.current - neg.previous).toBe(neg.difference)
    expect(pct(neg.current, neg.previous)).toBe(neg.percent_change)
  })

  it.each(['medicare', 'customs', 'tbill', 'social_security'] as const)(
    '%s',
    (key) => {
      const c = examples.categories[key]
      expect(sum(c.current)).toBe(c.current_total)
      expect(sum(c.previous)).toBe(c.previous_total)
      expect(c.current_total - c.previous_total).toBe(c.difference)
      expect(pct(c.current_total, c.previous_total)).toBe(c.percent_change)
    }
  )

  it('IRS refunds', () => {
    const r = examples.categories.irs_refunds
    expect(sum(r.table_v)).toBe(r.table_v_total)
  })
})

describe('category line items match the backend', () => {
  // Read as text so a rename on either side fails here rather than showing a
  // line item the backend no longer sums.
  // vitest runs from frontend/ (pnpm test); jsdom's URL can't read file: URLs.
  const backend = readFileSync(
    resolve(process.cwd(), '../backend/app/constants/categories.py'),
    'utf8'
  )
  const ids: FormulaId[] = [
    'major-spending',
    'major-receipts',
    'tbill-interest',
    'irs-refunds',
  ]
  it.each(ids)('%s', (id) => {
    const lines = FORMULAS[id].terms?.map((t) => t.meaning) ?? []
    expect(lines.length).toBeGreaterThan(0)
    for (const line of lines) expect(backend).toContain(`"${line}"`)
  })
})
