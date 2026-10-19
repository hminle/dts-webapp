import type { ReactNode } from 'react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'

/** The shell every route renders: sticky header with the title, then content. */
export function Page({ title, children }: { title: string; children: ReactNode }) {
  return (
    <>
      <Header fixed>
        <h1 className='text-base font-medium'>{title}</h1>
      </Header>
      <Main>{children}</Main>
    </>
  )
}
