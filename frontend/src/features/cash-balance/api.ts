import { useQuery } from '@tanstack/react-query'
import { api, throwApiError } from '@/lib/api/client'
import type { components } from '@/lib/api/schema'

export type CashBalance = components['schemas']['CashBalanceResponse']
export type CashBalancePoint = components['schemas']['CashBalancePoint']

/** The TGA closing balance from `startDate`; null asks for the API's default. */
export function useCashBalance(startDate: string | null) {
  return useQuery({
    queryKey: ['cash-balance', startDate],
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/cash-balance/daily',
        { params: { query: startDate ? { start_date: startDate } : {} } }
      )
      if (error)
        throwApiError(error, response, 'Could not load the cash balance')
      return data
    },
  })
}
