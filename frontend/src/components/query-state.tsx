import type { ReactNode } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { CircleAlert } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'

type QueryStateProps<T> = {
  query: UseQueryResult<T>
  children: (data: T) => ReactNode
  /** Height of the loading placeholder, as a Tailwind class. */
  skeletonClassName?: string
}

/**
 * One rendering of loading / error / data for every query on a page. The error
 * text is the backend's `detail` when it sent one (see `errorMessage`), so a
 * date with no statement says so instead of leaving the page blank.
 */
export function QueryState<T>({
  query,
  children,
  skeletonClassName = 'h-32',
}: QueryStateProps<T>) {
  if (query.isPending) {
    return <Skeleton className={`w-full ${skeletonClassName}`} />
  }
  if (query.isError) {
    return (
      <Alert variant='destructive'>
        <CircleAlert />
        <AlertDescription>{query.error.message}</AlertDescription>
      </Alert>
    )
  }
  return <>{children(query.data)}</>
}
