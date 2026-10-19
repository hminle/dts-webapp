import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { NetTransfersComparePage } from '@/features/daily/net-transfers-page'

export const Route = createFileRoute('/daily/net-transfers')({
  component: () => (
    <Page title='Daily net transfers'>
      <NetTransfersComparePage />
    </Page>
  ),
})
