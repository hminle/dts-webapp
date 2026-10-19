import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { DataStatusPage } from '@/features/data-status/data-status-page'

export const Route = createFileRoute('/data-status')({
  component: () => (
    <Page title='Data status'>
      <DataStatusPage />
    </Page>
  ),
})
