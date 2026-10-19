import { useState } from 'react'
import { useTable } from '@tanstack/react-table'
import type { ColumnDef, SortingState } from '@tanstack/react-table'
import {
  DataGrid,
  DataGridContainer,
  dataGridFeatures,
} from '@/components/reui/data-grid/data-grid'
import type { DataGridFeatures } from '@/components/reui/data-grid/data-grid'
import { DataGridPagination } from '@/components/reui/data-grid/data-grid-pagination'
import { DataGridScrollArea } from '@/components/reui/data-grid/data-grid-scroll-area'
import { DataGridTable } from '@/components/reui/data-grid/data-grid-table'

type PagedGridProps<Row> = {
  data: Row[]
  columns: ColumnDef<DataGridFeatures, Row>[]
  pageSize?: number
  initialSorting?: SortingState
  emptyMessage: string
}

/**
 * A sortable grid that pages in the browser — for responses that arrive whole
 * (one date's rows, one fiscal year's days). Server-paged data uses the grid
 * with `manualPagination` instead.
 */
export function PagedGrid<Row>({
  data,
  columns,
  pageSize = 20,
  initialSorting = [],
  emptyMessage,
}: PagedGridProps<Row>) {
  const [sorting, setSorting] = useState<SortingState>(initialSorting)
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize })

  const table = useTable({
    features: dataGridFeatures,
    data,
    columns,
    state: { sorting, pagination },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    // Two states only; the third would fall back to the API's order, which
    // looks like a sort nobody asked for.
    enableSortingRemoval: false,
  })

  return (
    <DataGrid
      table={table}
      recordCount={data.length}
      emptyMessage={emptyMessage}
      tableLayout={{ width: 'auto' }}
    >
      <div className='flex flex-col gap-3'>
        <DataGridContainer className='min-w-0 rounded-md border'>
          <DataGridScrollArea orientation='horizontal'>
            <DataGridTable />
          </DataGridScrollArea>
        </DataGridContainer>
        {data.length > pageSize && <DataGridPagination sizes={[20, 50, 100]} />}
      </div>
    </DataGrid>
  )
}
