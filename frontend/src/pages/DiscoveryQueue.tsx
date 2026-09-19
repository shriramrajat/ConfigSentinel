import { useState } from 'react'
import { useDiscoveredPatterns } from '../hooks/useDiscovery'
import { MappingReviewDialog } from '../components/MappingReviewDialog'
import { StatusBadge } from '../components/StatusBadge'
import { PageContainer } from '../components/PageContainer'
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
    <PageContainer
      title="Discovery Queue"
      description="Review unknown configuration directives and assign AI-assisted semantic mappings."
    >
      <div
        className="cs-card"
        style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '1.5rem',
          alignItems: 'center',
          flexWrap: 'wrap',
          padding: '1rem 1.25rem',
        }}
      >
        <div style={{ flex: '1 1 140px', minWidth: '120px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--cs-text-muted)', marginBottom: '0.25rem', fontWeight: 500 }}>Vendor</label>
          <select 
            className="cs-select"
            value={vendorFilter} 
            onChange={(e) => { setVendorFilter(e.target.value); setPage(0); }}
          >
            <option value="">All Vendors</option>
            <option value="cisco">Cisco</option>
            <option value="juniper">Juniper</option>
            <option value="arista">Arista</option>
            <option value="fortios">FortiOS</option>
            <option value="panos">PAN-OS</option>
          </select>
        </div>
        <div style={{ flex: '1 1 140px', minWidth: '120px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--cs-text-muted)', marginBottom: '0.25rem', fontWeight: 500 }}>Status</label>
          <select 
            className="cs-select"
            value={statusFilter} 
            onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
          >
            <option value="">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="MAPPED">Mapped</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="cs-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
          Loading discovery queue...
        </div>
      ) : isError ? (
        <div style={{ padding: '1rem 1.25rem', backgroundColor: 'var(--cs-fail-bg)', color: 'var(--cs-fail)', border: '1px solid var(--cs-fail-border)', borderRadius: 'var(--cs-radius)', marginBottom: '1.5rem' }}>
          Failed to load discovery queue.
        </div>
      ) : (
        <>
          <div className="cs-table-container">
            <table className="cs-table">
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Directive</th>
                  <th>First Seen</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{item.vendor}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--cs-font-mono)', color: 'var(--cs-text-code)' }}>
                      {item.raw_directive.substring(0, 60)}
                      {item.raw_directive.length > 60 && '...'}
                    </td>
                    <td style={{ color: 'var(--cs-text-muted)', fontSize: '0.75rem' }}>
                      {new Date(item.first_seen).toLocaleString()}
                    </td>
                    <td>
                      <StatusBadge status={item.status as any} />
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {item.status === 'PENDING' && (
                        <button
                          onClick={() => setSelectedPattern(item)}
                          className="cs-btn-ghost"
                          style={{ height: '1.875rem', padding: '0 0.625rem', fontSize: '0.75rem', color: 'var(--cs-accent)', borderColor: 'var(--cs-accent-muted)' }}
                        >
                          Review
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {data?.items.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ padding: '3rem', textAlign: 'center', color: 'var(--cs-text-muted)' }}>
                      No unknown directives found matching the filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem' }}>
            <div style={{ fontSize: '0.875rem', color: 'var(--cs-text-muted)' }}>
              Showing {data?.items.length ? (page * limit) + 1 : 0} to {Math.min((page + 1) * limit, data?.total || 0)} of {data?.total || 0}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                onClick={handlePrevPage} 
                disabled={page === 0}
                className="cs-btn-ghost"
              >
                Previous
              </button>
              <button 
                onClick={handleNextPage} 
                disabled={!data || (page + 1) * limit >= data.total}
                className="cs-btn-primary"
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
    </PageContainer>
  )
}
