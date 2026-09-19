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
        return <span style={{ color: '#ef4444', fontWeight: 600 }}>● OPEN</span>
      case 'ACKNOWLEDGED':
        return <span style={{ color: '#f59e0b', fontWeight: 600 }}>● ACKNOWLEDGED</span>
      case 'RESOLVED':
        return <span style={{ color: '#10b981', fontWeight: 600 }}>✓ RESOLVED</span>
      default:
        return <span>{status}</span>
    }
  }

  const getSeverityBadge = (severity: string) => {
    const s = severity.toUpperCase()
    let bg = '#374151'
    let color = '#ffffff'
    if (s === 'CRITICAL') { bg = '#991b1b'; color = '#fef2f2' }
    else if (s === 'HIGH') { bg = '#b45309'; color = '#fffbeb' }
    else if (s === 'MEDIUM') { bg = '#1e40af'; color = '#eff6ff' }
    else if (s === 'LOW') { bg = '#065f46'; color = '#ecfdf5' }

    return (
      <span
        style={{
          padding: '0.2rem 0.5rem',
          borderRadius: '4px',
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
    <div style={{ maxWidth: 'var(--cs-content-max)', margin: '0 auto', padding: '2rem 1.5rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--cs-text-primary)' }}>
          Finding Lifecycle Intelligence
        </h1>
        <p style={{ color: 'var(--cs-text-muted)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
          Track persistent security findings, occurrence history, and state transitions across audits. ({total} total findings)
        </p>
      </div>

      {/* Filter Toolbar */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          alignItems: 'center',
          flexWrap: 'wrap',
          marginBottom: '1.5rem',
          padding: '1rem',
          backgroundColor: 'var(--cs-bg-surface)',
          border: '1px solid var(--cs-border)',
          borderRadius: '6px',
        }}
      >
        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--cs-text-muted)', marginBottom: '0.25rem' }}>
            Status Filter
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              backgroundColor: 'var(--cs-bg-main)',
              color: 'var(--cs-text-primary)',
              border: '1px solid var(--cs-border)',
              borderRadius: '4px',
            }}
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--cs-text-muted)', marginBottom: '0.25rem' }}>
            Severity Filter
          </label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              backgroundColor: 'var(--cs-bg-main)',
              color: 'var(--cs-text-primary)',
              border: '1px solid var(--cs-border)',
              borderRadius: '4px',
            }}
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--cs-text-muted)', marginBottom: '0.25rem' }}>
            Device Search
          </label>
          <input
            type="text"
            placeholder="e.g. RTR-CORE-01"
            value={deviceIdFilter}
            onChange={(e) => setDeviceIdFilter(e.target.value)}
            style={{
              padding: '0.4rem 0.75rem',
              backgroundColor: 'var(--cs-bg-main)',
              color: 'var(--cs-text-primary)',
              border: '1px solid var(--cs-border)',
              borderRadius: '4px',
            }}
          />
        </div>
      </div>

      {/* Main Table */}
      {isLoading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
          Loading security findings...
        </div>
      ) : error ? (
        <div style={{ padding: '1.5rem', backgroundColor: '#fee2e2', color: '#b91c1c', borderRadius: '6px' }}>
          {error}
        </div>
      ) : findings.length === 0 ? (
        <div
          style={{
            padding: '3rem',
            textAlign: 'center',
            backgroundColor: 'var(--cs-bg-surface)',
            border: '1px solid var(--cs-border)',
            borderRadius: '6px',
            color: 'var(--cs-text-muted)',
          }}
        >
          No persistent security findings found matching the filter criteria.
        </div>
      ) : (
        <div style={{ overflowX: 'auto', border: '1px solid var(--cs-border)', borderRadius: '6px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'var(--cs-bg-surface)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--cs-border)', textAlign: 'left', fontSize: '0.75rem', color: 'var(--cs-text-muted)', textTransform: 'uppercase' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Device</th>
                <th style={{ padding: '0.75rem 1rem' }}>Control ID</th>
                <th style={{ padding: '0.75rem 1rem' }}>Severity</th>
                <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                <th style={{ padding: '0.75rem 1rem' }}>Occurrences</th>
                <th style={{ padding: '0.75rem 1rem' }}>First Seen</th>
                <th style={{ padding: '0.75rem 1rem' }}>Last Seen</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((f) => (
                <tr key={f.id} style={{ borderBottom: '1px solid var(--cs-border)', fontSize: '0.875rem' }}>
                  <td style={{ padding: '0.875rem 1rem', fontWeight: 600, color: 'var(--cs-text-primary)' }}>{f.device_id}</td>
                  <td style={{ padding: '0.875rem 1rem', fontFamily: 'var(--cs-font-mono)', color: 'var(--cs-accent)' }}>{f.control_id}</td>
                  <td style={{ padding: '0.875rem 1rem' }}>{getSeverityBadge(f.severity)}</td>
                  <td style={{ padding: '0.875rem 1rem' }}>{getStatusBadge(f.status)}</td>
                  <td style={{ padding: '0.875rem 1rem', fontWeight: 600 }}>{f.occurrence_count}</td>
                  <td style={{ padding: '0.875rem 1rem', color: 'var(--cs-text-muted)', fontSize: '0.75rem' }}>
                    {new Date(f.first_seen).toLocaleString()}
                  </td>
                  <td style={{ padding: '0.875rem 1rem', color: 'var(--cs-text-muted)', fontSize: '0.75rem' }}>
                    {new Date(f.last_seen).toLocaleString()}
                  </td>
                  <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      {f.status === 'OPEN' && (
                        <button
                          onClick={() => handleAcknowledge(f.id)}
                          style={{
                            padding: '0.25rem 0.5rem',
                            fontSize: '0.75rem',
                            backgroundColor: '#f59e0b',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                          }}
                        >
                          Acknowledge
                        </button>
                      )}
                      {f.status !== 'RESOLVED' && (
                        <button
                          onClick={() => handleResolve(f.id)}
                          style={{
                            padding: '0.25rem 0.5rem',
                            fontSize: '0.75rem',
                            backgroundColor: '#10b981',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                          }}
                        >
                          Resolve
                        </button>
                      )}
                      {f.status === 'RESOLVED' && (
                        <button
                          onClick={() => handleReopen(f.id)}
                          style={{
                            padding: '0.25rem 0.5rem',
                            fontSize: '0.75rem',
                            backgroundColor: '#ef4444',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                          }}
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
    </div>
  )
}
