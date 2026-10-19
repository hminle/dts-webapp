import { Skeleton } from '@/components/ui/skeleton'
import { useIrsTaxRefunds, useMajorSpending, useTBillInterest } from '../api'
import type { YearPair } from '../api'
import { spendingCards } from '../lib'
import { CategoryGrid, periodDescription } from './category-grid'

export function SpendingCategoriesSection({ pair }: { pair: YearPair }) {
  const spending = useMajorSpending(pair)
  const tbill = useTBillInterest(pair)
  const irs = useIrsTaxRefunds(pair)

  if (
    !spending.data &&
    !tbill.data &&
    (spending.isPending || tbill.isPending)
  ) {
    return <Skeleton className='h-48 w-full' />
  }
  const cards = spendingCards(spending.data, tbill.data, irs.data)
  if (cards.length === 0) return null

  return (
    <CategoryGrid
      title='Major spending categories'
      description={periodDescription(
        'spending',
        pair,
        spending.data?.current_date ?? tbill.data?.current_date,
        spending.data?.previous_date ?? tbill.data?.previous_date
      )}
      cards={cards}
      pair={pair}
    />
  )
}
