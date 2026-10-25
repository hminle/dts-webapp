import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { LeadingFlowsPage } from '@/features/daily/leading-flows-page'

export const Route = createFileRoute('/daily/leading-flows')({
  component: () => (
    <Page title='Leading flows'>
      <LeadingFlowsPage />
    </Page>
  ),
})
