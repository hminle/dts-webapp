import { TrendingDown, TrendingUp } from 'lucide-react'
import { FormulaHint } from '@/components/formula-hint'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDate, formatPercent } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { CategoryCardData } from '../lib'
import {
  ACCENT,
  changeClass,
  changeText,
  signedPrefix,
  totalText,
} from './accent'

type CategoryCardProps = {
  category: CategoryCardData
  onSelect: () => void
}

export function CategoryCard({ category, onSelect }: CategoryCardProps) {
  const change = category.yoy_change
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
        <FormulaHint id={category.formula} className='relative z-10' />
      </CardHeader>
      <CardContent className='flex flex-col gap-1'>
        <div className='text-2xl font-semibold tabular-nums'>
          {totalText(category.current_fytd)}
        </div>
        {change === null ? (
          <span className='text-xs text-muted-foreground'>
            Comparable from {formatDate(category.availableFrom)}
          </span>
        ) : (
          <div className='flex items-center gap-1'>
            {change >= 0 ? (
              <TrendingUp className='size-4 text-success' />
            ) : (
              <TrendingDown className='size-4 text-destructive' />
            )}
            <span
              className={cn(
                'text-sm font-medium tabular-nums',
                changeClass(change)
              )}
            >
              {changeText(change)}
            </span>
            {category.yoy_percent_change !== null && (
              <span className='text-xs text-muted-foreground tabular-nums'>
                ({signedPrefix(category.yoy_percent_change)}
                {formatPercent(category.yoy_percent_change)})
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
