import { YoYAnalysisLayout } from './yoy-analysis-layout'

export function NetTransfersYoYPage() {
  return (
    <YoYAnalysisLayout
      title='Net government transfers — change from a year ago'
      description='Year-over-year difference in net government transfers (total withdrawals − total deposits).'
      metric='net_flow'
    />
  )
}
