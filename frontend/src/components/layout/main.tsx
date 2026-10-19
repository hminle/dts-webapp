import { cn } from '@/lib/utils'

type MainProps = React.HTMLAttributes<HTMLDivElement> & {
  fixed?: boolean
  fluid?: boolean
  ref?: React.Ref<HTMLDivElement>
}

export function Main({ fixed, className, fluid, ...props }: MainProps) {
  // A div, not <main>: SidebarInset already renders the page's <main>, and a
  // second one nested inside it is an accessibility error.
  return (
    <div
      data-layout={fixed ? 'fixed' : 'auto'}
      className={cn(
        'px-4 py-6',

        // If layout is fixed, make the main container flex and grow
        fixed && 'flex grow flex-col overflow-hidden',

        // If layout is not fluid, set the max-width
        !fluid &&
          '@7xl/content:mx-auto @7xl/content:w-full @7xl/content:max-w-7xl',
        className
      )}
      {...props}
    />
  )
}
