import { useEffect, useState } from 'react'
import { getDeviceDashboard } from '../api/configsentinel'
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
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', color: '#F8FAFC' }}>
      <header style={{ marginBottom: '24px', borderBottom: '1px solid #334155', paddingBottom: '16px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', color: '#38BDF8' }}>Device Inventory & Posture Dashboard</h1>
        <p style={{ margin: '4px 0 0 0', color: '#94A3B8', fontSize: '14px' }}>
          Aggregate security compliance metrics grouped by device.
        </p>
      </header>

      {error && (
        <div style={{ padding: '12px 16px', background: '#7F1D1D', color: '#FECACA', borderRadius: '6px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ padding: '32px', textAlign: 'center', color: '#94A3B8' }}>Loading device dashboard...</div>
      ) : devices.length === 0 ? (
        <div style={{ padding: '32px', textAlign: 'center', background: '#1E293B', borderRadius: '8px', color: '#94A3B8' }}>
          No audited devices recorded yet.
        </div>
      ) : (
        <div style={{ overflowX: 'auto', background: '#1E293B', borderRadius: '8px', border: '1px solid #334155' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ background: '#0F172A', color: '#94A3B8', borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '12px 16px' }}>Device Identifier</th>
                <th style={{ padding: '12px 16px' }}>Vendor</th>
                <th style={{ padding: '12px 16px' }}>Audit Count</th>
                <th style={{ padding: '12px 16px' }}>Last Audited</th>
                <th style={{ padding: '12px 16px' }}>Total Passes</th>
                <th style={{ padding: '12px 16px' }}>Total Violations</th>
                <th style={{ padding: '12px 16px' }}>Posture Status</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((dev) => {
                const isClean = dev.total_fails === 0
                return (
                  <tr key={`${dev.device}-${dev.vendor}`} style={{ borderBottom: '1px solid #334155' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 'bold', color: '#F8FAFC' }}>
                      {dev.device}
                    </td>
                    <td style={{ padding: '12px 16px', textTransform: 'uppercase', color: '#94A3B8' }}>
                      {dev.vendor}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#CBD5E1' }}>{dev.audit_count}</td>
                    <td style={{ padding: '12px 16px', color: '#94A3B8' }}>
                      {new Date(dev.last_audit).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#34D399', fontWeight: 'bold' }}>{dev.total_passes}</td>
                    <td style={{ padding: '12px 16px', color: '#F87171', fontWeight: 'bold' }}>{dev.total_fails}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span
                        style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: 'bold',
                          background: isClean ? '#065F46' : '#991B1B',
                          color: isClean ? '#A7F3D0' : '#FCA5A5',
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
    </div>
  )
}
