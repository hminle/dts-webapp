import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/data-status')({
  component: () => <PagePlaceholder title='Data status' phase={5} />,
})
