import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'

export type Chapter = { id: string; title: string }

function ChapterLinks({ chapters }: { chapters: Chapter[] }) {
  return (
    <ol className='flex flex-col gap-1 text-sm'>
      {chapters.map((chapter, i) => (
        <li key={chapter.id}>
          <a
            href={`#${chapter.id}`}
            className='flex gap-2 rounded-md px-2 py-1 text-muted-foreground hover:bg-muted hover:text-foreground'
          >
            <span className='w-5 shrink-0 text-right tabular-nums'>
              {i + 1}
            </span>
            {chapter.title}
          </a>
        </li>
      ))}
    </ol>
  )
}

/**
 * The page's table of contents: a sticky column beside the text on large
 * screens, a collapsible list above it on smaller ones. Plain `#id` links let
 * the browser do the scrolling.
 */
export function MethodologyToc({
  chapters,
  className,
}: {
  chapters: Chapter[]
  className?: string
}) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <nav aria-label='On this page' className={cn('lg:hidden', className)}>
        <Collapsible open={open} onOpenChange={setOpen}>
          <CollapsibleTrigger asChild>
            <Button variant='outline' className='w-full justify-between'>
              On this page
              <ChevronDown
                data-icon='inline-end'
                className={cn('transition-transform', open && 'rotate-180')}
              />
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className='pt-2'>
            <ChapterLinks chapters={chapters} />
          </CollapsibleContent>
        </Collapsible>
      </nav>
      <nav
        aria-label='On this page'
        className={cn(
          'hidden lg:sticky lg:top-20 lg:flex lg:flex-col lg:gap-2 lg:self-start',
          className
        )}
      >
        <p className='px-2 text-sm font-medium'>On this page</p>
        <ChapterLinks chapters={chapters} />
      </nav>
    </>
  )
}
