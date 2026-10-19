import { CalendarCheck, RefreshCw } from 'lucide-react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { QueryState } from '@/components/query-state'
import { StatCard } from '@/components/stat-card'
import { dataSourceName } from '@/features/lookups/api'
import { useBuildInfo, useRecordCounts, useRecordCountsByYear } from '@/features/meta/api'
import { formatDate, formatDateTime, formatNumber } from '@/lib/format'

export function DataStatusPage() {
  const build = useBuildInfo()
  const counts = useRecordCounts()
  const byYear = useRecordCountsByYear()

  return (
    <div className='flex flex-col gap-6'>
      <QueryState query={build} skeletonClassName='h-28'>
        {(b) => (
          <div className='grid gap-4 md:grid-cols-2'>
            <StatCard
              title='Data through'
              icon={CalendarCheck}
              value={formatDate(b.latest_record_date)}
              note='The most recent statement in this dataset'
            />
            <StatCard
              title='Refreshed'
              icon={RefreshCw}
              value={<span className='text-base'>{formatDateTime(b.build_date)}</span>}
              note='Updates each business day after the Treasury publishes, around 4 pm ET'
            />
          </div>
        )}
      </QueryState>

      <div className='grid gap-4 lg:grid-cols-2'>
        <Card>
          <CardHeader>
            <CardTitle>Rows by table</CardTitle>
            <CardDescription>Every Daily Treasury Statement table we load</CardDescription>
          </CardHeader>
          <CardContent>
            <QueryState query={counts}>
              {(c) => (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Table</TableHead>
                      <TableHead className='text-end'>Rows</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(c).map(([table, rows]) => (
                      <TableRow key={table}>
                        <TableCell>{dataSourceName(table)}</TableCell>
                        <TableCell className='text-end tabular-nums'>
                          {formatNumber(rows)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </QueryState>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Rows by fiscal year</CardTitle>
            <CardDescription>Across all tables, newest first</CardDescription>
          </CardHeader>
          <CardContent>
            <QueryState query={byYear}>
              {(y) => (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fiscal year</TableHead>
                      <TableHead className='text-end'>Rows</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(y)
                      .sort(([a], [b]) => Number(b) - Number(a))
                      .map(([year, rows]) => (
                        <TableRow key={year}>
                          <TableCell>FY {year}</TableCell>
                          <TableCell className='text-end tabular-nums'>
                            {formatNumber(rows)}
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              )}
            </QueryState>
          </CardContent>
        </Card>
      </div>

      <p className='text-xs text-muted-foreground'>
        Source: U.S. Treasury Fiscal Data,{' '}
        <a
          className='underline underline-offset-2'
          href='https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/'
          target='_blank'
          rel='noreferrer'
        >
          Daily Treasury Statement
        </a>
        .
      </p>
    </div>
  )
}
