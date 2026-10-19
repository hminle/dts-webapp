import { TrendingDown, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatBillions, formatPercent } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { CategoryCardData } from '../lib'
import { ACCENT, changeClass, signedPrefix } from './accent'

type CategoryCardProps = {
  category: CategoryCardData
  onSelect: () => void
}

export function CategoryCard({ category, onSelect }: CategoryCardProps) {
  const up = category.yoy_change >= 0
  return (
    <Card
      role='button'
      tabIndex={0}
      aria-label={`${category.name}: show details`}
      className={cn(
        'cursor-pointer border-l-4 transition-shadow hover:shadow-md focus-visible:ring-2 focus-visible:ring-ring',
        ACCENT[category.accent].border
      )}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onSelect()
        }
      }}
    >
      <CardHeader>
        <CardTitle className='text-sm font-medium'>{category.name}</CardTitle>
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
