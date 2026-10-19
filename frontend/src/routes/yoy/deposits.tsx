import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { DepositsYoYPage } from '@/features/yoy/deposits-page'

export const Route = createFileRoute('/yoy/deposits')({
  component: () => (
    <Page title='Deposits year over year'>
      <DepositsYoYPage />
    </Page>
  ),
})
