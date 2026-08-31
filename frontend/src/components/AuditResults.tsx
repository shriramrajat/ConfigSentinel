/**
 * src/components/AuditResults.tsx
 *
 * Orchestration component for the audit results display.
 * Assembles DeviceInfo, ResultsSummary, and ResultsTable.
 * Handles the "Unknown Vendor" banner and client-side filtering.
 */

import { useState, useMemo } from 'react'
import type { AuditResponse, ComplianceStatus, Severity } from '../types/api'
import { DeviceInfo } from './DeviceInfo'
import { ResultsSummary } from './ResultsSummary'
import { ResultsTable } from './ResultsTable'

interface AuditResultsProps {
  data: AuditResponse
}

export function AuditResults({ data }: AuditResultsProps) {
  const isUnknownVendor = data.summary.vendor === 'unknown'

  // --- Filtering State ---
  const [filterStatus, setFilterStatus] = useState<ComplianceStatus | 'all'>('all')
  const [filterSeverity, setFilterSeverity] = useState<Severity | 'all'>('all')

  const filteredResults = useMemo(() => {
    return data.results.filter((res) => {
      if (filterStatus !== 'all' && res.status !== filterStatus) return false
      if (filterSeverity !== 'all' && res.severity !== filterSeverity) return false
      return true
    })
  }, [data.results, filterStatus, filterSeverity])

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '2rem',
        animation: 'cs-fade-in var(--cs-transition)',
      }}
      aria-label="Audit results"
    >
      {/* Optional Unknown Vendor Warning */}
      {isUnknownVendor && (
        <div
          role="alert"
          style={{
            backgroundColor: 'var(--cs-review-bg)',
            border: '1px solid var(--cs-review-border)',
            borderRadius: 'var(--cs-radius-md)',
            padding: '1rem 1.25rem',
            display: 'flex',
            gap: '0.75rem',
            alignItems: 'flex-start',
          }}
        >
          <svg
            aria-hidden="true"
            width="18"
            height="18"
            viewBox="0 0 15 15"
            fill="none"
            style={{ flexShrink: 0, marginTop: '0.125rem', color: 'var(--cs-review)' }}
          >
            <path
              d="M7.5 1.5L13.5 12H1.5L7.5 1.5Z"
              stroke="currentColor"
              strokeWidth="1.2"
              strokeLinejoin="round"
            />
            <path d="M7.5 6.5V9" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
            <circle cx="7.5" cy="10.5" r="0.6" fill="currentColor" />
          </svg>
          <p
            style={{
              margin: 0,
              fontFamily: 'var(--cs-font-sans)',
              fontSize: '0.875rem',
              color: 'var(--cs-review)',
              lineHeight: 1.55,
            }}
          >
            <strong>Vendor not recognised.</strong> All controls returned Not Applicable.
            ConfigSentinel supports Cisco IOS/IOS-XE and Juniper JunOS only.
          </p>
        </div>
      )}

      {/* Header Info Block */}
      <section aria-label="Device and Summary Information">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <DeviceInfo summary={data.summary} />
          <ResultsSummary summary={data.summary} />
        </div>
      </section>

      {/* Main Results Table */}
      <section aria-label="Detailed Compliance Results">
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            marginBottom: '1rem',
          }}
        >
          <h2
            style={{
              margin: 0,
              fontFamily: 'var(--cs-font-sans)',
              fontSize: '1rem',
              fontWeight: 600,
              color: 'var(--cs-text-primary)',
            }}
          >
            Compliance Controls
          </h2>

          {/* Filter Controls */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <FilterSelect
              label="Status"
              value={filterStatus}
              onChange={(val) => setFilterStatus(val as ComplianceStatus | 'all')}
              options={[
                { value: 'all', label: 'All Statuses' },
                { value: 'fail', label: 'Fail' },
                { value: 'needs_review', label: 'Review' },
                { value: 'pass', label: 'Pass' },
                { value: 'not_applicable', label: 'N/A' },
              ]}
            />
            <FilterSelect
              label="Severity"
              value={filterSeverity}
              onChange={(val) => setFilterSeverity(val as Severity | 'all')}
              options={[
                { value: 'all', label: 'All Severities' },
                { value: 'critical', label: 'Critical' },
                { value: 'high', label: 'High' },
                { value: 'medium', label: 'Medium' },
                { value: 'low', label: 'Low' },
                { value: 'info', label: 'Info' },
              ]}
            />
          </div>
        </div>

        {filteredResults.length > 0 ? (
          <ResultsTable results={filteredResults} />
        ) : (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              backgroundColor: 'var(--cs-bg-surface)',
              border: '1px solid var(--cs-border)',
              borderRadius: 'var(--cs-radius-md)',
              fontFamily: 'var(--cs-font-sans)',
              fontSize: '0.875rem',
              color: 'var(--cs-text-muted)',
            }}
          >
            No controls match the selected filters.
          </div>
        )}
      </section>

      <style>{`
        @keyframes cs-fade-in {
          from { opacity: 0; transform: translateY(5px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .cs-filter-select {
          font-family: var(--cs-font-sans);
          font-size: 0.75rem;
          color: var(--cs-text-primary);
          background-color: var(--cs-bg-elevated);
          border: 1px solid var(--cs-border);
          border-radius: var(--cs-radius-sm);
          padding: 0.25rem 1.5rem 0.25rem 0.5rem;
          appearance: none;
          cursor: pointer;
          transition: border-color var(--cs-transition-fast);
          background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%238a97b0' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 0.5rem center;
        }
        .cs-filter-select:focus-visible {
          outline: 2px solid var(--cs-accent);
          outline-offset: -1px;
          border-color: var(--cs-accent-muted);
        }
      `}</style>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Internal Filter Helper
// ---------------------------------------------------------------------------

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (val: string) => void
  options: { value: string; label: string }[]
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
      <span
        style={{
          fontFamily: 'var(--cs-font-sans)',
          fontSize: '0.6875rem',
          fontWeight: 500,
          color: 'var(--cs-text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        {label}
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="cs-filter-select"
        aria-label={`Filter by ${label}`}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
}

