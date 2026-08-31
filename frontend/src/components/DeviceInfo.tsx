/**
 * src/components/DeviceInfo.tsx
 *
 * Displays identifying information about the audited configuration.
 * Only uses data explicitly returned by the API response.
 */

import type { AuditSummary } from '../types/api'

interface DeviceInfoProps {
  summary: AuditSummary
}

export function DeviceInfo({ summary }: DeviceInfoProps) {
  const { vendor, hostname, source_name, total_controls } = summary

  return (
    <div
      style={{
        backgroundColor: 'var(--cs-bg-surface)',
        border: '1px solid var(--cs-border)',
        borderRadius: 'var(--cs-radius-md)',
        padding: '1rem 1.25rem',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '2rem',
        rowGap: '1rem',
      }}
    >
      <DeviceInfoItem label="Vendor" value={vendor} mono />

      {hostname ? (
        <DeviceInfoItem label="Hostname" value={hostname} mono />
      ) : (
        <DeviceInfoItem label="Hostname" value="Unknown" muted />
      )}

      {source_name && (
        <DeviceInfoItem label="Source" value={source_name} />
      )}

      <DeviceInfoItem label="Controls evaluated" value={String(total_controls)} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Internal helper
// ---------------------------------------------------------------------------

function DeviceInfoItem({
  label,
  value,
  mono = false,
  muted = false,
}: {
  label: string
  value: string
  mono?: boolean
  muted?: boolean
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
      <span
        style={{
          fontFamily: 'var(--cs-font-sans)',
          fontSize: '0.6875rem',
          fontWeight: 500,
          color: 'var(--cs-text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontFamily: mono ? 'var(--cs-font-mono)' : 'var(--cs-font-sans)',
          fontSize: '0.875rem',
          color: muted ? 'var(--cs-text-muted)' : 'var(--cs-text-primary)',
          fontWeight: mono ? 400 : 500,
        }}
      >
        {value}
      </span>
    </div>
  )
}
