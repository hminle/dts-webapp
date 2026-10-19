import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '@/lib/api/client'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // The data changes once per business day, so refetching sooner only
      // repeats the same answer.
      staleTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      // A 4xx ("no statement on that date") is the answer, not a glitch;
      // retrying only delays it. Network errors and 5xx get one retry.
      retry: (failureCount, error) =>
        !(error instanceof ApiError && error.status < 500) && failureCount < 1,
    },
  },
})
