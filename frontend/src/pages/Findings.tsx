/**
 * src/pages/Findings.tsx
 *
 * Persistent Security Finding Lifecycle Management UI.
 *
 * Features:
 *  - Real-time persistent security finding tracking across devices.
 *  - Lifecycle state filters: ALL, OPEN, ACKNOWLEDGED, RESOLVED.
 *  - Severity filters: ALL, CRITICAL, HIGH, MEDIUM, LOW.
 *  - Actions: Acknowledge finding, Resolve finding, Reopen finding.
 *  - Real backend data from /api/v1/findings.
 */

import { useEffect, useState } from 'react'
import {
  listFindings,
  acknowledgeFinding,
  resolveFinding,
  reopenFinding,
} from '../api/configsentinel'
import { PageContainer } from '../components/PageContainer'
import type { SecurityFinding } from '../types/api'

export function Findings() {
  const [findings, setFindings] = useState<SecurityFinding[]>([])
  const [total, setTotal] = useState<number>(0)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [deviceIdFilter, setDeviceIdFilter] = useState<string>('')

  const fetchFindings = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await listFindings({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        device_id: deviceIdFilter || undefined,
        limit: 100,
      })
      setFindings(res.findings)
      setTotal(res.total)
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch security findings.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchFindings()
  }, [statusFilter, severityFilter, deviceIdFilter])

  const handleAcknowledge = async (id: string) => {
    try {
      await acknowledgeFinding(id)
      fetchFindings()
    } catch (err: any) {
      alert(`Failed to acknowledge finding: ${err?.message || err}`)
    }
  }

  const handleResolve = async (id: string) => {
    try {
      await resolveFinding(id)
      fetchFindings()
    } catch (err: any) {
      alert(`Failed to resolve finding: ${err?.message || err}`)
    }
  }

  const handleReopen = async (id: string) => {
    try {
      await reopenFinding(id)
      fetchFindings()
    } catch (err: any) {
      alert(`Failed to reopen finding: ${err?.message || err}`)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <span style={{ color: 'var(--cs-fail)', fontWeight: 600 }}>● OPEN</span>
      case 'ACKNOWLEDGED':
        return <span style={{ color: 'var(--cs-review)', fontWeight: 600 }}>● ACKNOWLEDGED</span>
      case 'RESOLVED':
        return <span style={{ color: 'var(--cs-pass)', fontWeight: 600 }}>✓ RESOLVED</span>
      default:
        return <span>{status}</span>
    }
  }

  const getSeverityBadge = (severity: string) => {
    const s = severity.toUpperCase()
    let bg = 'var(--cs-bg-elevated)'
    let color = 'var(--cs-text-primary)'
    if (s === 'CRITICAL') {
      bg = 'var(--cs-fail-bg)'
      color = 'var(--cs-sev-critical)'
    } else if (s === 'HIGH') {
      bg = '#2d1602'
      color = 'var(--cs-sev-high)'
    } else if (s === 'MEDIUM') {
      bg = 'var(--cs-review-bg)'
      color = 'var(--cs-review)'
    } else if (s === 'LOW') {
      bg = 'var(--cs-pass-bg)'
      color = 'var(--cs-pass)'
    }

    return (
      <span
        style={{
          padding: '0.2rem 0.5rem',
          borderRadius: 'var(--cs-radius-sm)',
          fontSize: '0.75rem',
          fontWeight: 700,
          backgroundColor: bg,
          color: color,
        }}
      >
        {s}
      </span>
    )
  }

  return (
    <PageContainer
      title="Finding Lifecycle Intelligence"
      description={`Track persistent security findings, occurrence history, and state transitions across audits. (${total} total findings)`}
    >
      {/* Filter Toolbar */}
      <div
        className="cs-card"
        style={{
          display: 'flex',
          gap: '1rem',
          alignItems: 'center',
          flexWrap: 'wrap',
          marginBottom: '1.5rem',
          padding: '1rem 1.25rem',
        }}
      >
        <div style={{ flex: '1 1 160px', minWidth: '140px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--cs-text-muted)', marginBottom: '0.25rem', fontWeight: 500 }}>
            Status Filter
          </label>
          <select
            className="cs-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>

        <div style={{ flex: '1 1 160px', minWidth: '140px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--cs-text-muted)', marginBottom: '0.25rem', fontWeight: 500 }}>
            Severity Filter
          </label>
          <select
            className="cs-select"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div style={{ flex: '2 1 200px', minWidth: '180px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--cs-text-muted)', marginBottom: '0.25rem', fontWeight: 500 }}>
            Device Search
          </label>
          <input
            type="text"
            className="cs-text-input"
            placeholder="e.g. RTR-CORE-01"
            value={deviceIdFilter}
            onChange={(e) => setDeviceIdFilter(e.target.value)}
          />
        </div>
      </div>

      {/* Main Table */}
      {isLoading ? (
        <div className="cs-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
          Loading security findings...
        </div>
      ) : error ? (
        <div style={{ padding: '1rem 1.25rem', backgroundColor: 'var(--cs-fail-bg)', color: 'var(--cs-fail)', border: '1px solid var(--cs-fail-border)', borderRadius: 'var(--cs-radius)', marginBottom: '1.5rem' }}>
          {error}
        </div>
      ) : findings.length === 0 ? (
        <div className="cs-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
          No persistent security findings found matching the filter criteria.
        </div>
      ) : (
        <div className="cs-table-container">
          <table className="cs-table">
            <thead>
              <tr>
                <th>Device</th>
                <th>Control ID</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Occurrences</th>
                <th>First Seen</th>
                <th>Last Seen</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((f) => (
                <tr key={f.id}>
                  <td style={{ fontWeight: 600, color: 'var(--cs-text-primary)' }}>{f.device_id}</td>
                  <td style={{ fontFamily: 'var(--cs-font-mono)', color: 'var(--cs-accent)' }}>{f.control_id}</td>
                  <td>{getSeverityBadge(f.severity)}</td>
                  <td>{getStatusBadge(f.status)}</td>
                  <td style={{ fontWeight: 600 }}>{f.occurrence_count}</td>
                  <td style={{ color: 'var(--cs-text-muted)', fontSize: '0.75rem' }}>
                    {new Date(f.first_seen).toLocaleString()}
                  </td>
                  <td style={{ color: 'var(--cs-text-muted)', fontSize: '0.75rem' }}>
                    {new Date(f.last_seen).toLocaleString()}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      {f.status === 'OPEN' && (
                        <button
                          onClick={() => handleAcknowledge(f.id)}
                          className="cs-btn-ghost"
                          style={{ height: '1.875rem', padding: '0 0.625rem', fontSize: '0.75rem', color: 'var(--cs-review)', borderColor: 'var(--cs-review-border)' }}
                        >
                          Acknowledge
                        </button>
                      )}
                      {f.status !== 'RESOLVED' && (
                        <button
                          onClick={() => handleResolve(f.id)}
                          className="cs-btn-primary"
                          style={{ height: '1.875rem', padding: '0 0.625rem', fontSize: '0.75rem' }}
                        >
                          Resolve
                        </button>
                      )}
                      {f.status === 'RESOLVED' && (
                        <button
                          onClick={() => handleReopen(f.id)}
                          className="cs-btn-ghost"
                          style={{ height: '1.875rem', padding: '0 0.625rem', fontSize: '0.75rem', color: 'var(--cs-fail)' }}
                        >
                          Reopen
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </PageContainer>
  )
}
