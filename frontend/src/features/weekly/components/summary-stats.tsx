import { ArrowDown, ArrowUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { WeeklyComparison } from '../api'
import type { WeeklySummary } from '../lib'

function Figure({
  label,
  value,
  className,
}: {
  label: string
  value: React.ReactNode
  className?: string
}) {
  return (
    <div className='flex flex-col gap-1'>
      <p className='text-sm text-muted-foreground'>{label}</p>
      <p className={cn('text-2xl font-semibold tabular-nums', className)}>
        {value}
      </p>
    </div>
  )
}

export function SummaryStats({
  data,
  stats,
}: {
  data: WeeklyComparison
  stats: WeeklySummary
}) {
  const pct = stats.percentChange
  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly summary</CardTitle>
      </CardHeader>
      <CardContent className='grid gap-6 md:grid-cols-3'>
        {[
          {
            fy: data.first_fiscal_year,
            weeks: data.first_year_data?.length ?? 0,
            total: stats.firstYearTotal,
          },
          {
            fy: data.second_fiscal_year,
            weeks: data.second_year_data?.length ?? 0,
            total: stats.secondYearTotal,
          },
        ].map(({ fy, weeks, total }) => (
          <div key={fy} className='flex flex-col gap-3'>
            <h3 className='font-medium'>
              FY {fy - 1}–{fy}
            </h3>
            <Figure label='Weekly data points' value={weeks} />
            <Figure
              label='Latest weekly net transfers FYTD'
              value={formatCurrency(total)}
            />
          </div>
        ))}
        <div className='flex flex-col gap-3'>
          <h3 className='font-medium'>Year-over-year</h3>
          <Figure
            label='Weekly YoY difference'
            value={formatCurrency(stats.difference)}
          />
          <Figure
            label='Change'
            className={cn(
              'flex items-center gap-1',
              pct === null
                ? 'text-muted-foreground'
                : pct > 0
                  ? 'text-success'
                  : pct < 0
                    ? 'text-destructive'
                    : ''
            )}
            value={
              pct === null ? (
                'N/A'
              ) : (
                <>
                  {pct > 0 && <ArrowUp className='size-5' />}
                  {pct < 0 && <ArrowDown className='size-5' />}
                  {Math.abs(pct).toFixed(2)}%
                </>
              )
            }
          />
        </div>
      </CardContent>
    </Card>
  )
}
