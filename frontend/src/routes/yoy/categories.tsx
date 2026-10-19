import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/yoy/categories')({
  component: () => <PagePlaceholder title='Category comparison' phase={6} />,
})
