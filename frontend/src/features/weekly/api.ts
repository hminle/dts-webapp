import { useQuery } from '@tanstack/react-query'
import { api, throwApiError } from '@/lib/api/client'
import type { components } from '@/lib/api/schema'

export type WeeklyComparison = components['schemas']['WeeklyComparisonResponse']
export type WeeklyDataPoint = components['schemas']['WeeklyDataPoint']

export function useWeeklyComparison(
  first: number | null,
  second: number | null
) {
  return useQuery({
    queryKey: ['weekly', 'comparison', first, second],
    enabled: first !== null && second !== null && first !== second,
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/weekly/comparison',
        {
          params: {
            query: { first_fiscal_year: first!, second_fiscal_year: second! },
          },
        }
      )
      if (error)
        throwApiError(error, response, 'Could not load the weekly comparison')
      return data
    },
  })
}
