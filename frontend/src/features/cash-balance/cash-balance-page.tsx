import { useState } from 'react'
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts'
import { QueryState } from '@/components/query-state'
import { StatCard } from '@/components/stat-card'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { ChartContainer, ChartTooltip } from '@/components/ui/chart'
import type { ChartConfig } from '@/components/ui/chart'
import { Label } from '@/components/ui/label'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { rangeStart } from '@/features/daily/lib'
import { changeClass, changeText } from '@/features/yoy/components/accent'
import { formatBillions, formatDate, formatShortDate } from '@/lib/format'
import { useCashBalance } from './api'
import { latestChange } from './lib'

// The first statement in the artifact.
const DATA_START = '2005-10-03'

const RANGES = [
  { label: '1 year', value: '365' },
  { label: '5 years', value: '1826' },
  { label: 'All', value: 'all' },
] as const

const config = {
  closing_balance: { label: 'Closing balance', color: 'var(--chart-1)' },
} satisfies ChartConfig

export function CashBalancePage() {
  const [range, setRange] = useState<string>('365')
  const startDate =
    range === 'all' ? DATA_START : rangeStart(Number(range), new Date())
  const balance = useCashBalance(startDate)

  return (
    <div className='flex flex-col gap-6'>
      <Card>
        <CardContent className='flex flex-col gap-2'>
          <Label id='cash-range-label'>Range</Label>
          <ToggleGroup
            type='single'
            variant='outline'
            aria-labelledby='cash-range-label'
            value={range}
            // A toggle group can deselect its item; keep the range instead.
            onValueChange={(next) => next && setRange(next)}
          >
            {RANGES.map((r) => (
              <ToggleGroupItem key={r.value} value={r.value}>
                {r.label}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </CardContent>
      </Card>

      <QueryState query={balance} skeletonClassName='h-96'>
        {(data) => {
          const points = data.points ?? []
          const latest = latestChange(points)
          const last = points[points.length - 1]
          return (
            <>
              <div className='grid gap-4 sm:grid-cols-2'>
                <StatCard
                  title='Closing balance'
                  hint='cash-balance'
                  value={last ? formatBillions(last.closing_balance) : '—'}
                  note={last ? formatDate(last.record_date) : undefined}
                />
                <StatCard
                  title='Change over 5 statements'
                  hint='cash-balance'
                  value={changeText(latest?.change ?? null)}
                  valueClassName={
                    latest ? changeClass(latest.change) : undefined
                  }
                  note={
                    latest
                      ? `Since ${formatShortDate(latest.previous.record_date)}`
                      : undefined
                  }
                />
              </div>
              <Card>
                <CardHeader>
                  <CardTitle>
                    Treasury General Account, closing balance
                  </CardTitle>
                  <CardDescription>Billions of dollars</CardDescription>
                </CardHeader>
                <CardContent className='flex flex-col gap-3'>
                  <ChartContainer
                    config={config}
                    className='aspect-auto h-80 w-full'
                  >
                    <LineChart
                      data={points}
                      margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
                    >
                      <CartesianGrid vertical={false} />
                      <XAxis
                        dataKey='record_date'
                        tickLine={false}
                        axisLine={false}
                        tickMargin={8}
                        minTickGap={32}
                        tickFormatter={formatShortDate}
                      />
                      <YAxis
                        tickLine={false}
                        axisLine={false}
                        width={72}
                        tickFormatter={formatBillions}
                      />
                      <ChartTooltip
                        content={({ active, payload }) => {
                          const p = active ? payload?.[0]?.payload : undefined
                          if (!p) return null
                          return (
                            <div className='grid min-w-36 gap-1 rounded-lg border bg-background px-3 py-2 text-xs shadow-xl'>
                              <p className='font-medium'>
                                {formatShortDate(p.record_date)}
                              </p>
                              <p className='font-semibold tabular-nums'>
                                {formatBillions(p.closing_balance)}
                              </p>
                            </div>
                          )
                        }}
                      />
                      <Line
                        type='monotone'
                        dataKey='closing_balance'
                        stroke='var(--color-closing_balance)'
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ChartContainer>
                  <p className='text-xs text-muted-foreground'>
                    Cash the Treasury holds at the Federal Reserve. Before 2012
                    the Treasury also held cash in Tax and Loan accounts, not
                    shown.
                  </p>
                </CardContent>
              </Card>
            </>
          )
        }}
      </QueryState>
    </div>
  )
}
