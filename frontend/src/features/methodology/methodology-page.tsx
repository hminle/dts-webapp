import { useEffect } from 'react'
import { ProsePage, ProseSection } from '@/components/prose-section'
import {
  formatNumber,
  formatShortDate,
  formatSignedPercent,
  formatTreasuryValue,
} from '@/lib/format'
import { ArithmeticTable } from './components/arithmetic-table'
import { FormulaBlock } from './components/formula-block'
import { MethodologyToc } from './components/methodology-toc'
import type { Chapter } from './components/methodology-toc'
import examples from './worked-examples.json'

// Every figure on this page comes from worked-examples.json, which
// backend/tests/test_formula_examples.py runs through the real formula code.
const NT = examples.net_transfers
const YOY = examples.yoy
const NEG = examples.yoy_negative_base
const CATS = examples.categories

// Display names from backend/app/constants/endpoints.py (ENDPOINTS).
const TABLES = [
  'Operating Cash Balance',
  'Deposits & Withdrawals',
  'Public Debt Transactions',
  'Public Debt Adjustments',
  'Debt Subject to Limit',
  'Inter-Agency Tax Transfers',
  'Income Tax Refunds',
  'Federal Tax Deposits',
  'Short-Term Cash Investments',
]

// FY2027's first statements: October 12, 2026 was Columbus Day.
const FY2027_DAYS = [
  '2026-10-01',
  '2026-10-02',
  '2026-10-05',
  '2026-10-06',
  '2026-10-07',
  '2026-10-08',
  '2026-10-09',
  '2026-10-13',
  '2026-10-14',
  '2026-10-15',
  '2026-10-16',
  '2026-10-19',
]

const CHAPTERS: Chapter[] = [
  { id: 'start-here', title: 'Start here' },
  { id: 'reading-a-statement', title: 'Reading a statement' },
  {
    id: 'deposits-and-withdrawals',
    title: 'Deposits, withdrawals and borrowing',
  },
  { id: 'surplus-or-deficit', title: 'Net transfers' },
  { id: 'year-over-year', title: 'Comparing with a year ago' },
  { id: 'lining-up-two-years', title: 'Lining up two years' },
  { id: 'spending-categories', title: 'Major spending categories' },
  { id: 'receipt-categories', title: 'Major receipt categories' },
  { id: 't-bill-discount', title: 'T-Bill interest' },
  { id: 'tax-refunds', title: 'IRS tax refunds' },
  { id: 'any-line-item', title: 'Category comparison' },
  { id: 'friday-snapshots', title: 'Weekly comparison' },
  { id: 'known-limits', title: 'Known limits' },
  { id: 'glossary', title: 'Glossary' },
  { id: 'source-and-schedule', title: 'Source and update schedule' },
]

const GLOSSARY: [string, string][] = [
  [
    'DTS',
    'Daily Treasury Statement: the Treasury’s report of each business day’s cash.',
  ],
  [
    'TGA',
    'Treasury General Account: the government’s operating account at the Federal Reserve.',
  ],
  [
    'FY',
    'Fiscal year: October 1 to September 30, named for the year it ends in.',
  ],
  ['FYTD', 'Fiscal year to date: from October 1 through the statement date.'],
  [
    'MTD',
    'Month to date: from the 1st of the month through the statement date.',
  ],
  [
    'YoY',
    'Year over year: compared with the same point of the previous fiscal year.',
  ],
  [
    'EFT',
    'Electronic funds transfer: a payment made directly to a bank account.',
  ],
  ['SSA', 'Social Security Administration.'],
  [
    'HHS',
    'Department of Health and Human Services, which pays Medicare and Medicaid.',
  ],
  ['IRS', 'Internal Revenue Service.'],
  [
    'DHS',
    'Department of Homeland Security, whose Customs and Border Protection collects tariffs.',
  ],
  [
    'Table II',
    'Deposits and Withdrawals of Operating Cash: every line item of cash in and out.',
  ],
  [
    'Table IIIB',
    'Adjustment of Public Debt Transactions to Cash Basis: where borrowing and bill discounts are reconciled.',
  ],
  ['Table V', 'Income Tax Refunds Issued: refunds by type and payment method.'],
]

/** A value in millions as prose ("$N million"), with a true minus sign. */
function millions(value: number): string {
  return `${value < 0 ? '−' : ''}$${formatNumber(Math.abs(value))} million`
}

