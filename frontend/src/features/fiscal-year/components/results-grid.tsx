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
import type { TreasuryRow } from '@/features/daily/api'
import { dataSourceName } from '@/features/lookups/api'
import { formatCurrency, formatShortDate, formatText } from '@/lib/format'
import { END_ALIGNED_COLUMN_META } from '@/lib/table'

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

export function ResultsGrid({ rows }: { rows: TreasuryRow[] }) {
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
