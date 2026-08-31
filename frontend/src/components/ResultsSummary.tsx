/**
 * src/components/ResultsSummary.tsx
 *
 * Renders the top-level outcome counts of the audit.
 * Exactly reflects the values provided by the backend in AuditSummary.
 *
 * Rules:
 * - Do NOT calculate security scores or percentages
 * - Present N/A clearly as a neutral state
 */

import type { AuditSummary } from '../types/api'

interface ResultsSummaryProps {
  summary: AuditSummary
}

export function ResultsSummary({ summary }: ResultsSummaryProps) {
  const {
    pass_count,
    fail_count,
    needs_review_count,
    not_applicable_count,
    severity_distribution,
  } = summary

  // Prepare a string like "1 CRITICAL, 2 HIGH" if there are non-zero severities
  const distEntries = Object.entries(severity_distribution)
    .filter(([, count]) => count > 0)
    .map(([sev, count]) => `${count} ${sev.toUpperCase()}`)
  
  const distText = distEntries.length > 0 ? distEntries.join(', ') : 'None'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {/* 4-card grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '0.75rem',
        }}
      >
        <CountCard
          label="Pass"
          value={pass_count}
          color="var(--cs-pass)"
          bg="var(--cs-pass-bg)"
          border="var(--cs-pass-border)"
        />
        <CountCard
          label="Fail"
          value={fail_count}
          color="var(--cs-fail)"
          bg="var(--cs-fail-bg)"
          border="var(--cs-fail-border)"
        />
        <CountCard
          label="Needs Review"
          value={needs_review_count}
          color="var(--cs-review)"
          bg="var(--cs-review-bg)"
          border="var(--cs-review-border)"
        />
        <CountCard
          label="Not Applicable"
          value={not_applicable_count}
          color="var(--cs-na)"
          bg="var(--cs-na-bg)"
          border="var(--cs-na-border)"
        />
      </div>

      {/* Optional: Severity distribution info text below the cards */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '0 0.25rem' }}>
        <p
          style={{
            margin: 0,
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.75rem',
            color: 'var(--cs-text-muted)',
          }}
        >
          Severity distribution: <span style={{ color: 'var(--cs-text-secondary)' }}>{distText}</span>
        </p>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Internal card component
// ---------------------------------------------------------------------------

function CountCard({
  label,
  value,
  color,
  bg,
  border,
}: {
  label: string
  value: number
  color: string
  bg: string
  border: string
}) {
  return (
    <div
      style={{
        backgroundColor: bg,
        border: `1px solid ${border}`,
        borderRadius: 'var(--cs-radius-md)',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}
    >
      <span
        style={{
          fontFamily: 'var(--cs-font-sans)',
          fontSize: '0.8125rem',
          fontWeight: 500,
          color: 'var(--cs-text-secondary)',
          lineHeight: 1,
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontFamily: 'var(--cs-font-mono)',
          fontSize: '1.5rem',
          fontWeight: 700,
          color,
          lineHeight: 1,
        }}
      >
        {value}
      </span>
    </div>
  )
}
