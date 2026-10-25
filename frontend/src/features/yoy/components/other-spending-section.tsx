import { Skeleton } from '@/components/ui/skeleton'
import { useOtherSpending } from '../api'
import type { YearPair } from '../api'
import { otherSpendingCards } from '../lib'
import { CategoryGrid, periodDescription } from './category-grid'

export function OtherSpendingSection({ pair }: { pair: YearPair }) {
  const spending = useOtherSpending(pair)

  if (spending.isPending) return <Skeleton className='h-48 w-full' />
  const cards = otherSpendingCards(spending.data)
  if (cards.length === 0) return null

  return (
    <CategoryGrid
      title='Other spending categories'
      description={periodDescription(
        'spending',
        pair,
        spending.data?.current_date,
        spending.data?.previous_date
      )}
      cards={cards}
      pair={pair}
    />
  )
}
