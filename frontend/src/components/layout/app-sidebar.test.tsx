import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  createMemoryHistory,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { routeTree } from '@/routeTree.gen'

function renderAt(path: string) {
  const router = createRouter({
    routeTree,
    history: createMemoryHistory({ initialEntries: [path] }),
  })
  render(
    <QueryClientProvider client={new QueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}

describe('AppSidebar', () => {
  it('lists every analysis page and the data pages', async () => {
    renderAt('/')

    for (const name of [
      'Overview',
      'Fiscal year',
      'Weekly comparison',
      'Data status',
      'Methodology',
    ]) {
      expect(await screen.findByRole('link', { name })).toBeTruthy()
    }
    expect(screen.getByRole('button', { name: 'Daily' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Year over year' })).toBeTruthy()
  })

  it('opens the year-over-year group to reveal its pages', async () => {
    renderAt('/')

    await userEvent.click(
      await screen.findByRole('button', { name: 'Year over year' })
    )

    const link = screen.getByRole('link', { name: 'Category comparison' })
    expect(link.getAttribute('href')).toBe('/yoy/categories')
  })
})
