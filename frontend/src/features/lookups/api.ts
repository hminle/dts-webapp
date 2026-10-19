import { useQuery } from '@tanstack/react-query'
import { api, throwApiError } from '@/lib/api/client'
import type { components } from '@/lib/api/schema'

export type CategoryList = components['schemas']['CategoryListResponse']

/** Display names for table keys; the API lists keys only. */
export const DATA_SOURCE_NAMES: Record<string, string> = {
  operating_cash_balance: 'Operating Cash Balance',
  deposits_withdrawals: 'Deposits & Withdrawals',
  public_debt_transactions: 'Public Debt Transactions',
  adjustment_public_debt: 'Public Debt Adjustments',
  debt_subject_to_limit: 'Debt Subject to Limit',
  inter_agency_tax_transfers: 'Inter-Agency Tax Transfers',
  income_tax_refunds: 'Income Tax Refunds',
  federal_tax_deposits: 'Federal Tax Deposits',
  short_term_cash_investments: 'Short-Term Cash Investments',
  daily_net_transfers: 'Daily Net Transfers (derived)',
}

export function dataSourceName(key: string): string {
  return DATA_SOURCE_NAMES[key] ?? key
}

export function useFiscalYears() {
  return useQuery({
    queryKey: ['lookups', 'fiscal-years'],
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/lookups/fiscal-years')
      if (error) throwApiError(error, response, 'Could not load fiscal years')
      return data
    },
  })
}

export function useDataSources() {
  return useQuery({
    queryKey: ['lookups', 'data-sources'],
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/lookups/data-sources')
      if (error) throwApiError(error, response, 'Could not load data sources')
      return data
    },
  })
}

export function useAccountTypes(dataSource?: string) {
  return useQuery({
    queryKey: ['lookups', 'account-types', dataSource ?? null],
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/lookups/account-types', {
        params: { query: { data_source: dataSource } },
      })
      if (error) throwApiError(error, response, 'Could not load account types')
      return data
    },
  })
}

export function useCategories() {
  return useQuery({
    queryKey: ['lookups', 'categories'],
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/lookups/categories')
      if (error) throwApiError(error, response, 'Could not load categories')
      return data
    },
  })
}
