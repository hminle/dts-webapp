import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/yoy/net-transfers')({
  component: () => <PagePlaceholder title='Net transfers year over year' phase={6} />,
})
