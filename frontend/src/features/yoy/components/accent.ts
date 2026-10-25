import { formatBillions } from '@/lib/format'
import type { CategoryAccent } from '../lib'

/** Card edge and chart line per accent, from theme tokens. */
export const ACCENT: Record<CategoryAccent, { border: string; line: string }> =
  {
    increase: { border: 'border-l-chart-1', line: 'var(--chart-1)' },
    decrease: { border: 'border-l-warning', line: 'var(--warning)' },
    receipt: { border: 'border-l-success', line: 'var(--success)' },
  }

export const changeClass = (value: number) =>
  value >= 0 ? 'text-success' : 'text-destructive'

export const signedPrefix = (value: number) => (value >= 0 ? '+' : '')

/** A total that may be missing before a category's coverage date. */
export const totalText = (value: number | null) =>
  value === null ? '—' : formatBillions(value)

/** A signed change, or a dash when either total is missing. */
export const changeText = (value: number | null) =>
  value === null ? '—' : `${signedPrefix(value)}${formatBillions(value)}`
