import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/daily/net-transfers')({
  component: () => <PagePlaceholder title='Daily net transfers' phase={5} />,
})
