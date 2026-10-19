import { useState } from 'react'
import { useTable } from '@tanstack/react-table'
import type { ColumnDef } from '@tanstack/react-table'
import {
  DataGrid,
  DataGridContainer,
  dataGridFeatures,
} from '@/components/reui/data-grid/data-grid'
import type { DataGridFeatures } from '@/components/reui/data-grid/data-grid'
import { DataGridScrollArea } from '@/components/reui/data-grid/data-grid-scroll-area'
import { DataGridTable } from '@/components/reui/data-grid/data-grid-table'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { FiscalYearSelect } from '@/components/fiscal-year-select'
import { QueryState } from '@/components/query-state'
import type { TreasuryRow } from '@/features/daily/api'
import { dataSourceName, useDataSources, useFiscalYears } from '@/features/lookups/api'
import {
  formatCurrency,
  formatNumber,
  formatShortDate,
  formatText,
} from '@/lib/format'
import { END_ALIGNED_COLUMN_META } from '@/lib/table'
import { useFiscalYearData } from './api'

const PAGE_SIZE = 50

const COLUMNS: ColumnDef<DataGridFeatures, TreasuryRow>[] = [
  {
    id: 'record_date',
    header: 'Date',
    cell: ({ row }) => (
      <span className='whitespace-nowrap'>
        {formatShortDate(row.original.record_date)}
      </span>
    ),
  },
  {
    id: 'data_source',
    header: 'Source',
    cell: ({ row }) => (
      <span className='whitespace-nowrap'>
        {row.original.data_source ? dataSourceName(row.original.data_source) : '—'}
      </span>
    ),
  },
  {
    id: 'account_type',
    header: 'Account',
    cell: ({ row }) => (
      <span
        className='block max-w-56 truncate'
        title={formatText(row.original.account_type)}
      >
        {formatText(row.original.account_type)}
      </span>
    ),
  },
  {
    id: 'transaction_catg',
    header: 'Category',
    cell: ({ row }) => (
      <span
        className='block max-w-64 truncate'
        title={formatText(row.original.transaction_catg)}
      >
        {formatText(row.original.transaction_catg)}
      </span>
    ),
  },
  ...(['transaction_today_amt', 'transaction_mtd_amt', 'transaction_fytd_amt'] as const).map(
    (key, i): ColumnDef<DataGridFeatures, TreasuryRow> => ({
      id: key,
      header: ['Today', 'MTD', 'FYTD'][i],
      meta: END_ALIGNED_COLUMN_META,
      cell: ({ row }) => (
        <span className='tabular-nums'>{formatCurrency(row.original[key])}</span>
      ),
    })
  ),
]

function ResultsGrid({ rows }: { rows: TreasuryRow[] }) {
  const table = useTable({
    features: dataGridFeatures,
    data: rows,
    columns: COLUMNS,
    // The server already sliced this page; the grid's own paginated row model
    // would slice it again down to its default page size.
    manualPagination: true,
  })
  return (
    <DataGrid
      table={table}
      recordCount={rows.length}
      emptyMessage='No rows for this fiscal year and source.'
      tableLayout={{ width: 'auto' }}
    >
      <DataGridContainer className='min-w-0 rounded-md border'>
        <DataGridScrollArea orientation='horizontal'>
          <DataGridTable />
        </DataGridScrollArea>
      </DataGridContainer>
    </DataGrid>
  )
}

export function FiscalYearPage() {
  const years = useFiscalYears()
  const sources = useDataSources()
  const [chosenYear, setChosenYear] = useState<number | null>(null)
  const [dataSource, setDataSource] = useState('all')
  const [page, setPage] = useState(1)
  const fiscalYear = chosenYear ?? years.data?.[0] ?? null
  const data = useFiscalYearData(
    fiscalYear === null ? null : { fiscalYear, dataSource, page, pageSize: PAGE_SIZE }
  )

  return (
    <div className='flex flex-col gap-6'>
      <Card>
        <CardHeader>
          <CardTitle>Fiscal year and source</CardTitle>
          <CardDescription>
            Every row the Treasury published for a fiscal year
          </CardDescription>
        </CardHeader>
        <CardContent className='flex flex-wrap gap-6'>
          <FiscalYearSelect
            id='fiscal-year'
            label='Fiscal year'
            years={years.data ?? []}
            value={fiscalYear}
            onChange={(year) => {
              setChosenYear(year)
              setPage(1)
            }}
          />
          <div className='flex flex-col gap-2'>
            <Label htmlFor='data-source'>Data source</Label>
            <Select
              value={dataSource}
              onValueChange={(value) => {
                setDataSource(value)
                setPage(1)
              }}
            >
              <SelectTrigger id='data-source' className='w-64'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value='all'>All data sources</SelectItem>
                {(sources.data ?? []).map((source) => (
                  <SelectItem key={source} value={source}>
                    {dataSourceName(source)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {fiscalYear !== null && (
        <QueryState query={data} skeletonClassName='h-96'>
          {(result) => (
            <Card>
              <CardHeader>
                <CardTitle>
                  FY {fiscalYear}
                  {dataSource !== 'all' && (
                    <span className='ms-2 font-normal text-muted-foreground'>
                      · {dataSourceName(dataSource)}
                    </span>
                  )}
                </CardTitle>
                <CardDescription>
                  {formatNumber(result.total)} rows · page {result.page} of{' '}
                  {Math.max(result.pages, 1)} · newest first · millions of dollars
                </CardDescription>
              </CardHeader>
              <CardContent className='flex flex-col gap-3'>
                <ResultsGrid rows={result.items} />
                {result.pages > 1 && (
                  <div className='flex items-center justify-end gap-2'>
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={page === 1}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                    >
                      Previous
                    </Button>
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={page >= result.pages}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </QueryState>
      )}
    </div>
  )
}
