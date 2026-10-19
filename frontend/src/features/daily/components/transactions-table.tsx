import type { ColumnDef } from '@tanstack/react-table'
import type { DataGridFeatures } from '@/components/reui/data-grid/data-grid'
import { DataGridColumnHeader } from '@/components/reui/data-grid/data-grid-column-header'
import { PagedGrid } from '@/components/paged-grid'
import { formatCurrency, formatText } from '@/lib/format'
import { END_ALIGNED_COLUMN_META } from '@/lib/table'
import type { TreasuryRow } from '../api'

function text(value: string | null | undefined) {
  const shown = formatText(value)
  return (
    <span className='block max-w-64 truncate' title={shown}>
      {shown}
    </span>
  )
}

type AmountKey = 'transaction_today_amt' | 'transaction_mtd_amt' | 'transaction_fytd_amt'

function amount(
  key: AmountKey,
  title: string
): ColumnDef<DataGridFeatures, TreasuryRow> {
  return {
    id: key,
    accessorFn: (row) => row[key] ?? undefined,
    header: ({ column }) => <DataGridColumnHeader column={column} title={title} />,
    meta: END_ALIGNED_COLUMN_META,
    sortDescFirst: true,
    sortUndefined: 'last',
    cell: ({ row }) => (
      <span className='tabular-nums'>{formatCurrency(row.original[key])}</span>
    ),
  }
}

// The API's row model carries these fields only; the reference table also
// listed table name, line numbers and calendar parts, which were always "N/A".
const COLUMNS: ColumnDef<DataGridFeatures, TreasuryRow>[] = [
  {
    id: 'account_type',
    accessorFn: (row) => row.account_type ?? '',
    header: ({ column }) => <DataGridColumnHeader column={column} title='Account' />,
    cell: ({ row }) => text(row.original.account_type),
  },
  {
    id: 'transaction_type',
    accessorFn: (row) => row.transaction_type ?? '',
    header: ({ column }) => <DataGridColumnHeader column={column} title='Type' />,
    cell: ({ row }) => text(row.original.transaction_type),
  },
  {
    id: 'transaction_catg',
    accessorFn: (row) => row.transaction_catg ?? '',
    header: ({ column }) => <DataGridColumnHeader column={column} title='Category' />,
    cell: ({ row }) => text(row.original.transaction_catg),
  },
  amount('transaction_today_amt', 'Today'),
  amount('transaction_mtd_amt', 'MTD'),
  amount('transaction_fytd_amt', 'FYTD'),
]

export function TransactionsTable({ rows }: { rows: TreasuryRow[] }) {
  return (
    <PagedGrid
      data={rows}
      columns={COLUMNS}
      initialSorting={[{ id: 'transaction_today_amt', desc: true }]}
      emptyMessage='No deposits or withdrawals recorded for this date.'
    />
  )
}
