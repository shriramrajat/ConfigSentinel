import { useState } from 'react'
import { useDiscoveredPatterns } from '../hooks/useDiscovery'
import { MappingReviewDialog } from '../components/MappingReviewDialog'
import { StatusBadge } from '../components/StatusBadge'
import type { UnknownPattern } from '../types/api'

export function DiscoveryQueue() {
  const [page, setPage] = useState(0)
  const limit = 20
  
  const [vendorFilter, setVendorFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('PENDING')
  
  const { data, isLoading, isError } = useDiscoveredPatterns({
    limit,
    offset: page * limit,
    vendor: vendorFilter || undefined,
    status: statusFilter || undefined,
    sort_by: 'first_seen',
    sort_dir: 'desc',
  })

  const [selectedPattern, setSelectedPattern] = useState<UnknownPattern | null>(null)

  const handleNextPage = () => setPage(p => p + 1)
  const handlePrevPage = () => setPage(p => Math.max(0, p - 1))

  return (
    <div style={{ maxWidth: 'var(--cs-content-max)', margin: '0 auto', padding: '2rem 1.5rem' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--cs-text-primary)', margin: '0 0 0.5rem 0' }}>
          Discovery Queue
        </h1>
        <p style={{ color: 'var(--cs-text-muted)', margin: 0 }}>
          Review unknown configuration directives and assign AI-assisted semantic mappings.
        </p>
      </header>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Vendor</label>
          <select 
            value={vendorFilter} 
            onChange={(e) => { setVendorFilter(e.target.value); setPage(0); }}
            style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--cs-border)' }}
          >
            <option value="">All</option>
            <option value="cisco">Cisco</option>
            <option value="juniper">Juniper</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Status</label>
          <select 
            value={statusFilter} 
            onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
            style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--cs-border)' }}
          >
            <option value="">All</option>
            <option value="PENDING">Pending</option>
            <option value="MAPPED">Mapped</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div>Loading discovery queue...</div>
      ) : isError ? (
        <div style={{ color: 'var(--cs-fail)' }}>Failed to load discovery queue.</div>
      ) : (
        <>
          <div style={{ 
            backgroundColor: 'var(--cs-bg-surface)', 
            border: '1px solid var(--cs-border)', 
            borderRadius: '8px', 
            overflow: 'hidden' 
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--cs-border)', backgroundColor: 'var(--cs-bg-canvas)' }}>
                  <th style={{ padding: '1rem', fontSize: '0.875rem', fontWeight: 600 }}>Vendor</th>
                  <th style={{ padding: '1rem', fontSize: '0.875rem', fontWeight: 600 }}>Directive</th>
                  <th style={{ padding: '1rem', fontSize: '0.875rem', fontWeight: 600 }}>First Seen</th>
                  <th style={{ padding: '1rem', fontSize: '0.875rem', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '1rem', fontSize: '0.875rem', fontWeight: 600 }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid var(--cs-border)' }}>
                    <td style={{ padding: '1rem', fontSize: '0.875rem' }}>
                      <span style={{ textTransform: 'capitalize' }}>{item.vendor}</span>
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.875rem', fontFamily: 'monospace' }}>
                      {item.raw_directive.substring(0, 50)}
                      {item.raw_directive.length > 50 && '...'}
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.875rem', color: 'var(--cs-text-muted)' }}>
                      {new Date(item.first_seen).toLocaleString()}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <StatusBadge status={item.status as any} />
                    </td>
                    <td style={{ padding: '1rem' }}>
                      {item.status === 'PENDING' && (
                        <button
                          onClick={() => setSelectedPattern(item)}
                          style={{
                            padding: '0.25rem 0.75rem',
                            fontSize: '0.75rem',
                            backgroundColor: 'transparent',
                            border: '1px solid var(--cs-accent)',
                            color: 'var(--cs-accent)',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          Review
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {data?.items.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ padding: '2rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
                      No unknown directives found matching the filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
            <div style={{ fontSize: '0.875rem', color: 'var(--cs-text-muted)' }}>
              Showing {data?.items.length ? (page * limit) + 1 : 0} to {Math.min((page + 1) * limit, data?.total || 0)} of {data?.total || 0}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                onClick={handlePrevPage} 
                disabled={page === 0}
                style={{ padding: '0.5rem 1rem', border: '1px solid var(--cs-border)', background: 'transparent', borderRadius: '4px', cursor: page === 0 ? 'not-allowed' : 'pointer' }}
              >
                Previous
              </button>
              <button 
                onClick={handleNextPage} 
                disabled={!data || (page + 1) * limit >= data.total}
                style={{ padding: '0.5rem 1rem', border: '1px solid var(--cs-border)', background: 'transparent', borderRadius: '4px', cursor: (!data || (page + 1) * limit >= data.total) ? 'not-allowed' : 'pointer' }}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {selectedPattern && (
        <MappingReviewDialog 
          pattern={selectedPattern} 
          onClose={() => setSelectedPattern(null)} 
        />
      )}
    </div>
  )
}
