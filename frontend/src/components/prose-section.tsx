import type { ReactNode } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

/**
 * A titled card of reading text, for the methodology and legal pages. With an
 * `id`, the heading is an in-page link target that clears the sticky header.
 */
export function ProseSection({
  id,
  title,
  children,
}: {
  id?: string
  title: string
  children: ReactNode
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2 id={id} className='scroll-mt-20'>
            {title}
          </h2>
        </CardTitle>
      </CardHeader>
      <CardContent className='flex max-w-prose flex-col gap-3 text-sm text-muted-foreground [&_li]:ms-4 [&_ul]:list-disc'>
        {children}
      </CardContent>
    </Card>
  )
}

/** Stacks prose sections with the page's usual spacing. */
export function ProsePage({ children }: { children: ReactNode }) {
  return <div className='flex flex-col gap-4'>{children}</div>
}
