import { useQuery } from '@tanstack/react-query'
import { api, throwApiError } from '@/lib/api/client'
import type { components } from '@/lib/api/schema'

export type DatabaseStats = components['schemas']['DatabaseStats']
export type BuildInfo = components['schemas']['BuildInfo']

export function useStats() {
  return useQuery({
    queryKey: ['meta', 'stats'],
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/meta/stats')
      if (error) throwApiError(error, response, 'Could not load statistics')
      return data
    },
  })
}

export function useRecordCounts() {
  return useQuery({
    queryKey: ['meta', 'record-counts'],
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/meta/record-counts')
      if (error) throwApiError(error, response, 'Could not load record counts')
      return data
    },
  })
}

export function useRecordCountsByYear() {
  return useQuery({
    queryKey: ['meta', 'record-counts-by-year'],
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/meta/record-counts-by-year')
      if (error) throwApiError(error, response, 'Could not load yearly counts')
      return data
    },
  })
}

export function useBuildInfo() {
  return useQuery({
    queryKey: ['meta', 'build'],
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/meta/build')
      if (error) throwApiError(error, response, 'Could not load data status')
      return data
    },
  })
}
