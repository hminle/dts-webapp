// Formatters ported from the reference app's lib/utils.ts. Treasury amounts
// arrive in MILLIONS of dollars unless a function says otherwise.

const DECIMAL_PLACES = 2

/**
 * A bare `YYYY-MM-DD` is parsed by `new Date()` as UTC midnight, which every
 * U.S. time zone renders as the previous day — every Treasury date would show a
 * day early. Read such strings as local calendar dates instead.
 */
function toDate(date: string | Date): Date {
  if (typeof date === 'string') {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date)
    if (match) return new Date(+match[1], +match[2] - 1, +match[3])
  }
  return new Date(date)
}

export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A'
  return new Intl.NumberFormat('en-US').format(value)
}

export function formatDate(date: string | Date): string {
  if (!date) return 'N/A'
  return toDate(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export function formatShortDate(date: string | Date): string {
  if (!date) return 'N/A'
  return toDate(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/** A wall-clock instant (an ISO timestamp with time), in the viewer's zone. */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

/**
 * Auto-scale a value (in millions) to the most readable unit: T / B / M.
 * Examples: 1_500_000 → "$1.50T", 1_500 → "$1.50B", 750 → "$750M"
 */
export function formatTreasuryValue(value: number): string {
  const absValue = Math.abs(value)
  if (absValue >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(DECIMAL_PLACES)}T`
  } else if (absValue >= 1_000) {
    return `$${(value / 1_000).toFixed(DECIMAL_PLACES)}B`
  }
  return `$${value.toFixed(0)}M`
}

/** A value in millions, as billions. Example: 95_010 → "$95.01B" */
export function formatBillions(value: number): string {
  return `$${(value / 1_000).toFixed(DECIMAL_PLACES)}B`
}

/** A value in raw units, as millions. Example: 2_500_000 → "$2.50M" */
export function formatMillions(value: number): string {
  return `$${(value / 1_000_000).toFixed(DECIMAL_PLACES)}M`
}

/** Example: 3.1415 → "3.14%" */
export function formatPercent(value: number): string {
  return `${value.toFixed(DECIMAL_PLACES)}%`
}

/** Example: 3.14 → "+3.14%", -2.5 → "-2.50%" */
export function formatSignedPercent(value: number): string {
  const prefix = value >= 0 ? '+' : ''
  return `${prefix}${value.toFixed(DECIMAL_PLACES)}%`
}

/**
 * A text field as shown in a table. The Treasury API sends missing text as the
 * string "null" (aggregate rows have no category), so treat it as absent.
 */
export function formatText(value: string | null | undefined): string {
  return value && value !== 'null' ? value : '—'
}
