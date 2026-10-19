import { createFileRoute } from '@tanstack/react-router'
import { PagePlaceholder } from '@/components/page-placeholder'

export const Route = createFileRoute('/methodology')({
  component: () => <PagePlaceholder title='Methodology' phase={7} />,
})
