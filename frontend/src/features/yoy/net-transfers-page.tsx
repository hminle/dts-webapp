import { YoYAnalysisLayout } from './yoy-analysis-layout'

export function NetTransfersYoYPage() {
  return (
    <YoYAnalysisLayout
      title='Net government transfers — change from a year ago'
      description='Year-over-year difference in net government transfers.'
      metric='net_flow'
      formula='net-transfers'
    />
  )
}
