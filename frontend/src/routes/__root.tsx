import { createRootRoute, Outlet } from '@tanstack/react-router'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AppSidebar } from '@/components/layout/app-sidebar'

function RootError({ error }: { error: Error }) {
  return (
    <div className='flex min-h-svh flex-col items-center justify-center gap-3 p-8 text-center'>
      <h1 className='text-lg font-semibold'>Something broke</h1>
      <p className='max-w-prose text-sm text-muted-foreground'>
        {error.message}
      </p>
      <button
        className='rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-accent'
        onClick={() => window.location.reload()}
      >
        Reload
      </button>
    </div>
  )
}

function NotFound() {
  return (
    <div className='flex min-h-svh flex-col items-center justify-center gap-2 p-8 text-center'>
      <h1 className='text-lg font-semibold'>Page not found</h1>
      <a className='text-sm text-muted-foreground underline' href='/'>
        Back to overview
      </a>
    </div>
  )
}

export const Route = createRootRoute({
  errorComponent: RootError,
  notFoundComponent: NotFound,
  component: () => (
    // The sidebar renders tooltips on its collapsed icon rail, and this Tooltip
    // is a bare Radix root — without a provider at the app root it throws on
    // first render.
    <TooltipProvider>
      <SidebarProvider>
        <AppSidebar />
        {/* min-w-0: as a flex item next to the sidebar this defaults to
            min-width:auto, so a page holding something wider than the viewport
            — a wide data table — widens the whole shell instead of scrolling
            inside its own box. */}
        <SidebarInset className='min-w-0'>
          <Outlet />
        </SidebarInset>
        <Toaster />
      </SidebarProvider>
    </TooltipProvider>
  ),
})
