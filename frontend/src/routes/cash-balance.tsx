import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { CashBalancePage } from '@/features/cash-balance/cash-balance-page'

export const Route = createFileRoute('/cash-balance')({
  component: () => (
    <Page title='Cash balance'>
      <CashBalancePage />
    </Page>
  ),
})
