import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { WeeklyPage } from '@/features/weekly/weekly-page'

export const Route = createFileRoute('/weekly')({
  component: () => (
    <Page title='Weekly comparison'>
      <WeeklyPage />
    </Page>
  ),
})
