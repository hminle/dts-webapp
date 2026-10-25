import { useState } from 'react'
import { QueryState } from '@/components/query-state'
import { StatCard } from '@/components/stat-card'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import {
  formatBillions,
  formatShortDate,
  formatTreasuryValue,
} from '@/lib/format'
import { useRollingAverage } from './api'
import { RollingChart } from './components/rolling-chart'
import { lastWithValue, rangeStart } from './lib'

const RANGES = [
  { label: '6 months', days: 183 },
  { label: '1 year', days: 365 },
  { label: '3 years', days: 1095 },
  { label: '5 years', days: 1826 },
] as const

const asOf = (date: string | undefined) =>
  date ? `As of ${formatShortDate(date)}` : undefined

export function LeadingFlowsPage() {
  const [days, setDays] = useState(365)
  const startDate = rangeStart(days, new Date())
  const withdrawals = useRollingAverage('total_withdrawals', startDate)
  const unemployment = useRollingAverage('unemployment_benefits', startDate)

  return (
    <div className='flex flex-col gap-6'>
      <Card>
        <CardContent className='flex flex-col gap-2'>
          <Label id='range-label'>Range</Label>
          <ToggleGroup
            type='single'
            variant='outline'
            aria-labelledby='range-label'
            value={String(days)}
            // A toggle group can deselect its item; keep the range instead.
            onValueChange={(next) => next && setDays(Number(next))}
          >
            {RANGES.map((r) => (
              <ToggleGroupItem key={r.days} value={String(r.days)}>
                {r.label}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </CardContent>
      </Card>

      <QueryState query={withdrawals} skeletonClassName='h-96'>
        {(w) => {
          const points = w.points ?? []
          const latest = lastWithValue(points, 'rolling_average')
          return (
            <>
              <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-3'>
                <StatCard
                  title='10-day average of withdrawals'
                  hint='rolling-average'
                  value={
                    latest?.rolling_average == null
                      ? '—'
                      : formatBillions(latest.rolling_average)
                  }
                  note={asOf(latest?.record_date)}
                />
                <StatCard
                  title='Projected monthly rate'
                  hint='rolling-average'
                  value={
                    latest?.projected_monthly == null
                      ? '—'
                      : formatBillions(latest.projected_monthly)
                  }
                  note='10-day average × 20'
                />
                <UnemploymentStat query={unemployment} />
              </div>
              <Card>
                <CardHeader>
                  <CardTitle>Projected monthly withdrawals</CardTitle>
                  <CardDescription>
                    10-day average of total withdrawals × 20 business days
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <RollingChart
                    points={points}
                    dataKey='projected_monthly'
                    label='Projected monthly'
                    format={formatBillions}
                  />
                </CardContent>
              </Card>
            </>
          )
        }}
      </QueryState>

      <Card>
        <CardHeader>
          <CardTitle>Unemployment benefits, 10-day average</CardTitle>
          <CardDescription>
            Mean of the last 10 statements’ unemployment benefit payments
          </CardDescription>
        </CardHeader>
        <CardContent>
          <QueryState query={unemployment} skeletonClassName='h-72'>
            {(u) => (
              <RollingChart
                points={u.points ?? []}
                dataKey='rolling_average'
                label='10-day average'
                format={formatTreasuryValue}
              />
            )}
          </QueryState>
        </CardContent>
      </Card>
    </div>
  )
}

function UnemploymentStat({
  query,
}: {
  query: ReturnType<typeof useRollingAverage>
}) {
  const latest = query.data
    ? lastWithValue(query.data.points ?? [], 'rolling_average')
    : undefined
  return (
    <StatCard
      title='Unemployment benefits, 10-day average'
      hint='rolling-average'
      value={
        latest?.rolling_average == null
          ? '—'
          : formatTreasuryValue(latest.rolling_average)
      }
      note={asOf(latest?.record_date)}
    />
  )
}
