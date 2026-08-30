/**
 * src/api/client.ts
 *
 * Low-level HTTP client for ConfigSentinel API communication.
 *
 * Rules:
 *  - API base URL is read from VITE_API_BASE_URL (never hardcoded production).
 *  - All responses are typed.
 *  - Non-2xx responses throw ApiError with the backend error structure.
 *  - No raw fetch() should be used outside this file or configsentinel.ts.
 *  - No business logic or compliance logic lives here.
 */

import type { ErrorResponse } from '../types/api'

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/**
 * Backend base URL.
 * Set VITE_API_BASE_URL in your .env file.
 * Falls back to http://localhost:8000 for local development only.
 */
const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

/**
 * Typed error thrown when the backend returns a non-2xx response.
 *
 * `code` is the machine-readable backend error code (e.g. "INVALID_INPUT").
 * `message` is safe to display in the UI.
 * `httpStatus` is the HTTP status code.
 */
export class ApiError extends Error {
  readonly code: string
  readonly httpStatus: number

  constructor(code: string, message: string, httpStatus: number) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.httpStatus = httpStatus
  }
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

/**
 * Perform a fetch request against the ConfigSentinel backend.
 *
 * On non-2xx responses, attempts to parse the backend ErrorResponse envelope
 * and throws ApiError. If the response is not parseable JSON, throws a
 * generic ApiError with INTERNAL_ERROR.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${path}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    // Attempt to extract the backend error envelope.
    let errorPayload: ErrorResponse | null = null
    try {
      errorPayload = (await response.json()) as ErrorResponse
    } catch {
      // Response body was not valid JSON.
    }

    const code = errorPayload?.error?.code ?? 'INTERNAL_ERROR'
    const message =
      errorPayload?.error?.message ??
      `Request failed with status ${response.status}.`

    throw new ApiError(code, message, response.status)
  }

  return response.json() as Promise<T>
}
