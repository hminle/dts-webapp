import { useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { CircleAlert } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { QueryState } from '@/components/query-state'
import { ApiError } from '@/lib/api/client'
import { useBuildInfo } from '@/features/meta/api'
import { formatDate, formatNumber } from '@/lib/format'
import { useDataByDate, useNetTransfersForDate } from './api'
import { DateControls } from './components/date-controls'
import { NetTransfersSummary } from './components/net-transfers-summary'
import { TransactionsTable } from './components/transactions-table'

const DATA_SOURCE = 'deposits_withdrawals'

/** Both lookups 404 on a weekend or holiday: one explanation, not two alerts. */
function noStatement(...errors: (Error | null)[]): boolean {
  return errors.every((e) => e instanceof ApiError && e.status === 404)
}

export function SingleDatePage() {
  const build = useBuildInfo()
  const [queryDate, setQueryDate] = useState<string | null>(null)
  const summary = useNetTransfersForDate(queryDate)
  const rows = useDataByDate(queryDate, DATA_SOURCE)

  return (
    <div className='flex flex-col gap-6'>
      <Card>
        <CardHeader>
          <CardTitle>Select a date</CardTitle>
          <CardDescription>
            Deposits and withdrawals of the Treasury General Account for one
            business day
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* The latest statement is the useful default; "today" usually has none
              yet because the Treasury publishes in the afternoon. */}
          {build.isPending ? null : (
            <DateControls
              initialDate={build.data?.latest_record_date ?? ''}
              onSearch={setQueryDate}
            />
          )}
        </CardContent>
      </Card>

      {queryDate && noStatement(summary.error, rows.error) && (
        <Alert>
          <CircleAlert />
          <AlertDescription>
            No statement for {formatDate(queryDate)}. The Treasury publishes on
            business days only; the latest is{' '}
            {build.data ? formatDate(build.data.latest_record_date) : 'shown on Data status'}.
          </AlertDescription>
        </Alert>
      )}

      {queryDate && !noStatement(summary.error, rows.error) && (
        <>
          <QueryState query={summary}>
            {(day) => <NetTransfersSummary day={day} />}
          </QueryState>

          <QueryState query={rows} skeletonClassName='h-64'>
            {(data) => (
              <Card>
                <CardHeader>
                  <CardTitle>Records for {formatDate(queryDate)}</CardTitle>
                  <CardDescription>
                    {formatNumber(data.length)} rows · Deposits &amp; Withdrawals ·
                    click a column header to sort
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <TransactionsTable rows={data} />
                </CardContent>
              </Card>
            )}
          </QueryState>
        </>
      )}
    </div>
  )
}
