import { useQuery } from '@tanstack/react-query'
import { api, throwApiError } from '@/lib/api/client'
import type { components } from '@/lib/api/schema'

type Schemas = components['schemas']
export type YoYDailyDataPoint = Schemas['YoYDailyDataPoint']
export type YoYDailyComparison = Schemas['YoYDailyComparisonResponse']
export type YoYCategoryComparison = Schemas['YoYCategoryComparisonResponse']
export type MajorSpendingCategory = Schemas['MajorSpendingCategory']
export type MajorReceiptCategory = Schemas['MajorReceiptCategory']
export type MajorSpending = Schemas['MajorSpendingCategoriesResponse']
export type MajorReceipts = Schemas['MajorReceiptCategoriesResponse']
export type TBillInterest = Schemas['TBillInterestResponse']
export type IrsRefunds = Schemas['IrsRefundResponse']
export type SubcategoryBreakdown = Schemas['SubcategoryBreakdown']
export type TBillInterestComponent = Schemas['TBillInterestComponent']
export type IrsRefundComponent = Schemas['IrsRefundComponent']

export type ComparisonMode = 'fiscal_day' | 'calendar_date'
export type YoYMetric = 'total_deposits' | 'total_withdrawals' | 'net_flow'

export type YearPair = {
  currentFiscalYear: number
  previousFiscalYear: number
  comparisonMode: ComparisonMode
}

/** The query fields every category endpoint shares. */
function yearQuery({
  currentFiscalYear,
  previousFiscalYear,
  comparisonMode,
}: YearPair) {
  return {
    current_fiscal_year: currentFiscalYear,
    previous_fiscal_year: previousFiscalYear,
    comparison_mode: comparisonMode,
  }
}

const distinct = (p: YearPair) => p.currentFiscalYear !== p.previousFiscalYear

export function useYoYDailyComparison(pair: YearPair, metric: YoYMetric) {
  return useQuery({
    queryKey: ['yoy', 'daily', pair, metric],
    enabled: distinct(pair),
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/yoy/daily-comparison',
        {
          params: { query: { ...yearQuery(pair), metric } },
        }
      )
      if (error) throwApiError(error, response, 'Could not load the comparison')
      return data
    },
  })
}

export function useMajorSpending(pair: YearPair) {
  return useQuery({
    queryKey: ['yoy', 'major-spending', pair],
    enabled: distinct(pair),
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/categories/major-spending',
        {
          params: { query: yearQuery(pair) },
        }
      )
      if (error)
        throwApiError(error, response, 'Could not load spending categories')
      return data
    },
  })
}

export function useMajorReceipts(pair: YearPair) {
  return useQuery({
    queryKey: ['yoy', 'major-receipts', pair],
    enabled: distinct(pair),
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/categories/major-receipts',
        {
          params: { query: yearQuery(pair) },
        }
      )
      if (error)
        throwApiError(error, response, 'Could not load receipt categories')
      return data
    },
  })
}

export function useTBillInterest(pair: YearPair) {
  return useQuery({
    queryKey: ['yoy', 'tbill-interest', pair],
    enabled: distinct(pair),
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/categories/tbill-interest',
        {
          params: { query: yearQuery(pair) },
        }
      )
      if (error)
        throwApiError(error, response, 'Could not load T-bill interest')
      return data
    },
  })
}

export function useIrsTaxRefunds(pair: YearPair) {
  return useQuery({
    queryKey: ['yoy', 'irs-tax-refunds', pair],
    enabled: distinct(pair),
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/categories/irs-tax-refunds',
        {
          params: { query: yearQuery(pair) },
        }
      )
      if (error)
        throwApiError(error, response, 'Could not load IRS tax refunds')
      return data
    },
  })
}

export function useCategoryDailyYoY(
  pair: YearPair,
  category: { name: string; type: string } | null
) {
  return useQuery({
    queryKey: ['yoy', 'category-daily', pair, category],
    enabled: category !== null && distinct(pair),
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/categories/daily-yoy',
        {
          params: {
            query: {
              ...yearQuery(pair),
              category_name: category!.name,
              category_type: category!.type,
            },
          },
        }
      )
      if (error)
        throwApiError(error, response, 'Could not load the daily change')
      return data
    },
  })
}

export type CategoryComparisonQuery = YearPair & {
  categories: string[]
  transactionType?: 'Deposits' | 'Withdrawals'
}

export function useYoYCategoryComparison(
  query: CategoryComparisonQuery | null
) {
  return useQuery({
    queryKey: ['yoy', 'category-comparison', query],
    enabled: query !== null && query.categories.length > 0 && distinct(query),
    queryFn: async () => {
      const q = query!
      const { data, error, response } = await api.GET(
        '/api/v1/yoy/category-comparison',
        {
          params: {
            query: {
              ...yearQuery(q),
              category_descriptions: q.categories,
              transaction_type: q.transactionType,
            },
          },
        }
      )
      if (error) throwApiError(error, response, 'Could not load the comparison')
      return data
    },
  })
}