/** "Oct 3, Oct 8 and Oct 15": short dates without the year. */
function dayList(dates: string[]): string {
  const days = dates.map((d) => formatShortDate(d).replace(/, \d{4}$/, ''))
  return days.length < 2
    ? days.join('')
    : `${days.slice(0, -1).join(', ')} and ${days[days.length - 1]}`
}

function percent(value: number): string {
  return formatSignedPercent(value).replace('-', '−')
}

function Strong({ children }: { children: React.ReactNode }) {
  return <strong className='font-medium text-foreground'>{children}</strong>
}

const CUR_COL = `FY2027 · ${formatShortDate(CATS.current_date)}`
const PREV_COL = `FY2026 · ${formatShortDate(CATS.previous_date)}`

/** Rows for a category example: each line item, the total, the change. */
function categoryRows(ex: {
  current: Record<string, number>
  previous: Record<string, number>
  current_total: number
  previous_total: number
  difference: number
  percent_change: number
}) {
  const names = [
    ...new Set([...Object.keys(ex.current), ...Object.keys(ex.previous)]),
  ]
  return [
    ...names.map((name, i) => ({
      label: name,
      op: i > 0 ? ('+' as const) : undefined,
      values: [ex.current[name] ?? '—', ex.previous[name] ?? '—'],
    })),
    {
      label: 'Category FYTD',
      op: '=' as const,
      values: [ex.current_total, ex.previous_total],
      result: true,
    },
  ]
}

function changeSentence(ex: { difference: number; percent_change: number }) {
  return (
    <p>
      Difference: <Strong>{millions(ex.difference)}</Strong>, a change of{' '}
      <Strong>{percent(ex.percent_change)}</Strong>.
    </p>
  )
}

