/**
 * src/pages/Home.tsx
 *
 * ConfigSentinel audit launchpad — the primary and only page.
 *
 * Responsibilities:
 *   1. Product introduction and capability statement
 *   2. Render AuditForm
 *   3. Drive useAudit() mutation on form submit
 *   4. Render loading / error / empty / audit-received states
 *   5. Handle reset via useAudit().reset()
 *
 * Does NOT:
 *   - Contain any compliance logic
 *   - Calculate derived metrics from API response counts
 *   - Store results beyond React Query mutation state
 *   - Invent API fields, security scores, or AI summaries
 */

import { useAudit } from '../hooks/useAudit'
import { AuditForm } from '../components/AuditForm'
import { AuditResults } from '../components/AuditResults'
import type { AuditRequest } from '../types/api'
import { ApiError } from '../api/client'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Map backend error codes to operator-friendly messages. */
function getErrorMessage(error: ApiError | null): string {
  if (!error) return 'An unexpected error occurred.'
  switch (error.code) {
    case 'INVALID_INPUT':
      return `Invalid input: ${error.message}`
    case 'VALIDATION_ERROR':
      return `Request validation error: ${error.message}`
    case 'INTERNAL_ERROR':
      return 'Backend error — please try again. If the problem persists, verify the API server is running.'
    default:
      return error.message
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function Home() {
  const { mutate, data, isPending, isSuccess, isError, error, reset } = useAudit()

  function handleSubmit(request: AuditRequest) {
    mutate(request)
  }

  return (
    <div
      style={{
        maxWidth: 'var(--cs-content-max)',
        margin: '0 auto',
        padding: '2.5rem 1.5rem 4rem',
      }}
    >

      {/* ------------------------------------------------------------------ */}
      {/* Product header                                                       */}
      {/* ------------------------------------------------------------------ */}
      <div style={{ marginBottom: '2.5rem' }}>
        <h1
          style={{
            margin: '0 0 0.5rem',
            fontFamily: 'var(--cs-font-sans)',
            fontWeight: 700,
            fontSize: '1.375rem',
            color: 'var(--cs-text-primary)',
            letterSpacing: '-0.02em',
          }}
        >
          Configuration Audit
        </h1>
        <p
          style={{
            margin: 0,
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.875rem',
            color: 'var(--cs-text-secondary)',
            lineHeight: 1.6,
            maxWidth: '44rem',
          }}
        >
          Submit a raw network device configuration for deterministic compliance
          auditing. The engine evaluates{' '}
          <strong style={{ color: 'var(--cs-text-primary)', fontWeight: 600 }}>
            5 security controls
          </strong>{' '}
          across SSH version enforcement, telnet prohibition, session timeout,
          password hashing strength, and AAA authentication policy. Every result
          is reproducible and traceable to evidence in the configuration.
        </p>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Two-column layout: form (left) + capability panel (right)           */}
      {/* On narrow screens both go full-width, stacked                       */}
      {/* ------------------------------------------------------------------ */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr)',
          gap: '2rem',
          alignItems: 'start',
        }}
        className="cs-home-grid"
      >

        {/* ---------------------------------------------------------------- */}
        {/* Left column — audit form + state outputs                          */}
        {/* ---------------------------------------------------------------- */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

          {/* Form panel */}
          <section
            className="cs-card"
            style={{ padding: '1.5rem' }}
            aria-label="Audit configuration input"
          >
            <AuditForm
              onSubmit={handleSubmit}
              isPending={isPending}
              onReset={reset}
              hasResults={isSuccess}
            />
          </section>

          {/* ── Error state ─────────────────────────────────────────────── */}
          {isError && (
            <ErrorPanel message={getErrorMessage(error)} onDismiss={reset} />
          )}

          {/* ── Loading state ───────────────────────────────────────────── */}
          {isPending && <LoadingPanel />}

          {/* ── Results received (Phase 2 — full results) ──────────────── */}
          {isSuccess && data && (
            <AuditResults data={data} />
          )}

        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Right column — capability reference panel                         */}
        {/* ---------------------------------------------------------------- */}
        <aside aria-label="Audit capabilities reference">
          <CapabilityPanel />
        </aside>

      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// ErrorPanel
// ---------------------------------------------------------------------------

interface ErrorPanelProps {
  message: string
  onDismiss: () => void
}

function ErrorPanel({ message, onDismiss }: ErrorPanelProps) {
  return (
    <div
      role="alert"
      style={{
        backgroundColor: 'var(--cs-fail-bg)',
        border: '1px solid var(--cs-fail-border)',
        borderRadius: 'var(--cs-radius-md)',
        padding: '1rem 1.25rem',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
      }}
    >
      {/* Error icon */}
      <svg
        aria-hidden="true"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ flexShrink: 0, marginTop: '0.125rem', color: 'var(--cs-fail)' }}
      >
        <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.2" />
        <path d="M8 5v3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        <circle cx="8" cy="11" r="0.7" fill="currentColor" />
      </svg>

      <div style={{ flex: 1 }}>
        <p
          style={{
            margin: '0 0 0.625rem',
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.875rem',
            color: 'var(--cs-fail)',
            fontWeight: 500,
          }}
        >
          Audit failed
        </p>
        <p
          style={{
            margin: '0 0 0.75rem',
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.8125rem',
            color: 'var(--cs-text-secondary)',
            lineHeight: 1.55,
          }}
        >
          {message}
        </p>
        <button
          type="button"
          className="cs-btn-ghost"
          onClick={onDismiss}
          style={{ fontSize: '0.8125rem', padding: '0.375rem 0.75rem' }}
        >
          Dismiss
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// LoadingPanel
// ---------------------------------------------------------------------------

function LoadingPanel() {
  return (
    <div
      aria-live="polite"
      aria-label="Audit in progress"
      style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}
    >
      {/* Label */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0 0.25rem',
        }}
      >
        <span
          className="cs-spinner"
          aria-hidden="true"
          style={{
            color: 'var(--cs-accent)',
            width: '14px',
            height: '14px',
          }}
        />
        <span
          style={{
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.8125rem',
            color: 'var(--cs-text-secondary)',
          }}
        >
          Auditing configuration…
        </span>
      </div>

      {/* Skeleton rows — one per compliance control */}
      {Array.from({ length: 5 }).map((_, i) => (
        <SkeletonRow key={i} />
      ))}
    </div>
  )
}

