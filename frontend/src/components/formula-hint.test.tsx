import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { FORMULAS } from '@/features/methodology/formulas'
import { FormulaHint } from './formula-hint'

function renderHint() {
  const rootRoute = createRootRoute()
  const routes = [
    createRoute({
      getParentRoute: () => rootRoute,
      path: '/',
      component: () => <FormulaHint id='net-transfers' />,
    }),
    createRoute({ getParentRoute: () => rootRoute, path: '/methodology' }),
  ]
  const router = createRouter({
    routeTree: rootRoute.addChildren(routes),
    history: createMemoryHistory({ initialEntries: ['/'] }),
  })
  render(<RouterProvider router={router} />)
}

describe('FormulaHint', () => {
  it('opens the formula summary with a link to its Methodology section', async () => {
    renderHint()

    const button = await screen.findByRole('button', {
      name: 'Net transfers: how is this calculated?',
    })
    fireEvent.click(button)

    expect(
      await screen.findByText(FORMULAS['net-transfers'].summary)
    ).toBeTruthy()
    expect(
      screen.getByText('Net transfers = total withdrawals − total deposits')
    ).toBeTruthy()
    const link = screen.getByRole('link', { name: 'Read the full explanation' })
    expect(link.getAttribute('href')).toMatch(/\/methodology#net-transfers$/)

    fireEvent.keyDown(document.activeElement ?? document.body, {
      key: 'Escape',
    })
    await waitFor(() =>
      expect(screen.queryByText(FORMULAS['net-transfers'].summary)).toBeNull()
    )
  })
})
