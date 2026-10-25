import { OtherSpendingSection } from './components/other-spending-section'
import { SpendingCategoriesSection } from './components/spending-categories-section'
import { YoYAnalysisLayout } from './yoy-analysis-layout'

export function WithdrawalsYoYPage() {
  return (
    <YoYAnalysisLayout
      title='Total withdrawals — change from a year ago'
      description='Year-over-year difference in total withdrawals.'
      metric='total_withdrawals'
      formula='total-withdrawals'
      renderCategoriesSection={(pair) => (
        <>
          <SpendingCategoriesSection pair={pair} />
          <OtherSpendingSection pair={pair} />
        </>
      )}
    />
  )
}
