import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/daily/single-date')({
  component: () => <PagePlaceholder title='Single date' phase={5} />,
})
