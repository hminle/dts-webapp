import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/fiscal-year')({
  component: () => <PagePlaceholder title='Fiscal year' phase={5} />,
})
