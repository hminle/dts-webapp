import { OtherReceiptsSection } from './components/other-receipts-section'
import { ReceiptCategoriesSection } from './components/receipt-categories-section'
import { YoYAnalysisLayout } from './yoy-analysis-layout'

export function DepositsYoYPage() {
  return (
    <YoYAnalysisLayout
      title='Treasury deposits — change from a year ago'
      description='Year-over-year difference in total deposits.'
      metric='total_deposits'
      formula='total-deposits'
      latestNote='Higher means more revenue'
      renderCategoriesSection={(pair) => (
        <>
          <ReceiptCategoriesSection pair={pair} />
          <OtherReceiptsSection pair={pair} />
        </>
      )}
    />
  )
}
