/**
 * src/hooks/useAudit.ts
 *
 * React Query mutation hook for running a ConfigSentinel compliance audit.
 *
 * Usage:
 *   const { mutate, data, isPending, isError, error } = useAudit()
 *   mutate({ config_text: '...', source_name: 'my-router.conf' })
 *
 * The hook encapsulates all server-state concerns:
 *  - Calling the API function (auditConfig from src/api/configsentinel.ts)
 *  - Tracking loading, success, and error state
 *  - Exposing typed result data
 *
 * Components that use this hook should handle:
 *  - isPending  → loading state
 *  - isSuccess  → show results
 *  - isError    → show error message (use error.message, safe for display)
 *  - data === undefined after reset → empty state
 */

import { useMutation } from '@tanstack/react-query'
import { auditConfig } from '../api/configsentinel'
import { ApiError } from '../api/client'
import type { AuditRequest, AuditResponse } from '../types/api'

export interface UseAuditResult {
  mutate: (request: AuditRequest) => void
  mutateAsync: (request: AuditRequest) => Promise<AuditResponse>
  data: AuditResponse | undefined
  isPending: boolean
  isSuccess: boolean
  isError: boolean
  /** ApiError when isError is true. Access .message for UI display, .code for logic. */
  error: ApiError | null
  reset: () => void
}

/**
 * React Query mutation hook for the POST /api/v1/audit endpoint.
 *
 * Audit is a mutation (not a query) because it has side effects on the
 * backend (parser state, etc.) and is user-initiated, not auto-fetched.
 */
export function useAudit(): UseAuditResult {
  const mutation = useMutation<AuditResponse, ApiError, AuditRequest>({
    mutationFn: auditConfig,
  })

  return {
    mutate: mutation.mutate,
    mutateAsync: mutation.mutateAsync,
    data: mutation.data,
    isPending: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error,
    reset: mutation.reset,
  }
}
