import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { FiscalYearPage } from '@/features/fiscal-year/fiscal-year-page'

export const Route = createFileRoute('/fiscal-year')({
  component: () => (
    <Page title='Fiscal year'>
      <FiscalYearPage />
    </Page>
  ),
})
