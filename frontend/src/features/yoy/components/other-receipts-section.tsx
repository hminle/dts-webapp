import { Skeleton } from '@/components/ui/skeleton'
import { useOtherReceipts } from '../api'
import type { YearPair } from '../api'
import { otherReceiptCards } from '../lib'
import { CategoryGrid, periodDescription } from './category-grid'

export function OtherReceiptsSection({ pair }: { pair: YearPair }) {
  const receipts = useOtherReceipts(pair)

  if (receipts.isPending) return <Skeleton className='h-48 w-full' />
  const cards = otherReceiptCards(receipts.data)
  if (cards.length === 0) return null

  return (
    <CategoryGrid
      title='Other receipt categories'
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
