/**
 * src/components/ResultsTable.tsx
 *
 * Professional enterprise table for displaying compliance results.
 * Supports row expansion to reveal FindingDetail.
 * Designed for readability at desktop widths and accessibility.
 */

import { useState } from 'react'
import type { ComplianceResult } from '../types/api'
import { StatusBadge } from './StatusBadge'
import { SeverityIndicator } from './SeverityIndicator'
import { FindingDetail } from './FindingDetail'

interface ResultsTableProps {
  results: ComplianceResult[]
}

export function ResultsTable({ results }: ResultsTableProps) {
  // Track expanded row IDs
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  function toggleRow(id: string) {
    const next = new Set(expandedIds)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    setExpandedIds(next)
  }

  // Handle keyboard interaction (Enter/Space to toggle row)
  function handleKeyDown(e: React.KeyboardEvent, id: string) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      toggleRow(id)
    }
  }

  if (results.length === 0) {
    return null
  }

  return (
    <div
      style={{
        backgroundColor: 'var(--cs-bg-surface)',
        border: '1px solid var(--cs-border)',
        borderRadius: 'var(--cs-radius-md)',
        overflow: 'hidden',
      }}
      role="table"
      aria-label="Compliance Results"
    >
      {/* Table Header */}
      <div
        role="rowgroup"
        style={{
          display: 'grid',
          gridTemplateColumns: '80px 3fr 1fr 100px 48px',
          gap: '1rem',
          padding: '0.875rem 1.5rem',
          backgroundColor: 'var(--cs-bg-subtle)',
          borderBottom: '1px solid var(--cs-border)',
          fontFamily: 'var(--cs-font-sans)',
          fontSize: '0.6875rem',
          fontWeight: 600,
          color: 'var(--cs-text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
        }}
      >
        <div role="columnheader">ID</div>
        <div role="columnheader">Control Name</div>
        <div role="columnheader">Severity</div>
        <div role="columnheader">Status</div>
        <div role="columnheader" aria-label="Expand row details"></div>
      </div>

      {/* Table Body */}
      <div role="rowgroup">
        {results.map((result, idx) => {
          const isExpanded = expandedIds.has(result.control_id)
          const isLast = idx === results.length - 1

          return (
            <div
              key={result.control_id}
              style={{
                borderBottom: isLast ? 'none' : '1px solid var(--cs-border)',
              }}
            >
              {/* Row Header (Clickable) */}
              <div
                role="row"
                tabIndex={0}
                onClick={() => toggleRow(result.control_id)}
                onKeyDown={(e) => handleKeyDown(e, result.control_id)}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '80px 3fr 1fr 100px 48px',
                  gap: '1rem',
                  alignItems: 'center',
                  padding: '1rem 1.5rem',
                  cursor: 'pointer',
                  transition: 'background-color var(--cs-transition-fast)',
                  backgroundColor: isExpanded ? 'var(--cs-bg-subtle)' : 'transparent',
                }}
                className="cs-result-row"
                aria-expanded={isExpanded}
                aria-controls={`detail-${result.control_id}`}
              >
                {/* ID */}
                <div
                  role="cell"
                  style={{
                    fontFamily: 'var(--cs-font-mono)',
                    fontSize: '0.8125rem',
                    fontWeight: 500,
                    color: 'var(--cs-accent)',
                  }}
                >
                  {result.control_id}
                </div>

                {/* Name */}
                <div
                  role="cell"
                  style={{
                    fontFamily: 'var(--cs-font-sans)',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    color: 'var(--cs-text-primary)',
                  }}
                >
                  {result.control_name}
                </div>

                {/* Severity */}
                <div role="cell">
                  <SeverityIndicator severity={result.severity} />
                </div>

                {/* Status */}
                <div role="cell">
                  <StatusBadge status={result.status} />
                </div>

                {/* Expand Icon */}
                <div
                  role="cell"
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    color: 'var(--cs-text-muted)',
                  }}
                >
                  <svg
                    aria-hidden="true"
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    style={{
                      transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform var(--cs-transition-fast)',
                    }}
                  >
                    <path
                      d="M4 6L8 10L12 6"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              </div>

              {/* Expanded Detail Panel */}
              {isExpanded && (
                <div id={`detail-${result.control_id}`} role="region">
                  <FindingDetail result={result} />
                </div>
              )}
            </div>
          )
        })}
      </div>
      
      {/* Inject hover style for rows */}
      <style>{`
        .cs-result-row:hover {
          background-color: var(--cs-bg-subtle) !important;
        }
        .cs-result-row:focus-visible {
          outline: 2px solid var(--cs-accent);
          outline-offset: -2px;
        }
        
        /* Responsive adjustments for table */
        @media (max-width: 768px) {
          /* Convert grid to stacked card layout on mobile */
          [role="rowgroup"] > [role="row"] {
            display: flex !important;
            flex-direction: column;
            align-items: flex-start !important;
            gap: 0.5rem !important;
            padding: 1rem !important;
          }
          /* Hide table headers on mobile */
          [role="rowgroup"]:first-of-type {
            display: none !important;
          }
          [role="row"] > div {
            width: 100%;
          }
          /* Show expand icon correctly on mobile */
          [role="row"] > div:last-child {
            position: absolute;
            right: 1rem;
            margin-top: 0.25rem;
            width: auto;
          }
          /* Adjust row container for absolute positioning of icon */
          [role="row"] {
            position: relative;
          }
        }
      `}</style>
    </div>
  )
}
