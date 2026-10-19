import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/yoy/withdrawals')({
  component: () => <PagePlaceholder title='Withdrawals year over year' phase={6} />,
})
