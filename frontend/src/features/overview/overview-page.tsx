import { Link } from '@tanstack/react-router'
import { Activity, Calendar, CalendarRange, Database, TrendingUp } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { QueryState } from '@/components/query-state'
import { StatCard } from '@/components/stat-card'
import { dataSourceName } from '@/features/lookups/api'
import { useStats } from '@/features/meta/api'
import { formatDateTime, formatNumber, formatShortDate } from '@/lib/format'

const QUICK_LINKS = [
  {
    to: '/daily/single-date',
    icon: Calendar,
    title: 'Single date',
    text: 'Deposits, withdrawals and net flow for one business day',
  },
  {
    to: '/yoy/net-transfers',
    icon: TrendingUp,
    title: 'Year over year',
    text: 'Net transfers against the same day last fiscal year',
  },
  {
    to: '/weekly',
    icon: CalendarRange,
    title: 'Weekly comparison',
    text: 'Friday-to-Friday totals for two fiscal years',
  },
] as const

export function OverviewPage() {
  const stats = useStats()

  return (
    <div className='flex flex-col gap-6'>
      <div className='flex flex-col gap-1'>
        <h2 className='text-2xl font-semibold tracking-tight'>
          U.S. Treasury Daily Statement
        </h2>
        <p className='text-sm text-muted-foreground'>
          Cash in and out of the Treasury General Account, every business day since
          2005. Amounts are in millions of dollars.
        </p>
      </div>

      <QueryState query={stats}>
        {(s) => (
          <>
            <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
              <StatCard
                title='Total records'
                icon={Database}
                value={formatNumber(s.record_count)}
                note='Across all data sources'
              />
              <StatCard
                title='Date range'
                icon={Calendar}
                value={`${s.fiscal_years.length} fiscal years`}
                note={
                  s.earliest_date && s.latest_date
                    ? `${formatShortDate(s.earliest_date)} – ${formatShortDate(s.latest_date)}`
                    : 'No data yet'
                }
              />
              <StatCard
                title='Data sources'
                icon={TrendingUp}
                value={s.data_sources.length}
                note='Daily Treasury Statement tables'
              />
              <StatCard
                title='Last updated'
                icon={Activity}
                value={
                  <span className='text-base'>
                    {s.last_updated ? formatDateTime(s.last_updated) : 'Never'}
                  </span>
                }
                note='When the daily refresh last ran'
              />
            </div>

            <div className='grid gap-4 md:grid-cols-2'>
              <Card>
                <CardHeader>
                  <CardTitle>Available data sources</CardTitle>
                  <CardDescription>Treasury tables in this dataset</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className='flex flex-col gap-2'>
                    {s.data_sources.map((source) => (
                      <li key={source} className='flex items-center gap-2 text-sm'>
                        <span className='size-1.5 rounded-full bg-primary' />
                        {dataSourceName(source)}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Available fiscal years</CardTitle>
                  <CardDescription>October 1 to September 30</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='flex flex-wrap gap-2'>
                    {s.fiscal_years.map((year) => (
                      <Badge key={year} variant='secondary'>
                        FY {year}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </QueryState>

      <Card>
        <CardHeader>
          <CardTitle>Quick start</CardTitle>
          <CardDescription>Common places to begin</CardDescription>
        </CardHeader>
        <CardContent className='grid gap-3 md:grid-cols-3'>
          {QUICK_LINKS.map(({ to, icon: Icon, title, text }) => (
            <Link
              key={to}
              to={to}
              className='flex flex-col gap-1 rounded-lg border p-4 transition-colors hover:bg-accent'
            >
              <Icon className='size-5 text-muted-foreground' />
              <span className='font-medium'>{title}</span>
              <span className='text-xs text-muted-foreground'>{text}</span>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
