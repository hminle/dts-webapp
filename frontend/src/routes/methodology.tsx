import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { MethodologyPage } from '@/features/methodology/methodology-page'

export const Route = createFileRoute('/methodology')({
  component: () => (
    <Page title='Methodology'>
      <MethodologyPage />
    </Page>
  ),
})
