import type { ReactNode } from 'react'
import { FormulaHint } from '@/components/formula-hint'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { FormulaId } from '@/features/methodology/formulas'
import { cn } from '@/lib/utils'

type StatCardProps = {
  title: string
  value: ReactNode
  note?: ReactNode
  icon?: React.ElementType
  valueClassName?: string
  /** The formula behind the value, shown as a "How is this calculated?" button. */
  hint?: FormulaId
}

export function StatCard({
  title,
  value,
  note,
  icon: Icon,
  valueClassName,
  hint,
}: StatCardProps) {
  return (
    <Card>
      <CardHeader className='flex flex-row items-center justify-between gap-2'>
        <div className='flex items-center gap-1'>
          <CardTitle className='text-sm font-medium text-muted-foreground'>
            {title}
          </CardTitle>
          {hint && <FormulaHint id={hint} />}
        </div>
        {Icon && <Icon className='size-4 text-muted-foreground' />}
      </CardHeader>
      <CardContent className='flex flex-col gap-1'>
        <div
          className={cn('text-2xl font-semibold tabular-nums', valueClassName)}
        >
          {value}
        </div>
        {note && <p className='text-xs text-muted-foreground'>{note}</p>}
      </CardContent>
    </Card>
  )
}
