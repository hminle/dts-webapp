import { ProsePage, ProseSection } from '@/components/prose-section'

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

export function MethodologyPage() {
  return (
    <ProsePage>
      <ProseSection title='Source'>
        <p>
          Every figure comes from the U.S. Treasury&apos;s{' '}
          <a
            className='text-foreground underline underline-offset-4'
            href='https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/'
            target='_blank'
            rel='noreferrer'
          >
            Daily Treasury Statement
          </a>{' '}
          (DTS), read through the Treasury Fiscal Data API. The DTS reports the
          cash that flowed into and out of the Treasury General Account, the
          government&apos;s main bank account, on each business day. The app
          keeps these nine DTS tables:
        </p>
        <ul>
          {TABLES.map((table) => (
            <li key={table}>{table}</li>
          ))}
        </ul>
        <p>
          Two tables, Federal Tax Deposits and Short-Term Cash Investments, are
          no longer published by the Treasury; they hold history only.
        </p>
      </ProseSection>

      <ProseSection title='Update schedule'>
        <p>
          The Treasury publishes each statement around 4 pm Eastern on the next
          business day. The app checks for new statements every weekday at 22:30
          UTC and is refreshed a few minutes later when there is one. The Data
          status page shows the latest statement date and when the data was last
          refreshed.
        </p>
      </ProseSection>

      <ProseSection title='Units'>
        <p>
          The Treasury reports amounts in <strong>millions of dollars</strong>.
          The app shows them rounded to millions, billions or trillions, so
          $1.25B means about $1,250 million.
        </p>
      </ProseSection>

      <ProseSection title='Net transfers'>
        <p>For each day, from the Deposits & Withdrawals table:</p>
        <ul>
          <li>
            <strong>Total deposits</strong>: the Treasury General Account&apos;s
            total deposits, excluding public debt cash issues (money raised by
            selling Treasury securities).
          </li>
          <li>
            <strong>Total withdrawals</strong>: its total withdrawals, excluding
            public debt cash redemptions (money paid to repay maturing
            securities).
          </li>
          <li>
            <strong>Net transfers</strong> = total withdrawals − total deposits.
            A positive number means the government spent more than it took in
            that day, before borrowing.
          </li>
        </ul>
        <p>
          The same formula is applied to the month-to-date and
          fiscal-year-to-date columns of the statement.
        </p>
      </ProseSection>

      <ProseSection title='Fiscal year'>
        <p>
          The U.S. federal fiscal year runs from October 1 to September 30 and
          is named after the year it ends in: fiscal year 2027 starts on October
          1, 2026. The <em>day of the fiscal year</em> counts business days with
          a statement: day 1 is the first statement on or after October 1, day 2
          the next one, and so on. Weekends and holidays are not counted.
        </p>
      </ProseSection>

      <ProseSection title='Comparison modes'>
        <p>
          Year-over-year pages line up the two fiscal years in one of two ways:
        </p>
        <ul>
          <li>
            <strong>Fiscal day</strong> (the default): day N of one year against
            day N of the other, so both sides cover the same number of business
            days.
          </li>
          <li>
            <strong>Calendar date</strong>: the same calendar date in each year,
            e.g. December 31 against December 31. Dates that have a statement in
            only one of the two years are left out.
          </li>
        </ul>
        <p>
          Weekly comparisons use each Friday&apos;s statement, or the closest
          earlier day with one when Friday was a holiday.
        </p>
      </ProseSection>

      <ProseSection title='Known limits'>
        <ul>
          <li>
            The app fetches each statement once. If the Treasury later revises a
            published figure, the app keeps the original until the data is
            rebuilt in full.
          </li>
          <li>
            Days whose statement lacks the totals above are skipped in net
            transfer figures.
          </li>
          <li>
            Category names follow the Treasury&apos;s own labels, which have
            changed over the years, so a category can appear in one fiscal year
            and not another.
          </li>
        </ul>
      </ProseSection>
    </ProsePage>
  )
}
