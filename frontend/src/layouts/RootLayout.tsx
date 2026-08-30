/**
 * src/layouts/RootLayout.tsx
 *
 * Root layout wrapper used by React Router's Outlet mechanism.
 *
 * Provides the consistent shell around all pages:
 *  - Top navigation bar (minimal in this phase)
 *  - Main content area
 *  - Footer
 *
 * Rohan and Matin: extend this layout as the UI design matures.
 * Do not add business logic here — this is purely structural.
 */

import { Outlet } from 'react-router-dom'

export function RootLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-950 text-gray-100">
      {/* Navigation */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center">
          <span className="text-sm font-semibold tracking-wide text-blue-400">
            ConfigSentinel
          </span>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-10 flex items-center">
          <p className="text-xs text-gray-500">
            ConfigSentinel — Deterministic network configuration security auditing.
          </p>
        </div>
      </footer>
    </div>
  )
}