function SkeletonRow() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.875rem 1rem',
        backgroundColor: 'var(--cs-bg-surface)',
        border: '1px solid var(--cs-border)',
        borderRadius: 'var(--cs-radius)',
      }}
    >
      {/* Control ID skeleton */}
      <div
        className="cs-skeleton"
        style={{ width: '4.5rem', height: '0.875rem', flexShrink: 0 }}
      />
      {/* Name skeleton */}
      <div
        className="cs-skeleton"
        style={{ flex: 1, height: '0.875rem' }}
      />
      {/* Severity skeleton */}
      <div
        className="cs-skeleton"
        style={{ width: '3.5rem', height: '0.875rem', flexShrink: 0 }}
      />
      {/* Status skeleton */}
      <div
        className="cs-skeleton"
        style={{ width: '3rem', height: '1.25rem', borderRadius: '0.25rem', flexShrink: 0 }}
      />
    </div>
  )
}

// ---------------------------------------------------------------------------
// CapabilityPanel — static capability reference
// All content is grounded in the repository. No invented capabilities.
// ---------------------------------------------------------------------------

function CapabilityPanel() {
  const controls: { id: string; name: string; severity: string; sevColor: string }[] = [
    { id: 'SSH-001', name: 'SSH Protocol Version',          severity: 'HIGH',     sevColor: 'var(--cs-sev-high)' },
    { id: 'TLN-001', name: 'Telnet Must Be Disabled',       severity: 'CRITICAL', sevColor: 'var(--cs-sev-critical)' },
    { id: 'EXEC-001', name: 'VTY Idle Session Timeout',     severity: 'HIGH',     sevColor: 'var(--cs-sev-high)' },
    { id: 'PWD-001', name: 'Privileged Password Hashing',   severity: 'HIGH',     sevColor: 'var(--cs-sev-high)' },
    { id: 'AAA-001', name: 'Remote AAA Authentication',     severity: 'HIGH',     sevColor: 'var(--cs-sev-high)' },
  ]

  return (
    <div
      className="cs-card"
      style={{ padding: '1.25rem' }}
      aria-label="Controls evaluated"
    >
      {/* Header */}
      <div
        style={{
          marginBottom: '1rem',
          paddingBottom: '0.75rem',
          borderBottom: '1px solid var(--cs-border)',
        }}
      >
        <h2
          style={{
            margin: 0,
            fontFamily: 'var(--cs-font-sans)',
            fontWeight: 600,
            fontSize: '0.8125rem',
            color: 'var(--cs-text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
          }}
        >
          Active Controls
        </h2>
      </div>

      {/* Control list */}
      <ul
        style={{
          listStyle: 'none',
          margin: 0,
          padding: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: '0',
        }}
      >
        {controls.map((ctrl, idx) => (
          <li
            key={ctrl.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.625rem 0',
              borderBottom:
                idx < controls.length - 1
                  ? '1px solid var(--cs-border-muted)'
                  : 'none',
            }}
          >
            {/* Control ID */}
            <span
              style={{
                fontFamily: 'var(--cs-font-mono)',
                fontSize: '0.75rem',
                fontWeight: 500,
                color: 'var(--cs-accent)',
                minWidth: '4.5rem',
                flexShrink: 0,
              }}
            >
              {ctrl.id}
            </span>

            {/* Name */}
            <span
              style={{
                fontFamily: 'var(--cs-font-sans)',
                fontSize: '0.8125rem',
                color: 'var(--cs-text-primary)',
                flex: 1,
              }}
            >
              {ctrl.name}
            </span>

            {/* Severity indicator */}
            <span
              style={{
                fontFamily: 'var(--cs-font-sans)',
                fontSize: '0.625rem',
                fontWeight: 600,
                color: ctrl.sevColor,
                letterSpacing: '0.06em',
                flexShrink: 0,
              }}
              aria-label={`Severity: ${ctrl.severity}`}
            >
              {ctrl.severity}
            </span>
          </li>
        ))}
      </ul>

      {/* Vendor support section */}
      <div
        style={{
          marginTop: '1.25rem',
          paddingTop: '1rem',
          borderTop: '1px solid var(--cs-border)',
        }}
      >
        <p
          style={{
            margin: '0 0 0.625rem',
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.6875rem',
            fontWeight: 600,
            color: 'var(--cs-text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
          }}
        >
          Supported Vendors
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
          {['Cisco IOS / IOS-XE', 'Juniper JunOS', 'Arista EOS', 'FortiOS', 'PAN-OS'].map((v) => (
            <span
              key={v}
              style={{
                fontFamily: 'var(--cs-font-sans)',
                fontSize: '0.75rem',
                fontWeight: 500,
                color: 'var(--cs-text-primary)',
                backgroundColor: 'var(--cs-bg-elevated)',
                border: '1px solid var(--cs-border-strong)',
                borderRadius: 'var(--cs-radius-sm)',
                padding: '0.2rem 0.5rem',
              }}
            >
              {v}
            </span>
          ))}
        </div>
      </div>

      {/* Determinism note */}
      <div
        style={{
          marginTop: '1.25rem',
          padding: '0.75rem 0.875rem',
          backgroundColor: 'rgba(59, 130, 246, 0.08)',
          border: '1px solid var(--cs-accent-muted)',
          borderRadius: 'var(--cs-radius)',
          display: 'flex',
          gap: '0.625rem',
          alignItems: 'flex-start',
        }}
      >
        <svg
          aria-hidden="true"
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          style={{ flexShrink: 0, marginTop: '0.125rem', color: 'var(--cs-accent)' }}
        >
          <path
            d="M8 1.5L2.5 3.8v4.2c0 3.1 2.3 5.9 5.5 7 3.2-1.1 5.5-3.9 5.5-7V3.8L8 1.5z"
            stroke="currentColor"
            strokeWidth="1.3"
            strokeLinejoin="round"
          />
          <path d="M6 8l1.5 1.5L10.5 6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <p
          style={{
            margin: 0,
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.75rem',
            color: 'var(--cs-text-secondary)',
            lineHeight: 1.5,
          }}
        >
          <strong style={{ color: 'var(--cs-text-primary)', fontWeight: 600 }}>
            Deterministic Security Engine.
          </strong>{' '}
          Every result is reproducible and traceable to configuration evidence. Zero LLM reliance for compliance logic.
        </p>
      </div>
    </div>
  )
}
