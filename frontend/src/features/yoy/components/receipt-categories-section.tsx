import { Skeleton } from '@/components/ui/skeleton'
import { useMajorReceipts } from '../api'
import type { YearPair } from '../api'
import { receiptCards } from '../lib'
import { CategoryGrid, periodDescription } from './category-grid'

export function ReceiptCategoriesSection({ pair }: { pair: YearPair }) {
  const receipts = useMajorReceipts(pair)

  if (receipts.isPending) return <Skeleton className='h-48 w-full' />
  const cards = receiptCards(receipts.data)
  if (cards.length === 0) return null

  return (
    <CategoryGrid
      title='Major receipt categories'
      description={periodDescription(
        'receipts',
        pair,
        receipts.data?.current_date,
        receipts.data?.previous_date
      )}
      cards={cards}
      pair={pair}
    />
  )
}
