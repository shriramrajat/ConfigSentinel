/**
 * src/layouts/AppFooter.tsx
 *
 * Application footer — product/version information.
 *
 * Displays:
 *   - Product name and short descriptor
 *   - Backend version (from useVersion, when available)
 *   - Supported vendor statement (factual, from docs/FRONTEND.md)
 *
 * Rules:
 *   - No invented certifications or compliance claims
 *   - No decorative elements
 *   - Only factual, repository-grounded content
 */

import { useVersion } from '../hooks/useVersion'

export function AppFooter() {
  const { data: version } = useVersion()

  return (
    <footer
      style={{
        backgroundColor: 'var(--cs-bg-surface)',
        borderTop: '1px solid var(--cs-border-muted)',
        padding: '1rem 1.5rem',
      }}
    >
      <div
        style={{
          maxWidth: 'var(--cs-content-max)',
          margin: '0 auto',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.5rem',
        }}
      >
        {/* Left — product name + descriptor */}
        <p
          style={{
            margin: 0,
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.75rem',
            color: 'var(--cs-text-muted)',
          }}
        >
          <span style={{ color: 'var(--cs-text-secondary)', fontWeight: 500 }}>
            ConfigSentinel
          </span>
          {version && (
            <span
              style={{ fontFamily: 'var(--cs-font-mono)', marginLeft: '0.375rem' }}
            >
              v{version.version}
            </span>
          )}
          {' '}— Deterministic network configuration security auditing.
        </p>

        {/* Right — vendor support statement */}
        <p
          style={{
            margin: 0,
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.75rem',
            color: 'var(--cs-text-muted)',
          }}
        >
          Supports Cisco IOS/IOS-XE, Juniper JunOS, Arista EOS, FortiOS, and PAN-OS.
        </p>
      </div>
    </footer>
  )
}
