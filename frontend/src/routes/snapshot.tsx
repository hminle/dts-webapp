import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { SnapshotPage } from '@/features/snapshot/snapshot-page'

export const Route = createFileRoute('/snapshot')({
  component: () => (
    <Page title='Weekly snapshot'>
      <SnapshotPage />
    </Page>
  ),
})
