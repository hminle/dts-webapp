import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { SingleDatePage } from '@/features/daily/single-date-page'

export const Route = createFileRoute('/daily/single-date')({
  component: () => (
    <Page title='Single date'>
      <SingleDatePage />
    </Page>
  ),
})
