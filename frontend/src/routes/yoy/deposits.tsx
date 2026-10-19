import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/yoy/deposits')({
  component: () => <PagePlaceholder title='Deposits year over year' phase={6} />,
})
