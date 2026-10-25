import { useState } from 'react'
import {
  AnchorWeekdaySelect,
  type AnchorWeekday,
} from '@/components/anchor-weekday-select'
import { QueryState } from '@/components/query-state'
import { StatCard } from '@/components/stat-card'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { changeClass, changeText } from '@/features/yoy/components/accent'
import { formatBillions, formatTreasuryValue } from '@/lib/format'
import { useWeeklySnapshot } from './api'
import type { WeeklySnapshot } from './api'
import { FigureCard } from './components/figure-card'
import { SnapshotHeader } from './components/snapshot-header'
import { describeGapChange, shortWeekday } from './lib'

function gapNote(s: WeeklySnapshot): string {
  if (s.net_transfers_gap_change === null || !s.previous_week_date)
    return s.gap_change_unavailable_reason ?? ''
  const change = describeGapChange(
    s.previous_week_net_transfers_gap,
    s.net_transfers_fytd.change
  )
  if (!change) return s.gap_change_unavailable_reason ?? ''
  const since = `since ${shortWeekday(s.previous_week_date)}`
  const amount = formatBillions(change.amount)
  switch (change.kind) {
    case 'widened':
      return `Widened by ${amount} ${since}`
    case 'narrowed':
      return `Narrowed by ${amount} ${since}`
    case 'flipped':
      return `Flipped sign ${since}, a move of ${amount}`
    case 'unchanged':
      return `Unchanged ${since}`
  }
}

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className='flex flex-col gap-3'>
      <h2 className='text-sm font-medium text-muted-foreground'>{title}</h2>
      {children}
    </section>
  )
}

export function SnapshotPage() {
  const [anchor, setAnchor] = useState<AnchorWeekday>('thursday')
  const [asOf, setAsOf] = useState('')
  const snapshot = useWeeklySnapshot(anchor, asOf || null)

  return (
    <div className='flex flex-col gap-6'>
      <Card>
        <CardContent className='flex flex-wrap items-end gap-6'>
          <AnchorWeekdaySelect
            id='anchor-weekday'
            value={anchor}
            onChange={setAnchor}
          />
          <div className='flex flex-col gap-2'>
            <Label htmlFor='as-of'>As of</Label>
            <div className='flex gap-2'>
              <Input
                id='as-of'
                type='date'
                className='w-44'
                value={asOf}
                onChange={(e) => setAsOf(e.target.value)}
              />
              <Button
                variant='outline'
                disabled={!asOf}
                onClick={() => setAsOf('')}
              >
                Latest
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <QueryState query={snapshot} skeletonClassName='h-96'>
        {(s) => (
          <>
            <SnapshotHeader snapshot={s} />

            <Section title='This month so far'>
              <div className='grid gap-4 sm:grid-cols-2'>
                <StatCard
                  title='Withdrawals, month to date'
                  hint='today-mtd-fytd'
                  value={formatTreasuryValue(s.withdrawals_mtd)}
                />
                <StatCard
                  title='Net transfers, month to date'
                  hint='net-transfers'
                  value={formatTreasuryValue(s.net_transfers_mtd)}
                />
              </div>
            </Section>

            <Section title='Fiscal year to date, against a year ago'>
              <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
                <FigureCard
                  title='Total withdrawals'
                  hint='total-withdrawals'
                  figure={s.withdrawals_fytd}
                  previousFiscalYear={s.previous_fiscal_year}
                />
                <FigureCard
                  title='Total deposits'
                  hint='total-deposits'
                  figure={s.deposits_fytd}
                  previousFiscalYear={s.previous_fiscal_year}
                />
                <FigureCard
                  title='Net transfers'
                  hint='net-transfers'
                  figure={s.net_transfers_fytd}
                  previousFiscalYear={s.previous_fiscal_year}
                />
                <FigureCard
                  title='Withholding tax'
                  hint='major-receipts'
                  figure={s.withholding_fytd}
                  previousFiscalYear={s.previous_fiscal_year}
                />
              </div>
            </Section>

            <Section title='Net transfers gap'>
              <div className='grid gap-4 sm:grid-cols-2'>
                <StatCard
                  title='Gap vs a year ago'
                  hint='weekly-snapshot'
                  value={changeText(s.net_transfers_fytd.change)}
                  valueClassName={
                    s.net_transfers_fytd.change === null
                      ? undefined
                      : changeClass(s.net_transfers_fytd.change)
                  }
                  note={gapNote(s)}
                />
              </div>
            </Section>
          </>
        )}
      </QueryState>
    </div>
  )
}
