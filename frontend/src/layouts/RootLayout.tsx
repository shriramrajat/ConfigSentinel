/**
 * src/layouts/RootLayout.tsx
 *
 * Root layout wrapper used by React Router's Outlet mechanism.
 *
 * Provides the consistent shell around all pages:
 *   - AppHeader — product identity + backend status
 *   - Main content area — routes render here via <Outlet />
 *   - AppFooter — product/version information
 *
 * Do not add business logic here — this is purely structural.
 */

import { Outlet } from 'react-router-dom'
import { AppHeader } from './AppHeader'
import { AppFooter } from './AppFooter'

export function RootLayout() {
  return (
    <div
      style={{
        minHeight: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--cs-bg-base)',
        color: 'var(--cs-text-primary)',
        fontFamily: 'var(--cs-font-sans)',
      }}
    >
      <AppHeader />

      {/* Page content */}
      <main style={{ flex: 1 }}>
        <Outlet />
      </main>

      <AppFooter />
    </div>
  )
}
