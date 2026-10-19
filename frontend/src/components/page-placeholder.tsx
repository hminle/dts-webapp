import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'

type PagePlaceholderProps = {
  title: string
  phase: number
}

export function PagePlaceholder({ title, phase }: PagePlaceholderProps) {
  return (
    <>
      <Header fixed>
        <h1 className='text-base font-medium'>{title}</h1>
      </Header>
      <Main>
        <p className='text-sm text-muted-foreground'>Coming in Phase {phase}.</p>
      </Main>
    </>
  )
}
