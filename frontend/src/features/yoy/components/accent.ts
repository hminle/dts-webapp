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
