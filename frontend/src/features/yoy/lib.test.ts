import { describe, expect, it } from 'vitest'
import type {
  IrsRefunds,
  MajorSpending,
  TBillInterest,
  YoYCategoryComparison,
  YoYDailyDataPoint,
} from './api'
import {
  breakdownRows,
  categoryDiffSeries,
  comparisonRows,
  receiptCards,
  spendingCards,
  summarize,
} from './lib'

const point = (day: number, current: number, previous: number) =>
  ({
    day_of_fiscal_year: day,
    current_value: current,
    previous_value: previous,
    difference: current - previous,
    percent_change: previous
      ? ((current - previous) / Math.abs(previous)) * 100
      : null,
  }) as YoYDailyDataPoint

describe('summarize', () => {
  it('reports latest, average, max and min differences', () => {
    const s = summarize([
      point(1, 100, 90),
      point(2, 150, 170),
      point(3, 300, 250),
    ])!

    expect(s.latestDifference).toBe(50)
    expect(s.latestCurrentValue).toBe(300)
    expect(s.averageDifference).toBeCloseTo((10 - 20 + 50) / 3)
    expect(s.maxDifference).toBe(50)
    expect(s.minDifference).toBe(-20)
  })

  it('returns null for an empty series', () => {
    expect(summarize([])).toBeNull()
  })
})

describe('category cards', () => {
  const spending = {
    categories: [
      {
        name: 'Medicare',
        current_fytd: 50,
        previous_fytd: 60,
        yoy_change: -10,
        yoy_percent_change: -16.7,
        available_from: '2020-03-09',
        subcategories: [],
      },
    ],
  } as unknown as MajorSpending
  const tbill = {
    total_current_fytd: 8,
    total_previous_fytd: 5,
    total_yoy_change: 3,
    total_yoy_percent_change: 60,
    available_from: '2022-09-12',
    components: [
      {
        adj_type: 'Bills',
        name: 'Treasury Bills',
        current_fytd: 8,
        previous_fytd: 5,
        yoy_change: 3,
      },
    ],
  } as unknown as TBillInterest

  it('appends T-bill interest and IRS refunds after the major categories', () => {
    const cards = spendingCards(spending, tbill, undefined)

    expect(cards.map((c) => c.name)).toEqual(['Medicare', 'T-Bill Interest'])
    expect(cards.map((c) => c.accent)).toEqual(['decrease', 'increase'])
    expect(cards[1].categoryType).toBe('tbill')
  })

  it('works before every response has arrived', () => {
    expect(spendingCards(undefined, undefined, undefined)).toEqual([])
    expect(receiptCards(undefined)).toEqual([])
  })

  it('normalizes each breakdown into the same rows', () => {
    const [, tbillCard] = spendingCards(spending, tbill, undefined)
    expect(breakdownRows(tbillCard)).toEqual([
      {
        key: 'Bills',
        name: 'Treasury Bills',
        code: 'Bills',
        current: 8,
        previous: 5,
        change: 3,
      },
    ])

    const irs = {
      total_current_fytd: 2,
      total_previous_fytd: 3,
      total_yoy_change: -1,
      total_yoy_percent_change: null,
      components: [
        {
          tax_refund_type: 'IRS - EFT',
          name: 'Individual (EFT)',
          current_fytd: 2,
          previous_fytd: 3,
          yoy_change: -1,
        },
      ],
    } as unknown as IrsRefunds
    const irsCard = spendingCards(undefined, undefined, irs)[0]
    expect(irsCard.yoy_percent_change).toBeNull()
    expect(breakdownRows(irsCard)[0].code).toBe('IRS - EFT')
  })

  it('passes a null total through and keeps availableFrom', () => {
    const early = {
      categories: [
        {
          name: 'Social Security Benefits',
          current_fytd: 120,
          previous_fytd: null,
          yoy_change: null,
          yoy_percent_change: null,
          available_from: '2021-07-19',
          subcategories: [],
        },
      ],
    } as unknown as MajorSpending
    const [card] = spendingCards(early, undefined, undefined)
    expect(card.current_fytd).toBe(120)
    expect(card.previous_fytd).toBeNull()
    expect(card.yoy_change).toBeNull()
    expect(card.availableFrom).toBe('2021-07-19')
    expect(card.accent).toBe('increase')
  })

  it('drops breakdown rows that are zero in both years', () => {
    const medicaid = {
      categories: [
        {
          name: 'Medicaid',
          current_fytd: 40,
          previous_fytd: 30,
          yoy_change: 10,
          yoy_percent_change: 33.3,
          available_from: '2005-10-03',
          subcategories: [
            {
              category_name: 'HHS - Grants to States for Medicaid',
              current_fytd: 40,
              previous_fytd: 30,
              yoy_change: 10,
            },
            {
              category_name: 'Medicaid',
              current_fytd: 0,
              previous_fytd: 0,
              yoy_change: 0,
            },
          ],
        },
      ],
    } as unknown as MajorSpending
    const [card] = spendingCards(medicaid, undefined, undefined)
    expect(breakdownRows(card).map((r) => r.name)).toEqual([
      'HHS - Grants to States for Medicaid',
    ])
  })
})

const comparison = (
  current: number[][],
  previous: number[][]
): YoYCategoryComparison =>
  ({
    current_fiscal_year: 2026,
    previous_fiscal_year: 2025,
    comparison_mode: 'fiscal_day',
    current_year_data: [
      {
        category_description: 'Medicare',
        data_points: current.map(([d, v]) => ({
          day_of_fiscal_year: d,
          record_date: `2025-10-0${d}`,
          transaction_fytd_amt: v,
        })),
      },
    ],
    previous_year_data: [
      {
        category_description: 'Medicare',
        data_points: previous.map(([d, v]) => ({
          day_of_fiscal_year: d,
          record_date: `2024-10-0${d}`,
          transaction_fytd_amt: v,
        })),
      },
    ],
  }) as unknown as YoYCategoryComparison

describe('categoryDiffSeries', () => {
  it('pairs days by day number, keeping only days both years have', () => {
    // The previous year is missing day 2; day 3 must not pair with anything else.
    const series = categoryDiffSeries(
      comparison(
        [
          [1, 10],
          [2, 25],
          [3, 40],
        ],
        [
          [1, 8],
          [3, 30],
        ]
      )
    )

    expect(series).toEqual([
      { day: 1, Medicare: 2 },
      { day: 3, Medicare: 10 },
    ])
  })
})

describe('comparisonRows', () => {
  it('counts a day the previous year lacks as zero, with no percent change', () => {
    const rows = comparisonRows(
      comparison(
        [
          [1, 10],
          [2, 25],
        ],
        [[1, 8]]
      )
    )

    expect(rows[0]).toMatchObject({
      day: 1,
      previousFytd: 8,
      difference: 2,
      percentChange: 25,
    })
    expect(rows[1]).toMatchObject({
      day: 2,
      previousDate: null,
      previousFytd: 0,
      difference: 25,
      percentChange: null,
    })
  })
})
