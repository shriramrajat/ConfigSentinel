/**
 * src/pages/Home.tsx
 *
 * Landing page for ConfigSentinel.
 *
 * This is intentionally minimal — it communicates what the product is
 * and confirms the frontend foundation is operational. The complete
 * dashboard, scanner form, and results UI are built in subsequent phases.
 *
 * For Rohan and Matin:
 *  - Replace this page with the actual dashboard in the dashboard feature branch.
 *  - Do not add business logic to this file.
 *  - The scanner form belongs in its own page component (e.g. pages/Audit.tsx).
 */

import { useVersion } from '../hooks/useVersion'

export function Home() {
  const { data: version, isLoading, isError } = useVersion()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      {/* Hero */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight text-gray-100">
          ConfigSentinel
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto">
          Network Configuration Security &amp; Compliance
        </p>
        <p className="text-sm text-gray-500 max-w-xl mx-auto">
          Deterministic multi-vendor compliance auditing for Cisco IOS/IOS-XE
          and Juniper JunOS. No AI — every result is reproducible and traceable.
        </p>
      </div>

      {/* Backend connection status */}
      <div className="mt-12 flex justify-center">
        <div className="rounded-lg border border-gray-800 bg-gray-900 px-6 py-4 text-sm space-y-1 min-w-64">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">
            Backend Status
          </p>
          {isLoading && (
            <p className="text-gray-500">Connecting to backend…</p>
          )}
          {isError && (
            <p className="text-red-400">
              Cannot reach backend. Ensure the ConfigSentinel API is running.
            </p>
          )}
          {version && (
            <div className="space-y-0.5">
              <p className="text-green-400">● Connected</p>
              <p className="text-gray-400">
                {version.product}{' '}
                <span className="text-gray-500">v{version.version}</span>
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Foundation status notice */}
      <div className="mt-12 text-center">
        <p className="text-xs text-gray-600">
          Frontend foundation phase — scanner UI coming in the next phase.
        </p>
      </div>
    </div>
  )
}
