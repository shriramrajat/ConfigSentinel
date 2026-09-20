/**
 * src/pages/Intelligence.tsx
 *
 * Phase 2: Cross-Vendor Security Intelligence Dashboard.
 *
 * Features:
 * 1. Cross-Vendor Control Coverage Matrix (Cisco, Juniper, Arista, FortiOS, PAN-OS)
 * 2. Security Policy Translation Engine
 * 3. Deterministic What-If Compliance Simulator
 * 4. Control Dependency & Risk Amplification Graph
 * 5. Bounded AI Security Explanation Modal
 */

import { useState, useEffect } from 'react'
import { PageContainer } from '../components/PageContainer'
import {
  getCoverageMatrix,
  getSecurityPolicies,
  translatePolicy,
  runSimulation,
  getControlDependencies,
  getFindingExplanation,
  getPostureAnalytics,
} from '../api/configsentinel'
import type {
  CoverageMatrixResponse,
  SecurityPolicySchema,
  PolicyTranslationResultSchema,
  SimulationResultSchema,
  ControlDependencyNodeSchema,
  FindingExplanationSchema,
  PostureAnalyticsResponse,
} from '../types/api'

export function Intelligence() {
  const [activeTab, setActiveTab] = useState<'matrix' | 'policies' | 'simulator' | 'dependencies'>('matrix')

  // Coverage State
  const [coverageData, setCoverageData] = useState<CoverageMatrixResponse | null>(null)
  const [coverageLoading, setCoverageLoading] = useState(true)

  // Policies State
  const [policies, setPolicies] = useState<SecurityPolicySchema[]>([])
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>('')
  const [translationResult, setTranslationResult] = useState<PolicyTranslationResultSchema | null>(null)
  const [translating, setTranslating] = useState(false)

  // Simulator State
  const [simConfigText, setSimConfigText] = useState<string>(
    'hostname RTR-BORDER-01\nline vty 0 4\n transport input telnet ssh\n no service password-encryption'
  )
  const [simIntents, setSimIntents] = useState<string[]>(['TELNET_DISABLED', 'PASSWORD_ENCRYPTION_ENABLED'])
  const [simulationResult, setSimulationResult] = useState<SimulationResultSchema | null>(null)
  const [simulating, setSimulating] = useState(false)

  // Dependencies State
  const [dependencies, setDependencies] = useState<ControlDependencyNodeSchema[]>([])
  const [depsLoading, setDepsLoading] = useState(false)

  // Posture Analytics
  const [analytics, setAnalytics] = useState<PostureAnalyticsResponse | null>(null)

  // AI Explanation Drawer
  const [explanationModal, setExplanationModal] = useState<{
    open: boolean
    controlId: string
    controlName: string
    loading: boolean
    data: FindingExplanationSchema | null
  }>({
    open: false,
    controlId: '',
    controlName: '',
    loading: false,
    data: null,
  })

  useEffect(() => {
    // Load initial coverage & analytics
    setCoverageLoading(true)
    Promise.all([getCoverageMatrix(), getPostureAnalytics(), getSecurityPolicies()])
      .then(([cov, post, pols]) => {
        setCoverageData(cov)
        setAnalytics(post)
        setPolicies(pols.items)
        if (pols.items.length > 0) {
          setSelectedPolicyId(pols.items[0].id)
        }
      })
      .catch((err) => console.error('Failed loading intelligence overview:', err))
      .finally(() => setCoverageLoading(false))
  }, [])

  useEffect(() => {
    if (activeTab === 'dependencies' && (!dependencies || dependencies.length === 0)) {
      setDepsLoading(true)
      getControlDependencies()
        .then((res: any) => {
          const chains = res?.chains || res?.dependencies || []
          setDependencies(chains)
        })
        .catch((err) => {
          console.error('Failed loading dependencies:', err)
          setDependencies([])
        })
        .finally(() => setDepsLoading(false))
    }
  }, [activeTab, dependencies?.length])

  const handleTranslatePolicy = async () => {
    if (!selectedPolicyId) return
    setTranslating(true)
    try {
      const res = await translatePolicy({ policy_id: selectedPolicyId })
      setTranslationResult(res)
    } catch (err) {
      console.error('Failed policy translation:', err)
    } finally {
      setTranslating(false)
    }
  }

  const handleRunSimulation = async () => {
    if (!simConfigText.trim()) return
    setSimulating(true)
    try {
      const res = await runSimulation({
        config_text: simConfigText,
        intents_to_fix: simIntents,
      })
      setSimulationResult(res)
    } catch (err) {
      console.error('Failed simulation:', err)
    } finally {
      setSimulating(false)
    }
  }

  const handleFetchExplanation = async (controlId: string, controlName: string) => {
    setExplanationModal({ open: true, controlId, controlName, loading: true, data: null })
    try {
      const exp = await getFindingExplanation(controlId, { control_name: controlName })
      setExplanationModal({ open: true, controlId, controlName, loading: false, data: exp })
    } catch (err) {
      console.error('Failed fetching AI explanation:', err)
      setExplanationModal({ open: true, controlId, controlName, loading: false, data: null })
    }
  }

  const vendorsList = ['cisco', 'juniper', 'arista', 'fortios', 'panos']

  return (
    <PageContainer
      title="Cross-Vendor Security Intelligence"
      description="Vendor-neutral security semantics, cross-vendor capability matrices, policy translation, and deterministic what-if compliance simulation."
    >
      {/* Analytics Summary Banner */}
      {analytics && (
        <div className="cs-kpi-grid">
          <div className="cs-card" style={{ padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Intent Coverage Ratio
            </span>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--cs-accent)', marginTop: '0.25rem' }}>
              {(analytics.intent_support_ratio * 100).toFixed(0)}%
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-secondary)' }}>
              {analytics.total_supported_intents} of {analytics.total_intents} vendor intents supported
            </span>
          </div>

          {Object.entries(analytics.vendor_coverage).map(([vendor, cov]) => (
            <div key={vendor} className="cs-card" style={{ padding: '1.25rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                {vendor.toUpperCase()} Capability
              </span>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--cs-text-primary)', marginTop: '0.25rem' }}>
                {cov.evaluated} / {cov.total}
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-secondary)' }}>Evaluated Intents</span>
            </div>
          ))}
        </div>
      )}

      {/* Tab Navigation */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid var(--cs-border)',
          marginBottom: '1.5rem',
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab('matrix')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'matrix' ? '2px solid var(--cs-accent)' : '2px solid transparent',
            color: activeTab === 'matrix' ? 'var(--cs-accent)' : 'var(--cs-text-muted)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Control Coverage Matrix
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('policies')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'policies' ? '2px solid var(--cs-accent)' : '2px solid transparent',
            color: activeTab === 'policies' ? 'var(--cs-accent)' : 'var(--cs-text-muted)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Policy Translation
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('simulator')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'simulator' ? '2px solid var(--cs-accent)' : '2px solid transparent',
            color: activeTab === 'simulator' ? 'var(--cs-accent)' : 'var(--cs-text-muted)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          What-If Simulator
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('dependencies')}
          style={{
            padding: '0.625rem 1rem',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'dependencies' ? '2px solid var(--cs-accent)' : '2px solid transparent',
            color: activeTab === 'dependencies' ? 'var(--cs-accent)' : 'var(--cs-text-muted)',
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: 'pointer',
          }}
        >
          Control Chain & Attack Paths
        </button>
      </div>

      {/* Tab 1: Coverage Matrix */}
      {activeTab === 'matrix' && (
        <div className="cs-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cs-text-primary)', margin: 0 }}>
              Cross-Vendor Security Intent Matrix
            </h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)' }}>
              Deterministic support status derived from registered syntax parsers
            </span>
          </div>

          {coverageLoading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>Loading coverage matrix…</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--cs-border)' }}>
                    <th style={{ padding: '0.75rem', color: 'var(--cs-text-muted)', fontWeight: 600 }}>Security Intent</th>
                    <th style={{ padding: '0.75rem', color: 'var(--cs-text-muted)', fontWeight: 600 }}>Domain</th>
                    {vendorsList.map((v) => (
                      <th key={v} style={{ padding: '0.75rem', color: 'var(--cs-text-muted)', fontWeight: 600, textAlign: 'center' }}>
                        {v.toUpperCase()}
                      </th>
                    ))}
                    <th style={{ padding: '0.75rem', color: 'var(--cs-text-muted)', fontWeight: 600, textAlign: 'center' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {coverageData?.intents.map((intent) => (
                    <tr key={intent.id} style={{ borderBottom: '1px solid var(--cs-border-subtle)' }}>
                      <td style={{ padding: '0.75rem' }}>
                        <div style={{ fontWeight: 600, color: 'var(--cs-text-primary)' }}>{intent.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)', fontFamily: 'var(--cs-font-mono)' }}>
                          {intent.id}
                        </div>
                      </td>
                      <td style={{ padding: '0.75rem', color: 'var(--cs-text-secondary)', fontSize: '0.8125rem' }}>
                        {intent.security_domain}
                      </td>
                      {vendorsList.map((v) => {
                        const status = coverageData.matrix[intent.id]?.[v] || 'UNKNOWN'
                        return (
                          <td key={v} style={{ padding: '0.75rem', textAlign: 'center' }}>
                            <span
                              style={{
                                display: 'inline-block',
                                padding: '0.2rem 0.5rem',
                                borderRadius: '4px',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                backgroundColor:
                                  status === 'SUPPORTED'
                                    ? 'rgba(34, 197, 94, 0.15)'
                                    : status === 'PARTIAL'
                                    ? 'rgba(234, 179, 8, 0.15)'
                                    : status === 'UNSUPPORTED'
                                    ? 'rgba(239, 68, 68, 0.15)'
                                    : 'rgba(148, 163, 184, 0.15)',
                                color:
                                  status === 'SUPPORTED'
                                    ? '#22c55e'
                                    : status === 'PARTIAL'
                                    ? '#eab308'
                                    : status === 'UNSUPPORTED'
                                    ? '#ef4444'
                                    : '#94a3b8',
                              }}
                            >
                              {status === 'SUPPORTED' ? '✓ SUPPORTED' : status === 'PARTIAL' ? '⚠ PARTIAL' : status === 'UNSUPPORTED' ? '✕ UNSUPPORTED' : '? UNKNOWN'}
                            </span>
                          </td>
                        )
                      })}
                      <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                        <button
                          onClick={() => handleFetchExplanation(intent.related_control_ids[0] || intent.id, intent.name)}
                          style={{
                            padding: '0.25rem 0.5rem',
                            fontSize: '0.75rem',
                            backgroundColor: 'var(--cs-bg-elevated)',
                            color: 'var(--cs-accent)',
                            border: '1px solid var(--cs-border)',
                            borderRadius: '4px',
                            cursor: 'pointer',
                          }}
                        >
                          Explain AI
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Policy Translation */}
      {activeTab === 'policies' && (
        <div className="cs-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cs-text-primary)', marginBottom: '0.5rem' }}>
            Vendor-Neutral Security Policy Translation
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--cs-text-muted)', marginBottom: '1.5rem' }}>
            Translate high-level organizational security policy declarations into multi-vendor technical requirements.
          </p>

          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem' }}>
            <label style={{ fontSize: '0.875rem', color: 'var(--cs-text-secondary)', fontWeight: 500 }}>Select Policy:</label>
            <select
              value={selectedPolicyId}
              onChange={(e) => setSelectedPolicyId(e.target.value)}
              style={{
                padding: '0.5rem 0.75rem',
                backgroundColor: 'var(--cs-bg-elevated)',
                color: 'var(--cs-text-primary)',
                border: '1px solid var(--cs-border)',
                borderRadius: '6px',
                fontSize: '0.875rem',
                minWidth: '280px',
              }}
            >
              {policies.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <button
              onClick={handleTranslatePolicy}
              disabled={translating}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: 'var(--cs-accent)',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: translating ? 'not-allowed' : 'pointer',
              }}
            >
              {translating ? 'Translating…' : 'Translate Policy'}
            </button>
          </div>

          {translationResult && (
            <div style={{ marginTop: '1.5rem' }}>
              <div style={{ padding: '1rem', backgroundColor: 'var(--cs-bg-elevated)', borderRadius: '6px', marginBottom: '1.5rem' }}>
                <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1rem', color: 'var(--cs-accent)' }}>
                  {translationResult.policy_name}
                </h3>
                <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--cs-text-muted)' }}>
                  {translationResult.description}
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
                {translationResult.translations.map((trans) => (
                  <div key={trans.vendor} className="cs-card" style={{ padding: '1.25rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--cs-text-primary)' }}>
                        {trans.vendor.toUpperCase()}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)' }}>
                        {trans.supported_intents.length} Supported
                      </span>
                    </div>

                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--cs-text-muted)', marginBottom: '0.375rem' }}>
                        Syntax Directives & Status:
                      </div>
                      {trans.syntax_guidance.map((sg, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: '0.5rem',
                            backgroundColor: 'var(--cs-bg-surface)',
                            border: '1px solid var(--cs-border-subtle)',
                            borderRadius: '4px',
                            marginBottom: '0.375rem',
                            fontSize: '0.8125rem',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                            <span style={{ fontWeight: 600, color: 'var(--cs-text-primary)' }}>{sg.intent_id}</span>
                            <span
                              style={{
                                fontSize: '0.6875rem',
                                fontWeight: 700,
                                color: sg.status === 'SUPPORTED' ? '#22c55e' : '#ef4444',
                              }}
                            >
                              {sg.status}
                            </span>
                          </div>
                          <code style={{ fontFamily: 'var(--cs-font-mono)', color: 'var(--cs-accent)', fontSize: '0.75rem' }}>
                            {sg.syntax}
                          </code>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Simulator */}
      {activeTab === 'simulator' && (
        <div className="cs-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span
              style={{
                backgroundColor: 'rgba(234, 179, 8, 0.2)',
                color: '#eab308',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 700,
              }}
            >
              SIMULATION ISOLATED
            </span>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cs-text-primary)', margin: 0 }}>
              What-If Compliance Simulator
            </h2>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--cs-text-muted)', marginBottom: '1.5rem' }}>
            Simulate security posture impact when proposed security controls are remediated. Guaranteed read-only evaluation.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--cs-text-secondary)', marginBottom: '0.5rem' }}>
                Configuration Snippet:
              </label>
              <textarea
                value={simConfigText}
                onChange={(e) => setSimConfigText(e.target.value)}
                rows={8}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontFamily: 'var(--cs-font-mono)',
                  fontSize: '0.8125rem',
                  backgroundColor: 'var(--cs-bg-elevated)',
                  color: 'var(--cs-text-primary)',
                  border: '1px solid var(--cs-border)',
                  borderRadius: '6px',
                  resize: 'vertical',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, color: 'var(--cs-text-secondary)', marginBottom: '0.5rem' }}>
                Select Virtual Fixes (Intents to remediate):
              </label>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  maxHeight: '180px',
                  overflowY: 'auto',
                  padding: '0.75rem',
                  backgroundColor: 'var(--cs-bg-elevated)',
                  border: '1px solid var(--cs-border)',
                  borderRadius: '6px',
                }}
              >
                {[
                  { id: 'TELNET_DISABLED', name: 'Disable Telnet Management' },
                  { id: 'PASSWORD_ENCRYPTION_ENABLED', name: 'Enforce Secret Password Hashing' },
                  { id: 'SSH_VERSION_ENFORCED', name: 'Enforce SSH Version 2' },
                  { id: 'AAA_AUTHENTICATION_ENABLED', name: 'Enable AAA Authentication' },
                  { id: 'HTTP_MANAGEMENT_DISABLED', name: 'Disable Unencrypted HTTP Server' },
                ].map((item) => (
                  <label key={item.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={simIntents.includes(item.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSimIntents([...simIntents, item.id])
                        } else {
                          setSimIntents(simIntents.filter((id) => id !== item.id))
                        }
                      }}
                    />
                    <span style={{ color: 'var(--cs-text-primary)' }}>{item.name}</span>
                    <code style={{ fontSize: '0.7rem', color: 'var(--cs-text-muted)' }}>({item.id})</code>
                  </label>
                ))}
              </div>
              <button
                onClick={handleRunSimulation}
                disabled={simulating}
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
                  cursor: simulating ? 'not-allowed' : 'pointer',
                }}
              >
                {simulating ? 'Running Simulation…' : 'Run Simulation'}
              </button>
            </div>
          </div>

          {simulationResult && (
            <div
              style={{
                padding: '1.25rem',
                backgroundColor: 'var(--cs-bg-elevated)',
                border: '1px solid var(--cs-border)',
                borderRadius: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--cs-text-primary)' }}>
                  Simulation Outcome
                </span>
                <span
                  style={{
                    padding: '0.25rem 0.75rem',
                    borderRadius: '4px',
                    fontWeight: 700,
                    fontSize: '0.75rem',
                    backgroundColor:
                      simulationResult.security_impact === 'SECURITY_IMPROVEMENT'
                        ? 'rgba(34, 197, 94, 0.2)'
                        : 'rgba(148, 163, 184, 0.2)',
                    color: simulationResult.security_impact === 'SECURITY_IMPROVEMENT' ? '#22c55e' : '#94a3b8',
                  }}
                >
                  {simulationResult.security_impact}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', textAlign: 'center' }}>
                <div style={{ padding: '0.75rem', backgroundColor: 'var(--cs-bg-surface)', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)' }}>Original Failures</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--cs-fail)' }}>
                    {simulationResult.original_fail_count}
                  </div>
                </div>
                <div style={{ padding: '0.75rem', backgroundColor: 'var(--cs-bg-surface)', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)' }}>Projected Failures</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#22c55e' }}>
                    {simulationResult.projected_fail_count}
                  </div>
                </div>
                <div style={{ padding: '0.75rem', backgroundColor: 'var(--cs-bg-surface)', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)' }}>Original Risk Score</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--cs-text-primary)' }}>
                    {simulationResult.original_risk_score.toFixed(2)}
                  </div>
                </div>
                <div style={{ padding: '0.75rem', backgroundColor: 'var(--cs-bg-surface)', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)' }}>Projected Risk Score</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--cs-accent)' }}>
                    {simulationResult.projected_risk_score.toFixed(2)}
                  </div>
                </div>
              </div>

              <div style={{ marginTop: '1rem', fontSize: '0.8125rem', color: 'var(--cs-text-secondary)' }}>
                <strong>Resolved Control IDs:</strong>{' '}
                {simulationResult.resolved_control_ids.length > 0 ? simulationResult.resolved_control_ids.join(', ') : 'None'}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Dependencies */}
      {activeTab === 'dependencies' && (
        <div className="cs-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--cs-text-primary)', marginBottom: '0.5rem' }}>
            Security Control Dependencies & Risk Amplification
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--cs-text-muted)', marginBottom: '1.5rem' }}>
            Explicit deterministic relationships showing how weak controls amplify security risks across threat chains.
          </p>

          {depsLoading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>Loading control dependencies…</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
              {dependencies.map((chain) => (
                <div key={chain.control_id} className="cs-card" style={{ padding: '1.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--cs-accent)' }}>{chain.control_id}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--cs-text-muted)' }}>{chain.control_name}</span>
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--cs-text-secondary)', marginBottom: '0.75rem' }}>
                    <strong>Threat Scenario:</strong> {chain.threat_scenario}
                  </div>
                  {chain.amplifies.length > 0 && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--cs-fail)' }}>
                      <strong>Amplifies Risk to:</strong> {chain.amplifies.join(' → ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Bounded AI Explanation Modal */}
      {explanationModal.open && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            className="cs-card"
            style={{
              maxWidth: '550px',
              width: '100%',
              padding: '1.5rem',
              backgroundColor: 'var(--cs-bg-surface)',
              borderRadius: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.125rem', color: 'var(--cs-text-primary)' }}>
                Bounded AI Explanation — {explanationModal.controlId}
              </h3>
              <button
                onClick={() => setExplanationModal({ ...explanationModal, open: false })}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--cs-text-muted)',
                  fontSize: '1.25rem',
                  cursor: 'pointer',
                }}
              >
                ✕
              </button>
            </div>

            {explanationModal.loading ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
                Generating bounded security explanation…
              </div>
            ) : explanationModal.data ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.875rem' }}>
                <div>
                  <strong style={{ color: 'var(--cs-text-primary)' }}>Why It Matters:</strong>
                  <p style={{ margin: '0.25rem 0 0 0', color: 'var(--cs-text-secondary)' }}>{explanationModal.data.why_it_matters}</p>
                </div>
                <div>
                  <strong style={{ color: 'var(--cs-text-primary)' }}>Potential Impact:</strong>
                  <p style={{ margin: '0.25rem 0 0 0', color: 'var(--cs-text-secondary)' }}>{explanationModal.data.potential_impact}</p>
                </div>
                <div>
                  <strong style={{ color: 'var(--cs-text-primary)' }}>Recommended Remediation:</strong>
                  <p style={{ margin: '0.25rem 0 0 0', color: 'var(--cs-text-secondary)' }}>{explanationModal.data.recommended_remediation}</p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--cs-text-muted)' }}>
                  <span>Confidence: {explanationModal.data.confidence}</span>
                  <span>AI Authority: NO (Advisory Only)</span>
                </div>
              </div>
            ) : (
              <div style={{ color: 'var(--cs-fail)' }}>Failed to load explanation.</div>
            )}
          </div>
        </div>
      )}
    </PageContainer>
  )
}
