import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/weekly')({
  component: () => <PagePlaceholder title='Weekly comparison' phase={6} />,
})
