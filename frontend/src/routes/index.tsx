import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { OverviewPage } from '@/features/overview/overview-page'

export const Route = createFileRoute('/')({
  component: () => (
    <Page title='Overview'>
      <OverviewPage />
    </Page>
  ),
})
