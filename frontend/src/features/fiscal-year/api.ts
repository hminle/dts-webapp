import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { api, throwApiError } from '@/lib/api/client'
import type { components } from '@/lib/api/schema'

export type TreasuryDataPage = components['schemas']['TreasuryDataList']

export type FiscalYearQuery = {
  fiscalYear: number
  /** A table key, or `'all'` for every table. */
  dataSource: string
  page: number
  pageSize: number
}

export function useFiscalYearData(query: FiscalYearQuery | null) {
  return useQuery({
    queryKey: ['fiscal-year', 'data', query],
    enabled: query !== null,
    // Keep the current page on screen while the next one loads.
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const { fiscalYear, dataSource, page, pageSize } = query!
      const { data, error, response } = await api.GET('/api/v1/data', {
        params: {
          query: {
            fiscal_year: fiscalYear,
            data_source: dataSource === 'all' ? undefined : dataSource,
            page,
            page_size: pageSize,
          },
        },
      })
      if (error) throwApiError(error, response, `No data for FY ${fiscalYear}`)
      return data
    },
  })
}
