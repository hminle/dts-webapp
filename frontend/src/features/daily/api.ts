import { useQuery } from '@tanstack/react-query'
import { api, throwApiError } from '@/lib/api/client'
import type { components } from '@/lib/api/schema'

export type TreasuryRow = components['schemas']['TreasuryDataResponse']
export type DailyNetTransfer = components['schemas']['DailyNetTransfer']

/** Raw rows of one table for one date; disabled until a date is chosen. */
export function useDataByDate(date: string | null, dataSource: string) {
  return useQuery({
    queryKey: ['daily', 'by-date', date, dataSource],
    enabled: !!date,
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/data/date/{date}', {
        params: { path: { date: date! }, query: { data_source: dataSource } },
      })
      if (error) throwApiError(error, response, `No data found for ${date}`)
      return data
    },
  })
}

export function useNetTransfersForDate(date: string | null) {
  return useQuery({
    queryKey: ['daily', 'net-transfers', 'date', date],
    enabled: !!date,
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/net-transfers/date/{date}', {
        params: { path: { date: date! } },
      })
      if (error) throwApiError(error, response, 'Net transfers are not available')
      return data
    },
  })
}

export function useNetTransfersForFiscalYear(fiscalYear: number | null) {
  return useQuery({
    queryKey: ['daily', 'net-transfers', 'fiscal-year', fiscalYear],
    enabled: fiscalYear !== null,
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/net-transfers/fiscal-year/{fiscal_year}',
        { params: { path: { fiscal_year: fiscalYear! } } }
      )
      if (error) throwApiError(error, response, `No data for FY ${fiscalYear}`)
      return data
    },
  })
}

export type RollingAverage = components['schemas']['RollingAverageResponse']
export type RollingMetric = RollingAverage['metric']

/** A 10-statement rolling average of one daily amount, from `startDate`. */
export function useRollingAverage(metric: RollingMetric, startDate: string) {
  return useQuery({
    queryKey: ['rolling', metric, startDate],
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/rolling/daily', {
        params: { query: { metric, window: 10, start_date: startDate } },
      })
      if (error)
        throwApiError(error, response, 'Could not load the rolling average')
      return data
    },
  })
}
