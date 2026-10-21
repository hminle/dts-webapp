import { TrendingDown, TrendingUp } from 'lucide-react'
import { FormulaHint } from '@/components/formula-hint'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { FormulaId } from '@/features/methodology/formulas'
import { formatBillions, formatPercent } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { CategoryCardData, CategoryKind } from '../lib'
import { ACCENT, changeClass, signedPrefix } from './accent'

export const CATEGORY_FORMULA: Record<CategoryKind, FormulaId> = {
  spending: 'major-spending',
  receipt: 'major-receipts',
  tbill: 'tbill-interest',
  irs_refund: 'irs-refunds',
}

type CategoryCardProps = {
  category: CategoryCardData
  onSelect: () => void
}

export function CategoryCard({ category, onSelect }: CategoryCardProps) {
  const up = category.yoy_change >= 0
  return (
    // The title button stretches over the whole card, so the card opens the
    // dialog on click without nesting the formula hint inside another button.
    <Card
      className={cn(
        'relative border-l-4 transition-shadow hover:shadow-md has-[[data-card-open]:focus-visible]:ring-2 has-[[data-card-open]:focus-visible]:ring-ring',
        ACCENT[category.accent].border
      )}
    >
      <CardHeader className='flex flex-row items-center gap-1'>
        <CardTitle className='text-sm font-medium'>
          <button
            type='button'
            data-card-open
            aria-label={`${category.name}: show details`}
            className='text-left outline-none after:absolute after:inset-0 after:cursor-pointer'
            onClick={onSelect}
          >
            {category.name}
          </button>
        </CardTitle>
        <FormulaHint
          id={CATEGORY_FORMULA[category.categoryType]}
          className='relative z-10'
        />
      </CardHeader>
      <CardContent className='flex flex-col gap-1'>
        <div className='text-2xl font-semibold tabular-nums'>
          {formatBillions(category.current_fytd)}
        </div>
        <div className='flex items-center gap-1'>
          {up ? (
            <TrendingUp className='size-4 text-success' />
          ) : (
            <TrendingDown className='size-4 text-destructive' />
          )}
          <span
            className={cn(
              'text-sm font-medium tabular-nums',
              changeClass(category.yoy_change)
            )}
          >
            {signedPrefix(category.yoy_change)}
            {formatBillions(category.yoy_change)}
          </span>
          {category.yoy_percent_change !== null && (
            <span className='text-xs text-muted-foreground tabular-nums'>
              ({signedPrefix(category.yoy_percent_change)}
              {formatPercent(category.yoy_percent_change)})
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
