import { useEffect, useState } from 'react'
import { listAudits } from '../api/configsentinel'
import { PageContainer } from '../components/PageContainer'
import type { AuditListItem } from '../types/api'

export function History() {
  const [items, setItems] = useState<AuditListItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [offset, setOffset] = useState(0)
  const limit = 15

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listAudits({ limit, offset })
      setItems(res.items)
      setTotal(res.total)
    } catch (err: any) {
      setError(err.message || 'Failed to load audit history.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [offset])

  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

  return (
    <PageContainer
      title="Audit History"
      description="Historical records of evaluated device configurations and compliance reports."
    >
      {error && (
        <div
          style={{
            padding: '0.875rem 1rem',
            backgroundColor: 'var(--cs-fail-bg)',
            border: '1px solid var(--cs-fail-border)',
            color: 'var(--cs-fail)',
            borderRadius: 'var(--cs-radius)',
            marginBottom: '1.5rem',
          }}
        >
          {error}
        </div>
      )}

      {loading ? (
        <div className="cs-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
          Loading audit history...
        </div>
      ) : items.length === 0 ? (
        <div className="cs-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
          No audit records found.
        </div>
      ) : (
        <>
          <div className="cs-table-container">
            <table className="cs-table">
              <thead>
                <tr>
                  <th>Audit ID</th>
                  <th>Timestamp</th>
                  <th>Vendor</th>
                  <th>Device / Source</th>
                  <th>Pass</th>
                  <th>Fail</th>
                  <th>Total Controls</th>
                  <th>Report</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td style={{ fontFamily: 'var(--cs-font-mono)', color: 'var(--cs-accent)' }}>
                      {item.id.slice(0, 8)}...
                    </td>
                    <td style={{ color: 'var(--cs-text-secondary)' }}>
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td style={{ textTransform: 'uppercase', fontWeight: 600 }}>
                      {item.vendor}
                    </td>
                    <td style={{ color: 'var(--cs-text-primary)' }}>
                      {item.source_name || item.hostname || 'N/A'}
                    </td>
                    <td style={{ color: 'var(--cs-pass)', fontWeight: 600 }}>{item.pass_count}</td>
                    <td style={{ color: 'var(--cs-fail)', fontWeight: 600 }}>{item.fail_count}</td>
                    <td style={{ color: 'var(--cs-text-muted)' }}>{item.total}</td>
                    <td>
                      <a
                        href={`${apiBaseUrl}/api/v1/reports/${item.id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="cs-btn-ghost"
                        style={{ height: '2rem', padding: '0 0.75rem', fontSize: '0.75rem', textDecoration: 'none' }}
                      >
                        PDF Report
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem' }}>
            <span style={{ color: 'var(--cs-text-muted)', fontSize: '0.875rem' }}>
              Showing {offset + 1} - {Math.min(offset + limit, total)} of {total} audits
            </span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                disabled={offset === 0}
                onClick={() => setOffset((o) => Math.max(0, o - limit))}
                className="cs-btn-ghost"
              >
                Previous
              </button>
              <button
                disabled={offset + limit >= total}
                onClick={() => setOffset((o) => o + limit)}
                className="cs-btn-primary"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </PageContainer>
  )
}
