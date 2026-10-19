import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatBillions } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { BreakdownRow } from '../lib'
import { changeClass, signedPrefix } from './accent'

type BreakdownTableProps = {
  rows: BreakdownRow[]
  total: { current: number; previous: number; change: number }
  currentFiscalYear: number
  previousFiscalYear: number
}

/** The components that add up to a category, with their total. */
export function BreakdownTable({
  rows,
  total,
  currentFiscalYear,
  previousFiscalYear,
}: BreakdownTableProps) {
  const changeCell = (value: number) => (
    <TableCell className={cn('text-end tabular-nums', changeClass(value))}>
      {signedPrefix(value)}
      {formatBillions(value)}
    </TableCell>
  )
  return (
    <div className='rounded-md border'>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Component</TableHead>
            <TableHead className='text-end'>FY{currentFiscalYear}</TableHead>
            <TableHead className='text-end'>FY{previousFiscalYear}</TableHead>
            <TableHead className='text-end'>Y-o-Y</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.key}>
              <TableCell className='text-xs text-muted-foreground'>
                {row.name}
                {row.code && (
                  <code className='block text-[10px]'>{row.code}</code>
                )}
              </TableCell>
              <TableCell className='text-end tabular-nums'>
                {formatBillions(row.current)}
              </TableCell>
              <TableCell className='text-end tabular-nums'>
                {formatBillions(row.previous)}
              </TableCell>
              {changeCell(row.change)}
            </TableRow>
          ))}
          <TableRow className='font-semibold'>
            <TableCell>Total</TableCell>
            <TableCell className='text-end tabular-nums'>
              {formatBillions(total.current)}
            </TableCell>
            <TableCell className='text-end tabular-nums'>
              {formatBillions(total.previous)}
            </TableCell>
            {changeCell(total.change)}
          </TableRow>
        </TableBody>
      </Table>
    </div>
  )
}
