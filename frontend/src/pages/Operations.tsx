/**
 * src/pages/Operations.tsx
 *
 * Phase 3: Security Operations Dashboard.
 *
 * Features:
 * 1. Fleet Inventory & Posture Metrics
 * 2. Operator Priority Queue (P1 Critical -> P4 Low)
 * 3. Remediation & Post-Fix Verification Tool
 * 4. Configuration Baselines & Drift Compare
 * 5. Bounded Natural-Language Security Query Layer
 */

import { useState, useEffect } from 'react'
import { apiFetch } from '../api/client'

interface FleetDevice {
  device_id: string
  hostname: string
  vendor: string
  environment: string
  current_posture: string
  status: string
}

interface PriorityFinding {
  finding_id: string
  device_id: string
  control_id: string
  severity: string
  priority_tier: string
  priority_score: number
  risk_factors: string[]
}

interface FleetPostureOverview {
  total_devices: number
  healthy_devices: number
  needs_attention_devices: number
  critical_devices: number
  total_open_findings: number
  open_critical_findings: number
}

export function Operations() {
  const [activeTab, setActiveTab] = useState<'inventory' | 'queue' | 'remediation' | 'baselines' | 'query'>('inventory')

  // Inventory & Fleet State
  const [devices, setDevices] = useState<FleetDevice[]>([])
  const [posture, setPosture] = useState<FleetPostureOverview | null>(null)
  const [loading, setLoading] = useState(true)

  // Priority Queue State
  const [priorityQueue, setPriorityQueue] = useState<PriorityFinding[]>([])

  // Remediation & Verification State
  const [remControlId, setRemControlId] = useState('TLN-001')
  const [remVendor, setRemVendor] = useState('cisco')
  const [remConfigText, setRemConfigText] = useState('hostname RTR-01\nline vty 0 4\n transport input ssh\n service password-encryption')
  const [verifyResult, setVerifyResult] = useState<any>(null)
  const [verifying, setVerifying] = useState(false)

  // NL Query State
  const [nlQuery, setNlQuery] = useState('')
  const [queryResult, setQueryResult] = useState<any>(null)
  const [querying, setQuerying] = useState(false)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      apiFetch<{ devices: FleetDevice[] }>('/api/v1/devices'),
      apiFetch<FleetPostureOverview>('/api/v1/fleet/posture'),
      apiFetch<{ queue: PriorityFinding[] }>('/api/v1/prioritization/queue'),
    ])
      .then(([devsRes, postRes, qRes]) => {
        setDevices(devsRes.devices)
        setPosture(postRes)
        setPriorityQueue(qRes.queue)
      })
      .catch((err) => console.error('Failed loading operations data:', err))
      .finally(() => setLoading(false))
  }, [])

  const handleVerifyRemediation = async () => {
    setVerifying(true)
    try {
      const res = await apiFetch<any>(`/api/v1/remediation/finding-sample/verify`, {
        method: 'POST',
        body: JSON.stringify({
          control_id: remControlId,
          remediated_config_text: remConfigText,
          vendor: remVendor,
        }),
      })
      setVerifyResult(res)
    } catch (err) {
      console.error('Failed verifying remediation:', err)
    } finally {
      setVerifying(false)
    }
  }

  const handleRunNlQuery = async () => {
    if (!nlQuery.trim()) return
    setQuerying(true)
    try {
      const res = await apiFetch<any>('/api/v1/query', {
        method: 'POST',
        body: JSON.stringify({ query: nlQuery }),
      })
      setQueryResult(res)
    } catch (err) {
      console.error('Failed running natural language query:', err)
    } finally {
      setQuerying(false)
    }
  }

  return (
    <div style={{ paddingBottom: '3rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--cs-text-primary)', margin: '0 0 0.5rem 0', letterSpacing: '-0.02em' }}>
          Security Operations Dashboard
        </h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--cs-text-muted)', margin: 0 }}>
          Continuous fleet posture management, priority risk queue, remediation verification, and bounded natural-language query layer.
        </p>
      </div>

      {/* Fleet Overview Cards */}
      {posture && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <div className="cs-card" style={{ padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Total Devices
            </span>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--cs-text-primary)', marginTop: '0.25rem' }}>
              {posture.total_devices}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-secondary)' }}>Registered Inventory</span>
          </div>

          <div className="cs-card" style={{ padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Healthy Devices
            </span>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#22c55e', marginTop: '0.25rem' }}>
              {posture.healthy_devices}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-secondary)' }}>100% Compliant</span>
          </div>

          <div className="cs-card" style={{ padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Needs Attention
            </span>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#eab308', marginTop: '0.25rem' }}>
              {posture.needs_attention_devices}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-secondary)' }}>Medium/Low Findings</span>
          </div>

          <div className="cs-card" style={{ padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Open Critical Findings
            </span>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#ef4444', marginTop: '0.25rem' }}>
              {posture.open_critical_findings}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-secondary)' }}>Require Remediation</span>
          </div>
        </div>
      )}

      {/* Tab Nav */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--cs-border)', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('inventory')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'inventory' ? '2px solid var(--cs-accent)' : '2px solid transparent',
            color: activeTab === 'inventory' ? 'var(--cs-accent)' : 'var(--cs-text-muted)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Fleet Inventory
        </button>
        <button
          onClick={() => setActiveTab('queue')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'queue' ? '2px solid var(--cs-accent)' : '2px solid transparent',
            color: activeTab === 'queue' ? 'var(--cs-accent)' : 'var(--cs-text-muted)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Operator Priority Queue ({priorityQueue.length})
        </button>
        <button
          onClick={() => setActiveTab('remediation')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'remediation' ? '2px solid var(--cs-accent)' : '2px solid transparent',
            color: activeTab === 'remediation' ? 'var(--cs-accent)' : 'var(--cs-text-muted)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Remediation & Verification
        </button>
        <button
          onClick={() => setActiveTab('query')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'query' ? '2px solid var(--cs-accent)' : '2px solid transparent',
            color: activeTab === 'query' ? 'var(--cs-accent)' : 'var(--cs-text-muted)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Natural-Language Query
        </button>
      </div>

      {/* Tab 1: Fleet Inventory */}
      {activeTab === 'inventory' && (
        <div className="cs-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cs-text-primary)', marginBottom: '1rem' }}>
            Registered Device Inventory
          </h2>
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>Loading fleet devices…</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--cs-border)' }}>
                    <th style={{ padding: '0.75rem', color: 'var(--cs-text-muted)' }}>Hostname</th>
                    <th style={{ padding: '0.75rem', color: 'var(--cs-text-muted)' }}>Vendor</th>
                    <th style={{ padding: '0.75rem', color: 'var(--cs-text-muted)' }}>Environment</th>
                    <th style={{ padding: '0.75rem', color: 'var(--cs-text-muted)' }}>Posture</th>
                    <th style={{ padding: '0.75rem', color: 'var(--cs-text-muted)' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {devices.map((d) => (
                    <tr key={d.device_id} style={{ borderBottom: '1px solid var(--cs-border-subtle)' }}>
                      <td style={{ padding: '0.75rem', fontWeight: 600, color: 'var(--cs-text-primary)' }}>{d.hostname}</td>
                      <td style={{ padding: '0.75rem', color: 'var(--cs-text-secondary)' }}>{d.vendor.toUpperCase()}</td>
                      <td style={{ padding: '0.75rem', color: 'var(--cs-text-secondary)' }}>{d.environment}</td>
                      <td style={{ padding: '0.75rem' }}>
                        <span
                          style={{
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            backgroundColor:
                              d.current_posture === 'HEALTHY'
                                ? 'rgba(34, 197, 94, 0.15)'
                                : d.current_posture === 'CRITICAL'
                                ? 'rgba(239, 68, 68, 0.15)'
                                : 'rgba(234, 179, 8, 0.15)',
                            color:
                              d.current_posture === 'HEALTHY'
                                ? '#22c55e'
                                : d.current_posture === 'CRITICAL'
                                ? '#ef4444'
                                : '#eab308',
                          }}
                        >
                          {d.current_posture}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem', color: 'var(--cs-text-muted)' }}>{d.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Operator Priority Queue */}
      {activeTab === 'queue' && (
        <div className="cs-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cs-text-primary)', marginBottom: '0.5rem' }}>
            Deterministic Risk Priority Queue
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--cs-text-muted)', marginBottom: '1.5rem' }}>
            Findings ranked deterministically by severity base score, recurrence frequency, and attack chain risk amplification.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {priorityQueue.map((item) => (
              <div
                key={item.finding_id}
                style={{
                  padding: '1rem',
                  backgroundColor: 'var(--cs-bg-elevated)',
                  border: '1px solid var(--cs-border)',
                  borderRadius: '6px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span
                      style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        backgroundColor: item.priority_tier.startsWith('P1') ? 'rgba(239, 68, 68, 0.2)' : 'rgba(234, 179, 8, 0.2)',
                        color: item.priority_tier.startsWith('P1') ? '#ef4444' : '#eab308',
                      }}
                    >
                      {item.priority_tier}
                    </span>
                    <strong style={{ color: 'var(--cs-text-primary)' }}>{item.control_id}</strong>
                    <span style={{ fontSize: '0.8125rem', color: 'var(--cs-text-muted)' }}>on Device: {item.device_id}</span>
                  </div>
                  <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--cs-accent)' }}>
                    Priority Score: {item.priority_score} / 10
                  </span>
                </div>

                <div style={{ fontSize: '0.8125rem', color: 'var(--cs-text-secondary)', marginTop: '0.5rem' }}>
                  <strong>Risk Amplification Factors:</strong> {item.risk_factors.join(' • ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Remediation & Verification */}
      {activeTab === 'remediation' && (
        <div className="cs-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cs-text-primary)', marginBottom: '0.5rem' }}>
            Remediation Verification Tool
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--cs-text-muted)', marginBottom: '1.5rem' }}>
            Simulate or submit remediated configuration text to deterministically verify that the fix resolves non-compliant controls.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--cs-text-secondary)', marginBottom: '0.5rem' }}>
                Control ID & Vendor:
              </label>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                <input
                  type="text"
                  value={remControlId}
                  onChange={(e) => setRemControlId(e.target.value)}
                  style={{
                    padding: '0.5rem',
                    backgroundColor: 'var(--cs-bg-elevated)',
                    color: 'var(--cs-text-primary)',
                    border: '1px solid var(--cs-border)',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                  }}
                />
                <select
                  value={remVendor}
                  onChange={(e) => setRemVendor(e.target.value)}
                  style={{
                    padding: '0.5rem',
                    backgroundColor: 'var(--cs-bg-elevated)',
                    color: 'var(--cs-text-primary)',
                    border: '1px solid var(--cs-border)',
                    borderRadius: '6px',
                    fontSize: '0.875rem',
                  }}
                >
                  <option value="cisco">Cisco IOS</option>
                  <option value="juniper">Juniper JunOS</option>
                  <option value="arista">Arista EOS</option>
                  <option value="fortinet">FortiOS</option>
                  <option value="panos">PAN-OS</option>
                </select>
              </div>

              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--cs-text-secondary)', marginBottom: '0.5rem' }}>
                Remediated Config Text:
              </label>
              <textarea
                value={remConfigText}
                onChange={(e) => setRemConfigText(e.target.value)}
                rows={7}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontFamily: 'var(--cs-font-mono)',
                  fontSize: '0.8125rem',
                  backgroundColor: 'var(--cs-bg-elevated)',
                  color: 'var(--cs-text-primary)',
                  border: '1px solid var(--cs-border)',
                  borderRadius: '6px',
                }}
              />
              <button
                onClick={handleVerifyRemediation}
                disabled={verifying}
                style={{
                  marginTop: '1rem',
                  width: '100%',
                  padding: '0.625rem',
                  backgroundColor: 'var(--cs-accent)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  cursor: verifying ? 'not-allowed' : 'pointer',
                }}
              >
                {verifying ? 'Verifying Fix…' : 'Verify Fix Result'}
              </button>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--cs-text-secondary)', marginBottom: '0.5rem' }}>
                Verification Outcome:
              </label>
              {verifyResult ? (
                <div style={{ padding: '1.25rem', backgroundColor: 'var(--cs-bg-elevated)', borderRadius: '6px', border: '1px solid var(--cs-border)' }}>
                  <div style={{ fontSize: '1.125rem', fontWeight: 700, color: verifyResult.status === 'FIX_VERIFIED' ? '#22c55e' : '#ef4444', marginBottom: '0.5rem' }}>
                    {verifyResult.status}
                  </div>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--cs-text-secondary)' }}>
                    {verifyResult.evidence_note}
                  </p>
                </div>
              ) : (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--cs-text-muted)', border: '1px dashed var(--cs-border)', borderRadius: '6px' }}>
                  Click "Verify Fix Result" to execute verification comparator.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Natural-Language Query */}
      {activeTab === 'query' && (
        <div className="cs-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cs-text-primary)', marginBottom: '0.5rem' }}>
            Bounded Natural-Language Security Search
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--cs-text-muted)', marginBottom: '1.5rem' }}>
            Search fleet devices and security findings using plain English. Query is safely mapped to strict Pydantic schemas without arbitrary SQL execution.
          </p>

          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <input
              type="text"
              placeholder="e.g. 'Show me cisco devices with Telnet enabled'"
              value={nlQuery}
              onChange={(e) => setNlQuery(e.target.value)}
              style={{
                flex: 1,
                padding: '0.625rem 0.75rem',
                backgroundColor: 'var(--cs-bg-elevated)',
                color: 'var(--cs-text-primary)',
                border: '1px solid var(--cs-border)',
                borderRadius: '6px',
                fontSize: '0.875rem',
              }}
            />
            <button
              onClick={handleRunNlQuery}
              disabled={querying}
              style={{
                padding: '0.625rem 1.25rem',
                backgroundColor: 'var(--cs-accent)',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: querying ? 'not-allowed' : 'pointer',
              }}
            >
              {querying ? 'Searching…' : 'Execute Query'}
            </button>
          </div>

          {queryResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ padding: '1rem', backgroundColor: 'var(--cs-bg-elevated)', borderRadius: '6px' }}>
                <strong style={{ fontSize: '0.875rem', color: 'var(--cs-accent)' }}>Parsed Query Schema:</strong>
                <pre style={{ margin: '0.5rem 0 0 0', fontFamily: 'var(--cs-font-mono)', fontSize: '0.75rem', color: 'var(--cs-text-secondary)' }}>
                  {JSON.stringify(queryResult.parsed_schema, null, 2)}
                </pre>
              </div>

              <div>
                <strong style={{ fontSize: '0.875rem', color: 'var(--cs-text-primary)' }}>
                  Matched Devices ({queryResult.matched_devices.length}):
                </strong>
                <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {queryResult.matched_devices.map((d: any) => (
                    <span key={d.device_id} style={{ padding: '0.25rem 0.5rem', backgroundColor: 'var(--cs-bg-elevated)', border: '1px solid var(--cs-border)', borderRadius: '4px', fontSize: '0.8125rem', color: 'var(--cs-text-primary)' }}>
                      {d.hostname} ({d.vendor})
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
