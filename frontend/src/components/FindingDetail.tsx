/**
 * src/components/FindingDetail.tsx
 *
 * Detailed view for a single compliance result.
 * Reveals Evidence and Remediation blocks.
 */

import type { ComplianceResult } from '../types/api'
import { EvidenceBlock } from './EvidenceBlock'
import { RemediationBlock } from './RemediationBlock'

interface FindingDetailProps {
  result: ComplianceResult
}

export function FindingDetail({ result }: FindingDetailProps) {
  const hasRemediations = result.remediations.length > 0 || result.framework_refs.length > 0

  return (
    <div
      style={{
        padding: '1.25rem 1.5rem',
        backgroundColor: 'var(--cs-bg-base)',
        borderTop: '1px solid var(--cs-border)',
        display: 'flex',
        flexDirection: 'column',
        gap: '2rem',
      }}
    >
      {/* Description */}
      <div>
        <h3
          style={{
            margin: '0 0 0.5rem',
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.8125rem',
            fontWeight: 600,
            color: 'var(--cs-text-primary)',
          }}
        >
          Description
        </h3>
        <p
          style={{
            margin: 0,
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.875rem',
            lineHeight: 1.6,
            color: 'var(--cs-text-secondary)',
          }}
        >
          {result.description}
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '2rem',
          alignItems: 'start',
        }}
      >
        {/* Evidence Column */}
        <section>
          <h3
            style={{
              margin: '0 0 1rem',
              fontFamily: 'var(--cs-font-sans)',
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: 'var(--cs-text-primary)',
            }}
          >
            Evidence
          </h3>
          <EvidenceBlock evidence={result.evidence} />
        </section>

        {/* Remediation Column (only if present) */}
        {hasRemediations && (
          <section>
            <h3
              style={{
                margin: '0 0 1rem',
                fontFamily: 'var(--cs-font-sans)',
                fontSize: '0.8125rem',
                fontWeight: 600,
                color: 'var(--cs-text-primary)',
              }}
            >
              Remediation
            </h3>
            <RemediationBlock
              remediations={result.remediations}
              frameworkRefs={result.framework_refs}
            />
          </section>
        )}
      </div>
    </div>
  )
}
