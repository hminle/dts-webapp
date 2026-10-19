import { describe, expect, it } from 'vitest'
import { ApiError } from '@/lib/api/client'
import { queryClient } from './query-client'

const retry = queryClient.getDefaultOptions().queries!.retry as (
  failureCount: number,
  error: Error
) => boolean

describe('query retry policy', () => {
  it('does not retry an answer like "no data for that date"', () => {
    expect(retry(0, new ApiError('No data found', 404))).toBe(false)
  })

  it('retries a server failure or a network error once', () => {
    expect(retry(0, new ApiError('Data is not loaded yet', 503))).toBe(true)
    expect(retry(0, new TypeError('Failed to fetch'))).toBe(true)
    expect(retry(1, new TypeError('Failed to fetch'))).toBe(false)
  })
})
