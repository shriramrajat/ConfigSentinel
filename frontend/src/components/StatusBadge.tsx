/**
 * src/components/StatusBadge.tsx
 *
 * Consistent visual indicator for a control's compliance status.
 * Consumes CSS design tokens to enforce the ConfigSentinel palette.
 *
 * Statuses are exhaustive to the backend API: pass, fail, needs_review, not_applicable.
 */

import type { ComplianceStatus } from '../types/api'

interface StatusBadgeProps {
  status: ComplianceStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  let label = ''
  let colorVar = ''
  let bgVar = ''
  let borderVar = ''

  switch (status) {
    case 'pass':
      label = 'PASS'
      colorVar = 'var(--cs-pass)'
      bgVar = 'var(--cs-pass-bg)'
      borderVar = 'var(--cs-pass-border)'
      break
    case 'fail':
      label = 'FAIL'
      colorVar = 'var(--cs-fail)'
      bgVar = 'var(--cs-fail-bg)'
      borderVar = 'var(--cs-fail-border)'
      break
    case 'needs_review':
      label = 'REVIEW'
      colorVar = 'var(--cs-review)'
      bgVar = 'var(--cs-review-bg)'
      borderVar = 'var(--cs-review-border)'
      break
    case 'not_applicable':
      label = 'N/A'
      colorVar = 'var(--cs-na)'
      bgVar = 'var(--cs-na-bg)'
      borderVar = 'var(--cs-na-border)'
      break
    default:
      // Fallback for unexpected API values (fails gracefully)
      label = String(status).toUpperCase()
      colorVar = 'var(--cs-text-muted)'
      bgVar = 'var(--cs-bg-subtle)'
      borderVar = 'var(--cs-border)'
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0.125rem 0.5rem',
        borderRadius: 'var(--cs-radius)',
        backgroundColor: bgVar,
        border: `1px solid ${borderVar}`,
        color: colorVar,
        fontFamily: 'var(--cs-font-sans)',
        fontSize: '0.6875rem',
        fontWeight: 700,
        lineHeight: 1.25,
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
        userSelect: 'none',
        minWidth: '4.5rem',
      }}
      aria-label={`Status: ${label}`}
    >
      {label}
    </span>
  )
}
