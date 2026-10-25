import type { WeeklySnapshot } from './api'

export type GapChange = {
  kind: 'widened' | 'narrowed' | 'flipped' | 'unchanged'
  /** |current − previous| */
  amount: number
}

/** How the year-over-year gap moved since last week. */
export function describeGapChange(
  previousGap: number | null,
  currentGap: number | null
): GapChange | null {
  if (previousGap === null || currentGap === null) return null
  const amount = Math.abs(currentGap - previousGap)
  const signsDiffer =
    previousGap !== 0 && currentGap !== 0 && previousGap > 0 !== currentGap > 0
  if (signsDiffer) return { kind: 'flipped', amount }
  if (Math.abs(currentGap) > Math.abs(previousGap))
    return { kind: 'widened', amount }
  if (Math.abs(currentGap) < Math.abs(previousGap))
    return { kind: 'narrowed', amount }
  return { kind: 'unchanged', amount }
}

const weekday = (iso: string, style: 'long' | 'short') => {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-US', {
    weekday: style,
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

/** "Thursday, Dec 4, 2025", and a note when a holiday moved the statement. */
export function snapshotHeading(s: WeeklySnapshot): {
  title: string
  holidayNote: string | null
} {
  return {
    title: weekday(s.anchor_date, 'long'),
    holidayNote:
      s.record_date === s.anchor_date
        ? null
        : `No statement on ${weekday(s.anchor_date, 'short')}; using ${weekday(s.record_date, 'short')}, the closest earlier one.`,
  }
}

/** "Wed, Nov 26, 2025": the short form used in notes. */
export const shortWeekday = (iso: string) => weekday(iso, 'short')
