import { useState } from 'react'
import {
  useProposeMapping,
  useApproveMapping,
  useRejectMapping,
} from '../hooks/useDiscovery'
import type { UnknownPattern, SemanticMapping } from '../types/api'

interface Props {
  pattern: UnknownPattern | null
  onClose: () => void
}

export function MappingReviewDialog({ pattern, onClose }: Props) {
  const [proposal, setProposal] = useState<SemanticMapping | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const proposeMutation = useProposeMapping()
  const approveMutation = useApproveMapping()
  const rejectMutation = useRejectMapping()

  if (!pattern) return null

  const handlePropose = async () => {
    setErrorMsg(null)
    try {
      const res = await proposeMutation.mutateAsync(pattern.id)
      setProposal(res)
    } catch (err: any) {
      if (err?.error?.code === 'NOT_CONFIGURED') {
        setErrorMsg('AI Integration is not configured. Please check server settings.')
      } else {
        setErrorMsg('Failed to generate AI proposal.')
      }
    }
  }

  const handleApprove = async () => {
    if (!proposal) return
    try {
      await approveMutation.mutateAsync(proposal.id)
      onClose()
    } catch {
      setErrorMsg('Failed to approve mapping.')
    }
  }

  const handleReject = async () => {
    if (!proposal) return
    try {
      await rejectMutation.mutateAsync(proposal.id)
      onClose()
    } catch {
      setErrorMsg('Failed to reject mapping.')
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
      }}
    >
      <div
        style={{
          backgroundColor: 'var(--cs-bg-surface)',
          padding: '2rem',
          borderRadius: '8px',
          width: '100%',
          maxWidth: '600px',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}
      >
        <h2 style={{ marginTop: 0, color: 'var(--cs-text-primary)' }}>
          Review Discovery: {pattern.vendor}
        </h2>
        
        <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'var(--cs-bg-canvas)', borderRadius: '4px' }}>
          <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--cs-text-muted)' }}>Raw Directive</p>
          <pre style={{ margin: '0.5rem 0 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            {pattern.raw_directive}
          </pre>
          {pattern.section_context && (
            <>
              <p style={{ margin: '1rem 0 0 0', fontSize: '0.875rem', color: 'var(--cs-text-muted)' }}>Section Context</p>
              <pre style={{ margin: '0.5rem 0 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {pattern.section_context}
              </pre>
            </>
          )}
        </div>

        <div style={{ padding: '1rem', borderLeft: '4px solid var(--cs-warn)', backgroundColor: '#ffebe6', marginBottom: '1.5rem', color: '#bf2600', fontSize: '0.875rem' }}>
          <strong>Important:</strong> AI proposes translations only. The deterministic engine decides compliance. Do not rely on AI for PASS/FAIL or severity determination.
        </div>

        {errorMsg && (
          <div style={{ padding: '1rem', backgroundColor: '#ffebe6', color: '#bf2600', borderRadius: '4px', marginBottom: '1.5rem' }}>
            {errorMsg}
          </div>
        )}

        {!proposal && (
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button
              onClick={onClose}
              style={{ padding: '0.5rem 1rem', cursor: 'pointer', background: 'transparent', border: '1px solid var(--cs-border)', borderRadius: '4px' }}
            >
              Cancel
            </button>
            <button
              onClick={handlePropose}
              disabled={proposeMutation.isPending}
              style={{
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                background: 'var(--cs-accent)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                opacity: proposeMutation.isPending ? 0.7 : 1
              }}
            >
              {proposeMutation.isPending ? 'Generating...' : 'Generate AI Proposal'}
            </button>
          </div>
        )}

        {proposal && (
          <div style={{ borderTop: '1px solid var(--cs-border)', paddingTop: '1.5rem' }}>
            <h3 style={{ marginTop: 0 }}>AI Proposal</h3>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Proposed Key:</strong> {proposal.proposed_key}
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Proposed Value:</strong> {proposal.proposed_value || 'null'}
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <strong>Confidence:</strong> {proposal.confidence}
            </div>
            <div style={{ marginBottom: '1.5rem' }}>
              <strong>Explanation:</strong>
              <p style={{ margin: '0.5rem 0' }}>{proposal.explanation}</p>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button
                onClick={onClose}
                style={{ padding: '0.5rem 1rem', cursor: 'pointer', background: 'transparent', border: '1px solid var(--cs-border)', borderRadius: '4px' }}
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={rejectMutation.isPending || approveMutation.isPending}
                style={{ padding: '0.5rem 1rem', cursor: 'pointer', background: 'var(--cs-fail)', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
              </button>
              <button
                onClick={handleApprove}
                disabled={approveMutation.isPending || rejectMutation.isPending}
                style={{ padding: '0.5rem 1rem', cursor: 'pointer', background: 'var(--cs-pass)', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                {approveMutation.isPending ? 'Approving...' : 'Approve'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
