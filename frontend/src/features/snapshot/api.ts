import { useQuery } from '@tanstack/react-query'
import type { AnchorWeekday } from '@/components/anchor-weekday-select'
import { api, throwApiError } from '@/lib/api/client'
import type { components } from '@/lib/api/schema'

export type WeeklySnapshot = components['schemas']['WeeklySnapshotResponse']
export type SnapshotFigure = components['schemas']['SnapshotFigure']

export function useWeeklySnapshot(anchor: AnchorWeekday, asOf: string | null) {
  return useQuery({
    queryKey: ['snapshot', 'weekly', anchor, asOf],
    queryFn: async () => {
      const { data, error, response } = await api.GET(
        '/api/v1/snapshot/weekly',
        {
          params: {
            query: { anchor_weekday: anchor, ...(asOf ? { as_of: asOf } : {}) },
          },
        }
      )
      if (error)
        throwApiError(error, response, 'Could not load the weekly snapshot')
      return data
    },
  })
}
