import createClient from 'openapi-fetch'
import type { paths } from './schema'

/**
 * The one place the app talks to the network. Types come from schema.d.ts,
 * generated from the backend's committed OpenAPI snapshot — a contract break
 * becomes a TypeScript error here rather than a runtime surprise.
 *
 * Spec paths already carry the `/api` prefix, so requests go to the app's own
 * origin and Vite proxies `/api` to the backend in dev. The origin is spelled
 * out because `openapi-fetch` builds a `Request`, and outside a browser (jsdom,
 * SSR) `new Request()` rejects a relative URL.
 */
const baseUrl = typeof window === 'undefined' ? '' : window.location.origin

export const api = createClient<paths>({
  baseUrl,
  // Resolve fetch per call rather than capturing it when this module loads, so
  // the implementation can be swapped at runtime (tests stub globalThis.fetch).
  fetch: (request) => globalThis.fetch(request),
})

/**
 * The message to show for a failed call. The backend writes its 422 `detail`
 * for people ("Lot 12 has 2 left on 2026-09-27"), so that wins over a generic
 * fallback; a validation error list or a network failure does not.
 */
export function errorMessage(error: unknown, fallback: string): string {
  const detail = (error as { detail?: unknown } | undefined)?.detail
  return typeof detail === 'string' ? detail : fallback
}

/** A failed call with its HTTP status, so callers can tell "no data" from "down". */
export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** Throw the call's failure as an `ApiError` carrying the backend's detail. */
export function throwApiError(
  error: unknown,
  response: Response,
  fallback: string
): never {
  throw new ApiError(errorMessage(error, fallback), response.status)
}
