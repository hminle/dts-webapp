import type { ColumnDef } from '@tanstack/react-table'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { DataGridFeatures } from '@/components/reui/data-grid/data-grid'
import { PagedGrid } from '@/components/paged-grid'
import { formatCurrency } from '@/lib/format'
import { END_ALIGNED_COLUMN_META } from '@/lib/table'
import { cn } from '@/lib/utils'
import type { WeekRow } from '../lib'

type Column = ColumnDef<DataGridFeatures, WeekRow>

const money = (
  id: 'firstFytd' | 'secondFytd' | 'difference',
  header: string
): Column => ({
  id,
  header,
  meta: END_ALIGNED_COLUMN_META,
  cell: ({ row }) => {
    const value = row.original[id]
    return (
      <span
        className={cn(
          'tabular-nums',
          id === 'difference' &&
            (value > 0 ? 'text-success' : value < 0 ? 'text-destructive' : '')
        )}
      >
        {formatCurrency(value)}
      </span>
    )
  },
})

type WeeklyTableProps = {
  rows: WeekRow[]
  weeks: number
  firstFiscalYear: number
  secondFiscalYear: number
}

export function WeeklyTable({
  rows,
  weeks,
  firstFiscalYear,
  secondFiscalYear,
}: WeeklyTableProps) {
  const columns: Column[] = [
    {
      id: 'week',
      header: 'Week',
      cell: ({ row }) => (
        <span className='font-medium'>{row.original.week}</span>
      ),
    },
    {
      id: 'firstDate',
      header: `FY ${firstFiscalYear} date`,
      cell: ({ row }) => row.original.firstDate,
    },
    money('firstFytd', `FY ${firstFiscalYear} FYTD`),
    {
      id: 'secondDate',
      header: `FY ${secondFiscalYear} date`,
      cell: ({ row }) => row.original.secondDate || 'N/A',
    },
    money('secondFytd', `FY ${secondFiscalYear} FYTD`),
    money('difference', 'Difference'),
  ]
  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly details</CardTitle>
        <CardDescription>
          {weeks} weeks compared · millions of dollars
        </CardDescription>
      </CardHeader>
      <CardContent>
        <PagedGrid
          data={rows}
          columns={columns}
          pageSize={53}
          emptyMessage='No weeks to compare.'
        />
      </CardContent>
    </Card>
  )
}
