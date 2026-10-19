import type { ColumnDef } from '@tanstack/react-table'
import type { DataGridFeatures } from '@/components/reui/data-grid/data-grid'
import { DataGridColumnHeader } from '@/components/reui/data-grid/data-grid-column-header'
import { PagedGrid } from '@/components/paged-grid'
import { formatCurrency, formatShortDate } from '@/lib/format'
import { END_ALIGNED_COLUMN_META } from '@/lib/table'
import { cn } from '@/lib/utils'
import type { DailyNetTransfer } from '../api'
import { flowDirection } from '../lib'

const FLOW_CLASS = { outflow: 'text-success', inflow: 'text-destructive', balanced: '' }

function signed(value: number) {
  return (
    <span className={cn('font-medium tabular-nums', FLOW_CLASS[flowDirection(value)])}>
      {formatCurrency(value)}
    </span>
  )
}

const COLUMNS: ColumnDef<DataGridFeatures, DailyNetTransfer>[] = [
  {
    id: 'record_date',
    accessorFn: (row) => row.record_date,
    header: ({ column }) => <DataGridColumnHeader column={column} title='Date' />,
    cell: ({ row }) => (
      <span className='whitespace-nowrap'>{formatShortDate(row.original.record_date)}</span>
    ),
  },
  {
    id: 'day_of_fiscal_year',
    accessorFn: (row) => row.day_of_fiscal_year,
    header: ({ column }) => <DataGridColumnHeader column={column} title='Day of FY' />,
    meta: END_ALIGNED_COLUMN_META,
    cell: ({ row }) => (
      <span className='tabular-nums'>{row.original.day_of_fiscal_year}</span>
    ),
  },
  {
    id: 'net_flow_today',
    accessorFn: (row) => row.net_flow_today,
    header: ({ column }) => <DataGridColumnHeader column={column} title='Net flow today' />,
    meta: END_ALIGNED_COLUMN_META,
    sortDescFirst: true,
    cell: ({ row }) => signed(row.original.net_flow_today),
  },
  {
    id: 'net_flow_fytd',
    accessorFn: (row) => row.net_flow_fytd,
    header: ({ column }) => <DataGridColumnHeader column={column} title='Net flow FYTD' />,
    meta: END_ALIGNED_COLUMN_META,
    sortDescFirst: true,
    cell: ({ row }) => signed(row.original.net_flow_fytd),
  },
  {
    id: 'total_withdrawals_fytd',
    accessorFn: (row) => row.total_withdrawals_fytd,
    header: ({ column }) => (
      <DataGridColumnHeader column={column} title='Withdrawals FYTD' />
    ),
    meta: END_ALIGNED_COLUMN_META,
    sortDescFirst: true,
    cell: ({ row }) => (
      <span className='tabular-nums'>
        {formatCurrency(row.original.total_withdrawals_fytd)}
      </span>
    ),
  },
]

export function FiscalYearTable({ days }: { days: DailyNetTransfer[] }) {
  return (
    <PagedGrid
      data={days}
      columns={COLUMNS}
      initialSorting={[{ id: 'day_of_fiscal_year', desc: false }]}
      emptyMessage='No days recorded for this fiscal year.'
    />
  )
}
