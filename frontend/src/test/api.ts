import { vi } from 'vitest'

/**
 * Stub `globalThis.fetch` (the api client resolves fetch per call) with JSON
 * bodies keyed by request pathname. Anything unmocked answers 404 with a
 * detail that names the path, so a missing mock is obvious in the failure.
 */
export function mockApi(routes: Record<string, unknown>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const request = input instanceof Request ? input : new Request(input)
    const path = new URL(request.url).pathname
    if (path in routes) return Response.json(routes[path])
    return Response.json({ detail: `not mocked: ${path}` }, { status: 404 })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}
