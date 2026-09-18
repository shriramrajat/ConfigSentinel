import { useEffect, useState } from 'react'
import { listAudits } from '../api/configsentinel'
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
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', color: '#F8FAFC' }}>
      <header style={{ marginBottom: '24px', borderBottom: '1px solid #334155', paddingBottom: '16px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', color: '#38BDF8' }}>Audit History</h1>
        <p style={{ margin: '4px 0 0 0', color: '#94A3B8', fontSize: '14px' }}>
          Historical records of evaluated device configurations.
        </p>
      </header>

      {error && (
        <div style={{ padding: '12px 16px', background: '#7F1D1D', color: '#FECACA', borderRadius: '6px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ padding: '32px', textAlign: 'center', color: '#94A3B8' }}>Loading audit history...</div>
      ) : items.length === 0 ? (

        <div style={{ padding: '32px', textAlign: 'center', background: '#1E293B', borderRadius: '8px', color: '#94A3B8' }}>
          No audit records found.
        </div>
      ) : (
        <>
          <div style={{ overflowX: 'auto', background: '#1E293B', borderRadius: '8px', border: '1px solid #334155' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ background: '#0F172A', color: '#94A3B8', borderBottom: '1px solid #334155' }}>
                  <th style={{ padding: '12px 16px' }}>Audit ID</th>
                  <th style={{ padding: '12px 16px' }}>Timestamp</th>
                  <th style={{ padding: '12px 16px' }}>Vendor</th>
                  <th style={{ padding: '12px 16px' }}>Device / Source</th>
                  <th style={{ padding: '12px 16px' }}>Pass</th>
                  <th style={{ padding: '12px 16px' }}>Fail</th>
                  <th style={{ padding: '12px 16px' }}>Total Controls</th>
                  <th style={{ padding: '12px 16px' }}>Report</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #334155' }}>
                    <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: '#38BDF8' }}>
                      {item.id.slice(0, 8)}...
                    </td>
                    <td style={{ padding: '12px 16px', color: '#CBD5E1' }}>
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 16px', textTransform: 'uppercase', fontWeight: 'bold' }}>
                      {item.vendor}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#E2E8F0' }}>
                      {item.source_name || item.hostname || 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#34D399', fontWeight: 'bold' }}>{item.pass_count}</td>
                    <td style={{ padding: '12px 16px', color: '#F87171', fontWeight: 'bold' }}>{item.fail_count}</td>
                    <td style={{ padding: '12px 16px', color: '#94A3B8' }}>{item.total}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <a
                        href={`${apiBaseUrl}/api/v1/reports/${item.id}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          display: 'inline-block',
                          padding: '4px 10px',
                          background: '#0284C7',
                          color: '#FFF',
                          borderRadius: '4px',
                          textDecoration: 'none',
                          fontSize: '12px',
                        }}
                      >
                        PDF Report
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
            <span style={{ color: '#94A3B8', fontSize: '14px' }}>
              Showing {offset + 1} - {Math.min(offset + limit, total)} of {total} audits
            </span>
            <div>
              <button
                disabled={offset === 0}
                onClick={() => setOffset((o) => Math.max(0, o - limit))}
                style={{
                  padding: '6px 14px',
                  marginRight: '8px',
                  background: offset === 0 ? '#334155' : '#0284C7',
                  color: '#FFF',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: offset === 0 ? 'not-allowed' : 'pointer',
                }}
              >
                Previous
              </button>
              <button
                disabled={offset + limit >= total}
                onClick={() => setOffset((o) => o + limit)}
                style={{
                  padding: '6px 14px',
                  background: offset + limit >= total ? '#334155' : '#0284C7',
                  color: '#FFF',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: offset + limit >= total ? 'not-allowed' : 'pointer',
                }}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
