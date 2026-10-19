import { Info } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { SpendingCategoriesSection } from './components/spending-categories-section'
import { YoYAnalysisLayout } from './yoy-analysis-layout'

export function WithdrawalsYoYPage() {
  return (
    <YoYAnalysisLayout
      title='Total withdrawals — change from a year ago'
      description='Year-over-year difference in total withdrawals (excluding public debt redemptions).'
      metric='total_withdrawals'
      infoAlert={
        <Alert>
          <Info />
          <AlertDescription>
            Total withdrawals = TGA total withdrawals − public debt cash
            redemptions. This leaves out debt repayment to show actual
            government spending.
          </AlertDescription>
        </Alert>
      }
      renderCategoriesSection={(pair) => (
        <SpendingCategoriesSection pair={pair} />
      )}
    />
  )
}
