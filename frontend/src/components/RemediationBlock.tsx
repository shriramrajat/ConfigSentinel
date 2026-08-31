/**
 * src/components/RemediationBlock.tsx
 *
 * Displays remediation guidance from the API.
 * Makes it clear that `config_hint` is advisory only.
 */

import type { Remediation } from '../types/api'
import { CopyButton } from './CopyButton'

interface RemediationBlockProps {
  remediations: Remediation[]
  frameworkRefs: string[]
}

export function RemediationBlock({ remediations, frameworkRefs }: RemediationBlockProps) {
  if (remediations.length === 0 && frameworkRefs.length === 0) {
    return null
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {remediations.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {remediations.map((rem, idx) => (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              
              {/* Vendor Badge */}
              <div>
                <span
                  style={{
                    display: 'inline-block',
                    padding: '0.125rem 0.375rem',
                    backgroundColor: 'var(--cs-accent-subtle)',
                    border: '1px solid var(--cs-accent-muted)',
                    borderRadius: 'var(--cs-radius-sm)',
                    fontFamily: 'var(--cs-font-sans)',
                    fontSize: '0.625rem',
                    fontWeight: 600,
                    color: 'var(--cs-text-primary)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                  }}
                >
                  {rem.vendor}
                </span>
              </div>

              {/* Guidance text */}
              <p
                style={{
                  margin: 0,
                  fontFamily: 'var(--cs-font-sans)',
                  fontSize: '0.875rem',
                  lineHeight: 1.6,
                  color: 'var(--cs-text-primary)',
                }}
              >
                {rem.guidance}
              </p>

              {/* Code hint (Advisory only) */}
              {rem.config_hint && (
                <div
                  style={{
                    backgroundColor: 'var(--cs-bg-elevated)',
                    border: '1px solid var(--cs-border-strong)',
                    borderRadius: 'var(--cs-radius)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      padding: '0.375rem 0.75rem',
                      backgroundColor: '#1f1604', // custom dark amber for advisory warning
                      borderBottom: '1px solid var(--cs-border)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '0.5rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <svg
                        aria-hidden="true"
                        width="14"
                        height="14"
                        viewBox="0 0 14 14"
                        fill="none"
                        style={{ color: '#f59e0b', flexShrink: 0 }}
                      >
                        <path
                          d="M7 1.16669L1 11.6667H13L7 1.16669Z"
                          stroke="currentColor"
                          strokeWidth="1.2"
                          strokeLinejoin="round"
                        />
                        <path d="M7 5.25V8.16667" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                        <circle cx="7" cy="10" r="0.6" fill="currentColor" />
                      </svg>
                      <span
                        style={{
                          fontFamily: 'var(--cs-font-sans)',
                          fontSize: '0.6875rem',
                          fontWeight: 600,
                          color: '#fcd34d', // amber-300
                        }}
                      >
                        Advisory only — do not apply without review
                      </span>
                    </div>
                    
                    <CopyButton textToCopy={rem.config_hint} label="Copy config" />
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
                    }}
                  >
                    {rem.config_hint}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Framework References */}
      {frameworkRefs.length > 0 && (
        <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--cs-border-muted)' }}>
          <h4
            style={{
              margin: '0 0 0.5rem',
              fontFamily: 'var(--cs-font-sans)',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: 'var(--cs-text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            Framework References
          </h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {frameworkRefs.map(ref => (
              <span
                key={ref}
                style={{
                  padding: '0.125rem 0.5rem',
                  backgroundColor: 'var(--cs-bg-subtle)',
                  border: '1px solid var(--cs-border)',
                  borderRadius: 'var(--cs-radius-sm)',
                  fontFamily: 'var(--cs-font-mono)',
                  fontSize: '0.75rem',
                  color: 'var(--cs-text-primary)',
                }}
              >
                {ref}
              </span>
            ))}
          </div>
        </div>
      )}

    </div>
  )
}

