import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  createMemoryHistory,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router'
import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { routeTree } from '@/routeTree.gen'
import { mockApi } from '@/test/api'

afterEach(() => vi.unstubAllGlobals())

function renderAt(path: string) {
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: [path] }),
  })
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}

describe('OverviewPage', () => {
  it('shows the dataset statistics and quick links', async () => {
    mockApi({
      '/api/v1/meta/stats': {
        record_count: 867348,
        earliest_date: '2005-10-03',
        latest_date: '2026-10-15',
        last_updated: '2026-10-19T01:14:38+00:00',
        account_types: [],
        fiscal_years: [2027, 2026],
        data_sources: ['deposits_withdrawals', 'operating_cash_balance'],
      },
    })

    renderAt('/')

    expect(await screen.findByText('867,348')).toBeTruthy()
    expect(screen.getByText('FY 2027')).toBeTruthy()
    expect(screen.getByText('Deposits & Withdrawals')).toBeTruthy()
    expect(screen.getByText('Oct 3, 2005 – Oct 15, 2026')).toBeTruthy()
    const weekly = screen
      .getAllByRole('link', { name: /Weekly comparison/ })
      .map((link) => link.getAttribute('href'))
    expect(weekly).toContain('/weekly')
  })

  it('shows the backend message when the data is not loaded', async () => {
    mockApi({})

    renderAt('/')

    expect(await screen.findByText(/not mocked: \/api\/v1\/meta\/stats/)).toBeTruthy()
  })
})
