/**
 * src/components/EvidenceBlock.tsx
 *
 * Renders the exact evidence returned by the backend engine.
 * Displays verbatim configuration snippets WITHOUT fabricating line numbers.
 */

import type { Evidence } from '../types/api'
import { CopyButton } from './CopyButton'

interface EvidenceBlockProps {
  evidence: Evidence[]
}

export function EvidenceBlock({ evidence }: EvidenceBlockProps) {
  if (!evidence || evidence.length === 0) {
    return (
      <div
        style={{
          fontFamily: 'var(--cs-font-sans)',
          fontSize: '0.8125rem',
          color: 'var(--cs-text-muted)',
          fontStyle: 'italic',
        }}
      >
        No evidence provided by the engine.
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {evidence.map((ev, idx) => (
        <EvidenceItem key={idx} item={ev} />
      ))}
    </div>
  )
}

function EvidenceItem({ item }: { item: Evidence }) {
  // If raw_lines is empty, it means absence evidence (the directive wasn't found).
  const isAbsence = !item.raw_lines || item.raw_lines.length === 0
  const snippetText = item.raw_lines ? item.raw_lines.join('\n') : ''

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {/* Section label */}
      <div
        style={{
          fontFamily: 'var(--cs-font-sans)',
          fontSize: '0.75rem',
          fontWeight: 600,
          color: 'var(--cs-text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        Section: {item.section_name || 'Global'}
      </div>

      {/* Raw configuration snippet */}
      {isAbsence ? (
        <div
          style={{
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.8125rem',
            color: 'var(--cs-text-muted)',
            padding: '0.75rem',
            backgroundColor: 'var(--cs-bg-elevated)',
            border: '1px solid var(--cs-border)',
            borderRadius: 'var(--cs-radius)',
            fontStyle: 'italic',
          }}
        >
          Directive not found in configuration.
        </div>
      ) : (
        <div
          style={{
            backgroundColor: 'var(--cs-bg-elevated)',
            border: '1px solid var(--cs-border)',
            borderRadius: 'var(--cs-radius)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '0.375rem 0.75rem',
              backgroundColor: 'var(--cs-bg-subtle)',
              borderBottom: '1px solid var(--cs-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span
              style={{
                fontFamily: 'var(--cs-font-sans)',
                fontSize: '0.6875rem',
                color: 'var(--cs-text-muted)',
              }}
            >
              Configuration snippet
            </span>
            <CopyButton textToCopy={snippetText} label="Copy snippet" />
          </div>
          <pre
            style={{
              margin: 0,
              padding: '0.75rem',
              fontFamily: 'var(--cs-font-mono)',
              fontSize: '0.8125rem',
              lineHeight: 1.5,
              color: 'var(--cs-text-code)',
              overflowX: 'auto',
              whiteSpace: 'pre',
            }}
          >
            {snippetText}
          </pre>
        </div>
      )}

      {/* Observed vs Expected */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          padding: '0.75rem',
          backgroundColor: 'var(--cs-bg-subtle)',
          borderRadius: 'var(--cs-radius)',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--cs-text-muted)', textTransform: 'uppercase' }}>Found</span>
          <span style={{ fontSize: '0.8125rem', color: 'var(--cs-text-primary)' }}>
            {item.observed ?? 'Not present'}
          </span>
        </div>
        
        {item.expected && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            <span style={{ fontSize: '0.6875rem', color: 'var(--cs-text-muted)', textTransform: 'uppercase' }}>Required</span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--cs-text-primary)' }}>
              {item.expected}
            </span>
          </div>
        )}
      </div>

      {/* Note */}
      {item.note && (
        <p
          style={{
            margin: 0,
            fontFamily: 'var(--cs-font-sans)',
            fontSize: '0.8125rem',
            lineHeight: 1.5,
            color: 'var(--cs-text-secondary)',
          }}
        >
          <strong style={{ color: 'var(--cs-text-primary)' }}>Note:</strong> {item.note}
        </p>
      )}
    </div>
  )
}

