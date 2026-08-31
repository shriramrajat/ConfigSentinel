/**
 * src/components/SeverityIndicator.tsx
 *
 * Renders the business-impact severity of a security control.
 * Severity is a static property of the control itself, not the finding result.
 * Always includes text labels per the UX requirement (no color-only indicators).
 */

import type { Severity } from '../types/api'

interface SeverityIndicatorProps {
  severity: Severity
}

export function SeverityIndicator({ severity }: SeverityIndicatorProps) {
  let colorVar = ''

  switch (severity) {
    case 'critical':
      colorVar = 'var(--cs-sev-critical)'
      break
    case 'high':
      colorVar = 'var(--cs-sev-high)'
      break
    case 'medium':
      colorVar = 'var(--cs-sev-medium)'
      break
    case 'low':
      colorVar = 'var(--cs-sev-low)'
      break
    case 'info':
    default:
      colorVar = 'var(--cs-sev-info)'
      break
  }

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.375rem',
      }}
      aria-label={`Severity: ${severity}`}
    >
      <span
        aria-hidden="true"
        style={{
          display: 'inline-block',
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: colorVar,
          flexShrink: 0,
        }}
      />
      <span
        style={{
          fontFamily: 'var(--cs-font-sans)',
          fontSize: '0.6875rem',
          fontWeight: 600,
          color: colorVar,
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        {severity}
      </span>
    </div>
  )
}
