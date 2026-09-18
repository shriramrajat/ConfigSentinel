/**
 * src/api/configsentinel.ts
 *
 * Typed API functions for the ConfigSentinel backend.
 */

import { apiFetch } from './client'
import type {
  AuditRequest,
  AuditResponse,
  HealthResponse,
  VersionResponse,
  PaginatedUnknownPattern,
  SemanticMapping,
  AuditListResponse,
  DeviceDashboardResponse,
} from '../types/api'

// ---------------------------------------------------------------------------
// Health & Version
// ---------------------------------------------------------------------------

export async function healthCheck(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health')
}

export async function getVersion(): Promise<VersionResponse> {
  return apiFetch<VersionResponse>('/version')
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

export async function auditConfig(request: AuditRequest): Promise<AuditResponse> {
  return apiFetch<AuditResponse>('/api/v1/audit', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// ---------------------------------------------------------------------------
// Discovery & Mapping
// ---------------------------------------------------------------------------

export async function getDiscoveredPatterns(params: {
  vendor?: string
  status?: string
  limit?: number
  offset?: number
  sort_by?: string
  sort_dir?: string
}): Promise<PaginatedUnknownPattern> {
  const query = new URLSearchParams()
  if (params.vendor) query.append('vendor', params.vendor)
  if (params.status) query.append('status', params.status)
  if (params.limit !== undefined) query.append('limit', params.limit.toString())
  if (params.offset !== undefined) query.append('offset', params.offset.toString())
  if (params.sort_by) query.append('sort_by', params.sort_by)
  if (params.sort_dir) query.append('sort_dir', params.sort_dir)
  return apiFetch<PaginatedUnknownPattern>(`/api/v1/mappings/discovered?${query.toString()}`)
}

export async function proposeMapping(patternId: string): Promise<SemanticMapping> {
  return apiFetch<SemanticMapping>('/api/v1/mappings/propose', {
    method: 'POST',
    body: JSON.stringify({ pattern_id: patternId }),
  })
}

export async function approveMapping(mappingId: string): Promise<SemanticMapping> {
  return apiFetch<SemanticMapping>(`/api/v1/mappings/${mappingId}/approve`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

export async function rejectMapping(mappingId: string): Promise<SemanticMapping> {
  return apiFetch<SemanticMapping>(`/api/v1/mappings/${mappingId}/reject`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

// ---------------------------------------------------------------------------
// History & Device Dashboard
// ---------------------------------------------------------------------------

export async function listAudits(params: { vendor?: string; limit?: number; offset?: number } = {}): Promise<AuditListResponse> {
  const query = new URLSearchParams()
  if (params.vendor) query.append('vendor', params.vendor)
  if (params.limit !== undefined) query.append('limit', params.limit.toString())
  if (params.offset !== undefined) query.append('offset', params.offset.toString())
  return apiFetch<AuditListResponse>(`/api/v1/audits?${query.toString()}`)
}

export async function getAuditById(auditId: string): Promise<AuditResponse> {
  return apiFetch<AuditResponse>(`/api/v1/audits/${auditId}`)
}

export async function getDeviceDashboard(): Promise<DeviceDashboardResponse> {
  return apiFetch<DeviceDashboardResponse>('/api/v1/devices')
}
