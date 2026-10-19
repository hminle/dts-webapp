import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { WithdrawalsYoYPage } from '@/features/yoy/withdrawals-page'

export const Route = createFileRoute('/yoy/withdrawals')({
  component: () => (
    <Page title='Withdrawals year over year'>
      <WithdrawalsYoYPage />
    </Page>
  ),
})
