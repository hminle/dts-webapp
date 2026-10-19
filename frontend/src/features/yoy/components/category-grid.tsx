import { useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { YearPair } from '../api'
import type { CategoryCardData } from '../lib'
import { CategoryCard } from './category-card'
import { CategoryDetailDialog } from './category-detail-dialog'

type CategoryGridProps = {
  title: string
  description: string
  cards: CategoryCardData[]
  pair: YearPair
}

/** A titled grid of category cards; clicking a card opens its detail dialog. */
export function CategoryGrid({
  title,
  description,
  cards,
  pair,
}: CategoryGridProps) {
  const [selected, setSelected] = useState<CategoryCardData | null>(null)
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'>
            {cards.map((card) => (
              <CategoryCard
                key={card.name}
                category={card}
                onSelect={() => setSelected(card)}
              />
            ))}
          </div>
        </CardContent>
      </Card>
      <CategoryDetailDialog
        category={selected}
        pair={pair}
        onClose={() => setSelected(null)}
      />
    </>
  )
}

export function periodDescription(
  kind: 'spending' | 'receipts',
  pair: YearPair,
  currentDate: string | undefined,
  previousDate: string | undefined
): string {
  const mode =
    pair.comparisonMode === 'calendar_date' ? 'calendar date' : 'fiscal day'
  return (
    `FYTD ${kind} through ${currentDate ?? '—'} (FY${pair.currentFiscalYear}) ` +
    `compared to ${previousDate ?? '—'} (FY${pair.previousFiscalYear}), by ${mode}. ` +
    'Select a category for details.'
  )
}
