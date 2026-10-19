import { createFileRoute } from '@tanstack/react-router'
import { Page } from '@/components/page'
import { CategoryComparisonPage } from '@/features/yoy/category-comparison-page'

export const Route = createFileRoute('/yoy/categories')({
  component: () => (
    <Page title='Category comparison'>
      <CategoryComparisonPage />
    </Page>
  ),
})
