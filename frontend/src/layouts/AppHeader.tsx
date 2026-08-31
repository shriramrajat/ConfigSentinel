/**
 * src/layouts/AppHeader.tsx
 *
 * Application header — product identity and backend connectivity.
 *
 * Displays:
 *   - Product name (ConfigSentinel) with a shield icon
 *   - Product descriptor
 *   - Backend connectivity status (from useVersion)
 *   - API version when connected
 *
 * Rules:
 *   - No navigation links (single-page audit workflow)
 *   - Status reflects real API reachability via useVersion — no fake states
 *   - No security scores, ratings, or invented metrics
 */

import { useVersion } from '../hooks/useVersion'

export function AppHeader() {
  const { data: version, isLoading, isError } = useVersion()

  return (
    <header
      style={{
        height: 'var(--cs-header-h)',
        backgroundColor: 'var(--cs-bg-surface)',
        borderBottom: '1px solid var(--cs-border)',
      }}
    >
      <div
        style={{
          maxWidth: 'var(--cs-content-max)',
          margin: '0 auto',
          padding: '0 1.5rem',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
        }}
      >
        {/* Left — product identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          {/* Shield icon */}
          <svg
            aria-hidden="true"
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ flexShrink: 0 }}
          >
            <path
              d="M10 1.5L3 4.5V9.5C3 13.5 6 17 10 18.5C14 17 17 13.5 17 9.5V4.5L10 1.5Z"
              stroke="var(--cs-accent)"
              strokeWidth="1.4"
              strokeLinejoin="round"
              fill="var(--cs-accent-subtle)"
            />
            <path
              d="M7.5 10L9.5 12L12.5 8.5"
              stroke="var(--cs-accent)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>

          <div>
            <span
              style={{
                fontFamily: 'var(--cs-font-sans)',
                fontWeight: 700,
                fontSize: '0.9375rem',
                color: 'var(--cs-text-primary)',
                letterSpacing: '-0.01em',
              }}
            >
              ConfigSentinel
            </span>
            {/* Descriptor — only visible on wider screens via CSS */}
            <span
              className="cs-header-descriptor"
              style={{
                fontFamily: 'var(--cs-font-sans)',
                fontWeight: 400,
                fontSize: '0.75rem',
                color: 'var(--cs-text-muted)',
                marginLeft: '0.5rem',
              }}
            >
              Network Configuration Auditor
            </span>
          </div>
        </div>

        {/* Right — backend status */}
        <BackendStatus isLoading={isLoading} isError={isError} version={version?.version} />
      </div>
    </header>
  )
}

// ---------------------------------------------------------------------------
// BackendStatus — internal sub-component
// ---------------------------------------------------------------------------

interface BackendStatusProps {
  isLoading: boolean
  isError: boolean
  version?: string
}

function BackendStatus({ isLoading, isError, version }: BackendStatusProps) {
  if (isLoading) {
    return (
      <div
        role="status"
        aria-label="Connecting to backend"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
          fontSize: '0.75rem',
          color: 'var(--cs-text-muted)',
          fontFamily: 'var(--cs-font-sans)',
        }}
      >
        {/* Pulsing grey dot */}
        <span
          className="cs-dot-pulse"
          aria-hidden="true"
          style={{
            display: 'inline-block',
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: 'var(--cs-text-muted)',
            flexShrink: 0,
          }}
        />
        <span>Connecting…</span>
      </div>
    )
  }

  if (isError) {
    return (
      <div
        role="status"
        aria-label="Backend unavailable"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
          fontSize: '0.75rem',
          color: 'var(--cs-fail)',
          fontFamily: 'var(--cs-font-sans)',
        }}
      >
        {/* Red dot */}
        <span
          aria-hidden="true"
          style={{
            display: 'inline-block',
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: 'var(--cs-fail)',
            flexShrink: 0,
          }}
        />
        <span>Backend unavailable</span>
      </div>
    )
  }

  // Connected
  return (
    <div
      role="status"
      aria-label={`Backend connected, version ${version ?? ''}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.375rem',
        fontSize: '0.75rem',
        color: 'var(--cs-text-muted)',
        fontFamily: 'var(--cs-font-sans)',
      }}
    >
      {/* Green dot */}
      <span
        aria-hidden="true"
        style={{
          display: 'inline-block',
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: 'var(--cs-pass)',
          flexShrink: 0,
        }}
      />
      {version && (
        <span>
          <span style={{ color: 'var(--cs-text-secondary)' }}>API</span>
          {' '}
          <span
            style={{
              fontFamily: 'var(--cs-font-mono)',
              color: 'var(--cs-text-muted)',
              fontSize: '0.6875rem',
            }}
          >
            v{version}
          </span>
        </span>
      )}
    </div>
  )
}
