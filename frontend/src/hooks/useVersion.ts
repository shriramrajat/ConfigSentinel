/**
 * src/hooks/useVersion.ts
 *
 * React Query hook to fetch backend version information.
 *
 * Usage:
 *   const { data, isLoading, isError } = useVersion()
 *   // data?.version → "0.1.0"
 *   // data?.product → "ConfigSentinel"
 */

import { useQuery } from '@tanstack/react-query'
import { getVersion } from '../api/configsentinel'
import type { VersionResponse } from '../types/api'

/** Query key for version — stable, string-based. */
export const VERSION_QUERY_KEY = ['version'] as const

/**
 * Fetch backend product version.
 * Data is cached for the session; re-fetched on window focus.
 */
export function useVersion() {
  return useQuery<VersionResponse, Error>({
    queryKey: VERSION_QUERY_KEY,
    queryFn: getVersion,
    // Version rarely changes during a session. Keep it cached.
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
