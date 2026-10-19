import { Page } from '@/components/page'

type PagePlaceholderProps = {
  title: string
  phase: number
}

export function PagePlaceholder({ title, phase }: PagePlaceholderProps) {
  return (
    <Page title={title}>
      <p className='text-sm text-muted-foreground'>Coming in Phase {phase}.</p>
    </Page>
  )
}
