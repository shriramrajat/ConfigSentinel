/**
 * src/lib/queryClient.ts
 *
 * Shared React Query client instance.
 *
 * Imported by main.tsx to wrap the app in QueryClientProvider.
 * Keeping this in lib/ means tests and storybook can import the same instance.
 *
 * Default configuration:
 *  - retry: 1 (mutations) / 2 (queries) — avoids hammering the backend on
 *    transient errors without giving up immediately.
 *  - staleTime: 0 — queries are considered stale immediately by default.
 *    Override per-query when caching is appropriate (e.g. useVersion).
 *  - refetchOnWindowFocus: true — standard React Query default. Turn off
 *    per-query if needed (e.g. one-shot audits).
 */

import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 0,
    },
    mutations: {
      retry: 0,
    },
  },
})
