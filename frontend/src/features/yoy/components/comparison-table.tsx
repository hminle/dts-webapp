import type { ColumnDef } from '@tanstack/react-table'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { DataGridFeatures } from '@/components/reui/data-grid/data-grid'
import { DataGridColumnHeader } from '@/components/reui/data-grid/data-grid-column-header'
import { PagedGrid } from '@/components/paged-grid'
import { formatCurrency } from '@/lib/format'
import { END_ALIGNED_COLUMN_META } from '@/lib/table'
import { cn } from '@/lib/utils'
import type { YoYCategoryComparison } from '../api'
import { comparisonRows } from '../lib'
import type { ComparisonRow } from '../lib'
import { changeClass } from './accent'

type Column = ColumnDef<DataGridFeatures, ComparisonRow>

const money = (
  id: 'currentFytd' | 'previousFytd' | 'difference',
  title: string,
  colored = false
): Column => ({
  id,
  accessorFn: (row) => row[id],
  header: ({ column }) => (
    <DataGridColumnHeader column={column} title={title} />
  ),
  meta: END_ALIGNED_COLUMN_META,
  sortDescFirst: true,
  cell: ({ row }) => (
    <span
      className={cn('tabular-nums', colored && changeClass(row.original[id]))}
    >
      {formatCurrency(row.original[id])}
    </span>
  ),
})

function columns(currentFy: number, previousFy: number): Column[] {
  return [
    {
      id: 'day',
      accessorFn: (row) => row.day,
      header: ({ column }) => (
        <DataGridColumnHeader column={column} title='Day' />
      ),
      cell: ({ row }) => (
        <span className='font-medium tabular-nums'>{row.original.day}</span>
      ),
    },
    {
      id: 'category',
      accessorFn: (row) => row.category,
      header: ({ column }) => (
        <DataGridColumnHeader column={column} title='Category' />
      ),
      cell: ({ row }) => (
        <span className='block max-w-56 truncate' title={row.original.category}>
          {row.original.category}
        </span>
      ),
    },
    {
      id: 'currentDate',
      header: `FY${currentFy} date`,
      cell: ({ row }) => (
        <span className='whitespace-nowrap'>{row.original.currentDate}</span>
      ),
    },
    money('currentFytd', `FY${currentFy} FYTD`),
    {
      id: 'previousDate',
      header: `FY${previousFy} date`,
      cell: ({ row }) => (
        <span className='whitespace-nowrap'>
          {row.original.previousDate ?? 'N/A'}
        </span>
      ),
    },
    money('previousFytd', `FY${previousFy} FYTD`),
    money('difference', 'Difference', true),
    {
      id: 'percentChange',
      accessorFn: (row) => row.percentChange ?? undefined,
      header: ({ column }) => (
        <DataGridColumnHeader column={column} title='% change' />
      ),
      meta: END_ALIGNED_COLUMN_META,
      sortUndefined: 'last',
      cell: ({ row }) => {
        const pct = row.original.percentChange
        return pct === null ? (
          <span className='text-muted-foreground'>N/A</span>
        ) : (
          <span className={cn('tabular-nums', changeClass(pct))}>
            {pct.toFixed(2)}%
          </span>
        )
      },
    },
  ]
}

export function ComparisonTable({ data }: { data: YoYCategoryComparison }) {
  const rows = comparisonRows(data)
  if (rows.length === 0) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle>Detailed data</CardTitle>
        <CardDescription>
          {rows.length} data points across{' '}
          {(data.current_year_data ?? []).length} categories · millions of
          dollars
        </CardDescription>
      </CardHeader>
      <CardContent>
        <PagedGrid
          data={rows}
          columns={columns(data.current_fiscal_year, data.previous_fiscal_year)}
          pageSize={50}
          emptyMessage='No days to compare.'
        />
      </CardContent>
    </Card>
  )
}
