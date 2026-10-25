import type { CashBalancePoint } from './api'

export type LatestChange = {
  latest: CashBalancePoint
  previous: CashBalancePoint
  change: number
}

/**
 * The latest balance against the one `back` statements earlier (5 is about
 * a week); null when there are not enough points.
 */
export function latestChange(
  points: CashBalancePoint[],
  back = 5
): LatestChange | null {
  if (points.length <= back) return null
  const latest = points[points.length - 1]
  const previous = points[points.length - 1 - back]
  return {
    latest,
    previous,
    change: latest.closing_balance - previous.closing_balance,
  }
}
