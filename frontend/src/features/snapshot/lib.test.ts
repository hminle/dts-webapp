import { describe, expect, it } from 'vitest'
import type { WeeklySnapshot } from './api'
import { describeGapChange, snapshotHeading } from './lib'

describe('describeGapChange', () => {
  it('widens when the gap grows', () => {
    expect(describeGapChange(-89579, -112076)).toEqual({
      kind: 'widened',
      amount: 22497,
    })
  })

  it('narrows when the gap shrinks', () => {
    // Dec 11 → Dec 18, 2025: the newsletter's "an improvement of $36 bln".
    expect(describeGapChange(-136062, -100199)).toEqual({
      kind: 'narrowed',
      amount: 35863,
    })
  })

  it('flips when the sign changes', () => {
    expect(describeGapChange(10, -5)).toEqual({ kind: 'flipped', amount: 15 })
  })

  it('is null without both gaps', () => {
    expect(describeGapChange(null, -5)).toBeNull()
    expect(describeGapChange(-5, null)).toBeNull()
  })
})

describe('snapshotHeading', () => {
  const snapshot = (anchor: string, record: string) =>
    ({ anchor_date: anchor, record_date: record }) as WeeklySnapshot

  it('names the anchor day', () => {
    expect(snapshotHeading(snapshot('2025-12-04', '2025-12-04'))).toEqual({
      title: 'Thursday, Dec 4, 2025',
      holidayNote: null,
    })
  })

  it('notes a holiday that moved the statement', () => {
    expect(
      snapshotHeading(snapshot('2025-11-27', '2025-11-26')).holidayNote
    ).toBe(
      'No statement on Thu, Nov 27, 2025; using Wed, Nov 26, 2025, the closest earlier one.'
    )
  })
})
