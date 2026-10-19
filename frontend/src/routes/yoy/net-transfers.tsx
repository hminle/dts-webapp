import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { NetTransfersYoYPage } from '@/features/yoy/net-transfers-page'

export const Route = createFileRoute('/yoy/net-transfers')({
  component: () => (
    <Page title='Net transfers year over year'>
      <NetTransfersYoYPage />
    </Page>
  ),
})
