import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatNumber } from '@/lib/format'
import { cn } from '@/lib/utils'

export type ArithmeticRow = {
  label: string
  /** The operator that joins this row to the one above. */
  op?: '+' | '−' | '='
  values: (number | string)[]
  /** A result row: set in the foreground color and weight. */
  result?: boolean
}

/** A worked example laid out as a sum, with numbers in millions of dollars. */
export function ArithmeticTable({
  columns,
  rows,
  caption,
}: {
  columns: string[]
  rows: ArithmeticRow[]
  caption?: string
}) {
  return (
    <figure className='flex flex-col gap-2'>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <span className='sr-only'>Line</span>
            </TableHead>
            {columns.map((column) => (
              <TableHead key={column} className='text-right'>
                {column}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow
              key={row.label}
              className={cn(row.result && 'font-medium text-foreground')}
            >
              <TableCell className='whitespace-normal'>
                {row.op && (
                  <span className='me-2 inline-block w-3 font-mono'>
                    {row.op}
                  </span>
                )}
                {row.label}
              </TableCell>
              {row.values.map((value, i) => (
                <TableCell
                  key={i}
                  className={cn(
                    'text-right',
                    typeof value === 'number' && 'font-mono tabular-nums'
                  )}
                >
                  {typeof value === 'number' ? formatNumber(value) : value}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {caption && <figcaption className='text-xs'>{caption}</figcaption>}
    </figure>
  )
}