export function MethodologyPage() {
  // A link like /methodology#tbill-interest is scrolled to while the page is
  // still settling: web fonts and tables reflow the text above and the heading
  // drifts away. Hold it in place while the page resizes, for up to 2 s or
  // until the reader scrolls.
  useEffect(() => {
    const id = decodeURIComponent(window.location.hash.slice(1))
    const target = id ? document.getElementById(id) : null
    if (!target) return
    const observer = new ResizeObserver(() =>
      target.scrollIntoView({ behavior: 'instant' })
    )
    observer.observe(document.body)
    const stop = () => observer.disconnect()
    const timer = window.setTimeout(stop, 2000)
    const events = ['wheel', 'pointerdown', 'keydown', 'hashchange'] as const
    events.forEach((e) => window.addEventListener(e, stop, { once: true }))
    return () => {
      stop()
      window.clearTimeout(timer)
      events.forEach((e) => window.removeEventListener(e, stop))
    }
  }, [])

  const today = NT.outputs.today
  const fytd = NT.outputs.fytd
  const ss = CATS.social_security
  const naiveNegPct = ((NEG.current - NEG.previous) / NEG.previous) * 100

  return (
    <div className='flex flex-col gap-4 lg:grid lg:grid-cols-[minmax(0,1fr)_15rem] lg:items-start lg:gap-8'>
      <MethodologyToc chapters={CHAPTERS} className='lg:order-last' />
      <ProsePage>
        <ProseSection id='start-here' title='1. Start here'>
          <p>
            Every business day the U.S. Treasury publishes the{' '}
            <Strong>Daily Treasury Statement</Strong> (DTS): a report of the
            cash that moved into and out of the{' '}
            <Strong>Treasury General Account</Strong> (TGA), the government’s
            operating account at the Federal Reserve. Taxes, fees and money
            borrowed flow in; benefits, salaries, contracts, interest and debt
            repayments flow out.
          </p>
          <p>
            This app reads those statements and turns them into a few figures:
            how much more the government spent than it collected on a day or
            over the year so far, how that compares with a year earlier, and
            where the money goes. This page explains every formula behind those
            figures, with a real example from the statement of{' '}
            {formatShortDate(NT.date)}.
          </p>
          <p>
            The Treasury reports amounts in <Strong>millions of dollars</Strong>
            . The app rounds them to millions, billions or trillions for
            display: {millions(today.total_deposits)} appears as{' '}
            {formatTreasuryValue(today.total_deposits)}. The examples on this
            page stay in millions so you can check the arithmetic exactly.
          </p>
        </ProseSection>

        <ProseSection id='reading-a-statement' title='2. Reading a statement'>
          <p>
            Each line of a statement has three amounts. Comparing figures only
            makes sense between the same columns.
          </p>
          <FormulaBlock id='today-mtd-fytd' />
          <FormulaBlock
            id='fiscal-year'
            example={
              <ArithmeticTable
                columns={['FY2027']}
                rows={[
                  { label: 'Q1', values: ['Oct–Dec 2026'] },
                  { label: 'Q2', values: ['Jan–Mar 2027'] },
                  { label: 'Q3', values: ['Apr–Jun 2027'] },
                  { label: 'Q4', values: ['Jul–Sep 2027'] },
                ]}
              />
            }
          />
          <FormulaBlock
            id='day-of-fiscal-year'
            example={
              <figure className='flex flex-col gap-2'>
                <ol className='flex flex-wrap gap-2'>
                  {FY2027_DAYS.map((day, i) => (
                    <li
                      key={day}
                      className='flex flex-col rounded-md border px-2 py-1 text-xs'
                    >
                      <span className='font-medium text-foreground'>
                        Day {i + 1}
                      </span>
                      {dayList([day])}
                    </li>
                  ))}
                </ol>
                <figcaption className='text-xs'>
                  FY2027 starts on Thursday, October 1, 2026. Weekends and
                  Columbus Day (October 12) have no statement, so day{' '}
                  {NT.day_of_fiscal_year} is {formatShortDate(NT.date)}.
                </figcaption>
              </figure>
            }
          />
        </ProseSection>

        <ProseSection
          id='deposits-and-withdrawals'
          title='3. Deposits, withdrawals and borrowing'
        >
          <p>
            The TGA’s totals mix two kinds of cash. One is the government’s
            business: taxes in, programs paid out. The other is managing its
            debt: selling new Treasury securities brings cash in, repaying
            maturing ones sends cash out. The debt flows are large: on{' '}
            {formatShortDate(NT.date)} the year’s debt sales so far were{' '}
            {millions(NT.inputs.fytd.debt_issues)} of the{' '}
            {millions(NT.inputs.fytd.tga_deposits)} deposited. Left in, they
            would hide the picture of taxes against spending.
          </p>
          <div className='grid gap-3 sm:grid-cols-2'>
            {[
              {
                title: 'Cash in (deposits)',
                kept: 'Taxes, customs duties, fees, agency receipts',
                removed: 'New borrowing: public debt cash issues',
              },
              {
                title: 'Cash out (withdrawals)',
                kept: 'Benefits, salaries, grants, contracts, interest',
                removed: 'Repaying debt: public debt cash redemptions',
              },
            ].map((side) => (
              <div
                key={side.title}
                className='flex flex-col gap-2 rounded-lg border p-3'
              >
                <p className='font-medium text-foreground'>{side.title}</p>
                <p>Kept: {side.kept}</p>
                <p className='line-through decoration-muted-foreground/60'>
                  {side.removed}
                </p>
              </div>
            ))}
          </div>
          <FormulaBlock id='total-deposits' />
          <FormulaBlock
            id='total-withdrawals'
            example={
              <ArithmeticTable
                columns={['Today', 'FYTD']}
                caption={`${formatShortDate(NT.date)}, FY${NT.fiscal_year} day ${NT.day_of_fiscal_year}. Millions of dollars.`}
                rows={[
                  {
                    label: 'TGA total deposits',
                    values: [
                      NT.inputs.today.tga_deposits,
                      NT.inputs.fytd.tga_deposits,
                    ],
                  },
                  {
                    label: 'Public debt cash issues',
                    op: '−',
                    values: [
                      NT.inputs.today.debt_issues,
                      NT.inputs.fytd.debt_issues,
                    ],
                  },
                  {
                    label: 'Total deposits',
                    op: '=',
                    values: [today.total_deposits, fytd.total_deposits],
                    result: true,
                  },
                  {
                    label: 'TGA total withdrawals',
                    values: [
                      NT.inputs.today.tga_withdrawals,
                      NT.inputs.fytd.tga_withdrawals,
                    ],
                  },
                  {
                    label: 'Public debt cash redemptions',
                    op: '−',
                    values: [
                      NT.inputs.today.debt_redemptions,
                      NT.inputs.fytd.debt_redemptions,
                    ],
                  },
                  {
                    label: 'Total withdrawals',
                    op: '=',
                    values: [today.total_withdrawals, fytd.total_withdrawals],
                    result: true,
                  },
                ]}
              />
            }
          />
          <p>
            Some older statements lack the TGA total rows. For those days the
            app adds up the individual deposit and withdrawal lines itself, then
            removes borrowing the same way.
          </p>
        </ProseSection>

        <ProseSection id='surplus-or-deficit' title='4. Net transfers'>
          <p>
            With borrowing removed from both sides, the difference between them
            shows whether the government’s own business took cash in or sent it
            out.
          </p>
          <FormulaBlock
            id='net-transfers'
            example={
              <ArithmeticTable
                columns={['Today', 'FYTD']}
                caption={`${formatShortDate(NT.date)}. Millions of dollars.`}
                rows={[
                  {
                    label: 'Total withdrawals',
                    values: [today.total_withdrawals, fytd.total_withdrawals],
                  },
                  {
                    label: 'Total deposits',
                    op: '−',
                    values: [today.total_deposits, fytd.total_deposits],
                  },
                  {
                    label: 'Net transfers',
                    op: '=',
                    values: [today.net_transfers, fytd.net_transfers],
                    result: true,
                  },
                ]}
              />
            }
          />
          <p>
            On {formatShortDate(NT.date)} net transfers were{' '}
            <Strong>{millions(today.net_transfers)}</Strong>: a surplus day,
            with more coming in than going out. Yet the fiscal year so far stood
            at <Strong>{millions(fytd.net_transfers)}</Strong>, a deficit. Both
            are true: tax receipts arrive in large batches on a few days, while
            spending is spread across every day.
          </p>
          <FormulaBlock id='leading-flow' />
        </ProseSection>

        <ProseSection id='year-over-year' title='5. Comparing with a year ago'>
          <p>
            A figure alone says little; the same figure a year earlier gives it
            scale. Year-over-year pages compare a fiscal year with the previous
            one at the same point.
          </p>
          <FormulaBlock
            id='yoy-difference'
            example={
              <ArithmeticTable
                columns={['Net transfers FYTD']}
                caption={`Day ${YOY.day_of_fiscal_year} of each fiscal year. Millions of dollars.`}
                rows={[
                  {
                    label: `FY${YOY.current.fiscal_year} · ${formatShortDate(YOY.current.date)}`,
                    values: [YOY.current.value],
                  },
                  {
                    label: `FY${YOY.previous.fiscal_year} · ${formatShortDate(YOY.previous.date)}`,
                    op: '−',
                    values: [YOY.previous.value],
                  },
                  {
                    label: 'Difference',
                    op: '=',
                    values: [YOY.difference],
                    result: true,
                  },
                ]}
              />
            }
          />
          <FormulaBlock
            id='yoy-percent'
            example={
              <div className='flex flex-col gap-2'>
                <p>
                  {millions(YOY.difference)} ÷ {millions(YOY.previous.value)} ×
                  100 = <Strong>{percent(YOY.percent_change)}</Strong>: the
                  deficit so far is that much larger than a year earlier.
                </p>
                <p>
                  When last year was negative, the absolute value matters. Going
                  from {NEG.previous} to {NEG.current} is a change of{' '}
                  {NEG.difference}; divided by |{NEG.previous}| that is{' '}
                  <Strong>{percent(NEG.percent_change)}</Strong>. Dividing by{' '}
                  {NEG.previous} itself would give {percent(naiveNegPct)}, which
                  reads as a decline.
                </p>
              </div>
            }
          />
          <FormulaBlock id='yoy-summary' />
        </ProseSection>

        <ProseSection id='lining-up-two-years' title='6. Lining up two years'>
          <p>
            “The same point last year” can mean two things, and each answers a
            different question.
          </p>
          <FormulaBlock
            id='comparison-modes'
            example={
              <ArithmeticTable
                columns={['Fiscal day', 'Calendar date']}
                caption={`Partner of ${formatShortDate(YOY.current.date)} (FY2027 day ${YOY.day_of_fiscal_year}) in each mode.`}
                rows={[
                  {
                    label: 'FY2027',
                    values: [
                      formatShortDate(YOY.current.date),
                      formatShortDate(YOY.current.date),
                    ],
                  },
                  {
                    label: 'FY2026 partner',
                    values: [
                      `${formatShortDate(YOY.previous.date)} (day ${YOY.day_of_fiscal_year})`,
                      'Oct 19, 2025 (a Sunday)',
                    ],
                  },
                ]}
              />
            }
          />
          <p>
            In calendar-date mode the partner date often has no statement, as
            here. Each part of the app handles that in its own way:
          </p>
          <ul>
            <li>
              <Strong>Year-over-year charts</Strong> (net transfers,
              withdrawals, deposits) leave the date out and show only dates that
              have a statement in both years.
            </li>
            <li>
              <Strong>Major category cards</Strong> use the latest statement
              before the missing date: {formatShortDate(CATS.previous_date)}.
            </li>
            <li>
              <Strong>A category’s daily chart</Strong> (opened from its card)
              keeps the date and counts last year as 0, with no percent.
            </li>
          </ul>
          <p>
            Use <Strong>fiscal day</Strong> to compare the pace of the year:
            both sides cover the same number of business days. Use{' '}
            <Strong>calendar date</Strong> around fixed deadlines, such as the
            April 15 tax date, which fall on the same date but a different day
            number each year.
          </p>
        </ProseSection>

        <ProseSection
          id='spending-categories'
          title='7. Major spending categories'
        >
          <p>
            The statement lists hundreds of withdrawal lines. The app groups the
            largest programs into four categories, each a sum of exact Treasury
            line items.
          </p>
          <FormulaBlock
            id='major-spending'
            termLabels={['Category', 'Treasury line item']}
            example={
              <div className='flex flex-col gap-2'>
                <ArithmeticTable
                  columns={[CUR_COL, PREV_COL]}
                  caption='Medicare, fiscal year to date. Millions of dollars.'
                  rows={categoryRows(CATS.medicare)}
                />
                {changeSentence(CATS.medicare)}
              </div>
            }
          />
          <p>Ten more spending groups are shown below the major ones:</p>
          <FormulaBlock
            id='other-spending'
            termLabels={['Category', 'Treasury line item']}
          />
        </ProseSection>

        <ProseSection
          id='receipt-categories'
          title='8. Major receipt categories'
        >
          <p>
            Two receipt categories track the payroll taxes withheld from
            paychecks and the duties collected on imports.
          </p>
          <FormulaBlock
            id='major-receipts'
            termLabels={['Category', 'Treasury line item']}
            example={
              <div className='flex flex-col gap-2'>
                <ArithmeticTable
                  columns={[CUR_COL, PREV_COL]}
                  caption='Customs & Duties, fiscal year to date. Each year uses the name in force at the time. Millions of dollars.'
                  rows={categoryRows(CATS.customs)}
                />
                {changeSentence(CATS.customs)}
              </div>
            }
          />
          <p>
            The old name, “DHS - Customs and Certain Excise Taxes”, was last
            used on {formatShortDate('2025-11-07')}; the new one, “DHS - Customs
            Duties, Taxes, and Fees”, starts on {formatShortDate('2025-11-10')}.
          </p>
          <p>Four more receipt groups are shown below the major ones:</p>
          <FormulaBlock
            id='other-receipts'
            termLabels={['Category', 'Treasury line item']}
          />
        </ProseSection>

        <ProseSection id='t-bill-discount' title='9. T-Bill interest'>
          <p>
            Treasury bills pay no interest checks. They are sold below their
            face value and repaid at face value; the gap is the interest. That
            gap never leaves the TGA as cash, so it is not in the withdrawals.
            The statement records it as an adjustment to the debt figures.
          </p>
          <FormulaBlock
            id='tbill-interest'
            termLabels={['Discount on', 'Adjustment line']}
            example={
              <div className='flex flex-col gap-2'>
                <ArithmeticTable
                  columns={[CUR_COL, PREV_COL]}
                  caption='Fiscal year to date. Millions of dollars.'
                  rows={categoryRows(CATS.tbill)}
                />
                {changeSentence(CATS.tbill)}
              </div>
            }
          />
        </ProseSection>

        <ProseSection id='tax-refunds' title='10. IRS tax refunds'>
          <FormulaBlock
            id='irs-refunds'
            termLabels={['Refund', 'Table V line']}
            example={
              <ArithmeticTable
                columns={[CUR_COL]}
                caption='Fiscal year to date. Millions of dollars.'
                rows={[
                  ...Object.entries(CATS.irs_refunds.table_v).map(
                    ([name, v], i) => ({
                      label: name,
                      op: i > 0 ? ('+' as const) : undefined,
                      values: [v],
                    })
                  ),
                  {
                    label: 'IRS refunds FYTD',
                    op: '=' as const,
                    values: [CATS.irs_refunds.table_v_total],
                    result: true,
                  },
                ]}
              />
            }
          />
          <p>
            Table II also lists refunds, but only the two EFT lines. Added up
            there, refunds would be{' '}
            {millions(CATS.irs_refunds.table_ii_eft_only)} instead of{' '}
            {millions(CATS.irs_refunds.table_v_total)}: every refund paid by
            check would be missing.
          </p>
        </ProseSection>

        <ProseSection id='any-line-item' title='11. Category comparison'>
          <p>
            The category comparison page lets you pick any line item from the
            Deposits and Withdrawals table, not only the major categories, and
            follow its fiscal-year-to-date amount day by day in two fiscal
            years.
          </p>
          <FormulaBlock id='category-comparison' />
        </ProseSection>

        <ProseSection id='friday-snapshots' title='12. Weekly comparison'>
          <p>
            Daily figures are noisy. The weekly page takes one reading per week,
            on Friday, and compares the two years week by week.
          </p>
          <FormulaBlock id='weekly-comparison' />
          <p>
            In FY2027, week 1 is {formatShortDate('2026-10-02')}. When a Friday
            is a holiday, such as Juneteenth on {formatShortDate('2026-06-19')},
            that week uses Thursday’s statement. A week with no statement within
            5 days of its Friday is left out.
          </p>
        </ProseSection>

        <ProseSection id='known-limits' title='13. Known limits'>
          <ul>
            <li>
              The app fetches each statement once. If the Treasury later revises
              a published figure, the app keeps the original until the data is
              rebuilt in full.
            </li>
            <li>
              Days whose statement lacks the totals above are skipped in net
              transfer figures.
            </li>
            <li>
              The Treasury has renamed and reorganized its lines over the
              years. Each category is compared only from the date its lines
              took their current shape:
              <FormulaBlock id='category-coverage' />
            </li>
            <li>
              Early in a fiscal year, payment calendars move the comparisons.
              Social Security pays large batches of benefits on the 3rd of the
              month and on its second, third and fourth Wednesdays. By day{' '}
              {NT.day_of_fiscal_year}, FY2027 had large payment days on{' '}
              {dayList(ss.benefit_payment_days.current)}; FY2026 had them on{' '}
              {dayList(ss.benefit_payment_days.previous)}. Social Security FYTD
              was {millions(ss.current_total)} against{' '}
              {millions(ss.previous_total)}, a change of{' '}
              {percent(ss.percent_change)} that is mostly timing, not policy.
            </li>
          </ul>
        </ProseSection>

        <ProseSection id='glossary' title='14. Glossary'>
          <dl className='grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-2'>
            {GLOSSARY.map(([term, meaning]) => (
              <div key={term} className='contents'>
                <dt className='font-medium text-foreground'>{term}</dt>
                <dd>{meaning}</dd>
              </div>
            ))}
          </dl>
        </ProseSection>

        <ProseSection
          id='source-and-schedule'
          title='15. Source and update schedule'
        >
          <p>
            Every figure comes from the U.S. Treasury&apos;s{' '}
            <a
              className='text-foreground underline underline-offset-4'
              href='https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/'
              target='_blank'
              rel='noreferrer'
            >
              Daily Treasury Statement
            </a>
            , read through the Treasury Fiscal Data API. The app keeps these
            nine DTS tables:
          </p>
          <ul>
            {TABLES.map((table) => (
              <li key={table}>{table}</li>
            ))}
          </ul>
          <p>
            Two tables, Federal Tax Deposits and Short-Term Cash Investments,
            are no longer published by the Treasury; they hold history only.
          </p>
          <p>
            The Treasury publishes each statement around 4 pm Eastern on the
            next business day. The app checks for new statements every weekday
            at 22:30 UTC and is refreshed a few minutes later when there is one.
            The Data status page shows the latest statement date and when the
            data was last refreshed.
          </p>
        </ProseSection>
      </ProsePage>
    </div>
  )
}
