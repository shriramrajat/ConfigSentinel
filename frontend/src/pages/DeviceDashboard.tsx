import { useEffect, useState } from 'react'
import { getDeviceDashboard } from '../api/configsentinel'
import { PageContainer } from '../components/PageContainer'
import type { DeviceSummary } from '../types/api'

export function DeviceDashboard() {
  const [devices, setDevices] = useState<DeviceSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboard = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getDeviceDashboard()
      setDevices(res.devices)
    } catch (err: any) {
      setError(err.message || 'Failed to load device dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [])

  return (
    <PageContainer
      title="Device Inventory & Posture Dashboard"
      description="Aggregate security compliance metrics grouped by audited device."
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
          Loading device dashboard...
        </div>
      ) : devices.length === 0 ? (
        <div className="cs-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
          No audited devices recorded yet.
        </div>
      ) : (
        <div className="cs-table-container">
          <table className="cs-table">
            <thead>
              <tr>
                <th>Device Identifier</th>
                <th>Vendor</th>
                <th>Audit Count</th>
                <th>Last Audited</th>
                <th>Total Passes</th>
                <th>Total Violations</th>
                <th>Posture Status</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((dev) => {
                const isClean = dev.total_fails === 0
                return (
                  <tr key={`${dev.device}-${dev.vendor}`}>
                    <td style={{ fontWeight: 600, color: 'var(--cs-text-primary)' }}>
                      {dev.device}
                    </td>
                    <td style={{ textTransform: 'uppercase', color: 'var(--cs-text-secondary)' }}>
                      {dev.vendor}
                    </td>
                    <td style={{ color: 'var(--cs-text-primary)' }}>{dev.audit_count}</td>
                    <td style={{ color: 'var(--cs-text-muted)' }}>
                      {new Date(dev.last_audit).toLocaleString()}
                    </td>
                    <td style={{ color: 'var(--cs-pass)', fontWeight: 600 }}>{dev.total_passes}</td>
                    <td style={{ color: 'var(--cs-fail)', fontWeight: 600 }}>{dev.total_fails}</td>
                    <td>
                      <span
                        style={{
                          padding: '0.25rem 0.5rem',
                          borderRadius: 'var(--cs-radius-sm)',
                          fontSize: '0.6875rem',
                          fontWeight: 700,
                          backgroundColor: isClean ? 'var(--cs-pass-bg)' : 'var(--cs-fail-bg)',
                          color: isClean ? 'var(--cs-pass)' : 'var(--cs-fail)',
                          border: `1px solid ${isClean ? 'var(--cs-pass-border)' : 'var(--cs-fail-border)'}`,
                          letterSpacing: '0.04em',
                        }}
                      >
                        {isClean ? 'HEALTHY' : 'ATTENTION REQUIRED'}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </PageContainer>
  )
}
