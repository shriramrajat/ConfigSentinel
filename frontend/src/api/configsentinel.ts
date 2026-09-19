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

// ---------------------------------------------------------------------------
// Phase 1 API Functions: Analytics, History Trends, Drift, Posture & Findings
// ---------------------------------------------------------------------------

export async function getMappingStats(): Promise<import('../types/api').MappingStats> {
  return apiFetch<import('../types/api').MappingStats>('/api/v1/mappings/stats')
}

export async function getMappingUsage(): Promise<{ items: import('../types/api').MappingUsageItem[] }> {
  return apiFetch<{ items: import('../types/api').MappingUsageItem[] }>('/api/v1/mappings/usage')
}

export async function getAuditTrends(limit = 30): Promise<import('../types/api').AuditTrendsResponse> {
  return apiFetch<import('../types/api').AuditTrendsResponse>(`/api/v1/audits/trends?limit=${limit}`)
}

export async function getDeviceHistory(deviceId: string, limit = 50): Promise<import('../types/api').DeviceHistoryResponse> {
  return apiFetch<import('../types/api').DeviceHistoryResponse>(`/api/v1/devices/${encodeURIComponent(deviceId)}/history?limit=${limit}`)
}

export async function getDeviceDrift(deviceId: string): Promise<import('../types/api').DeviceDriftResponse> {
  return apiFetch<import('../types/api').DeviceDriftResponse>(`/api/v1/devices/${encodeURIComponent(deviceId)}/drift`)
}

export async function getDevicePosture(deviceId: string): Promise<import('../types/api').PostureDeltaResponse> {
  return apiFetch<import('../types/api').PostureDeltaResponse>(`/api/v1/devices/${encodeURIComponent(deviceId)}/posture`)
}

export async function listFindings(params: {
  device_id?: string
  status?: string
  severity?: string
  limit?: number
  offset?: number
} = {}): Promise<import('../types/api').FindingsListResponse> {
  const query = new URLSearchParams()
  if (params.device_id) query.append('device_id', params.device_id)
  if (params.status) query.append('status', params.status)
  if (params.severity) query.append('severity', params.severity)
  if (params.limit !== undefined) query.append('limit', params.limit.toString())
  if (params.offset !== undefined) query.append('offset', params.offset.toString())
  return apiFetch<import('../types/api').FindingsListResponse>(`/api/v1/findings?${query.toString()}`)
}

export async function getFindingById(findingId: string): Promise<import('../types/api').SecurityFinding> {
  return apiFetch<import('../types/api').SecurityFinding>(`/api/v1/findings/${encodeURIComponent(findingId)}`)
}

export async function acknowledgeFinding(findingId: string): Promise<import('../types/api').SecurityFinding> {
  return apiFetch<import('../types/api').SecurityFinding>(`/api/v1/findings/${encodeURIComponent(findingId)}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

export async function resolveFinding(findingId: string): Promise<import('../types/api').SecurityFinding> {
  return apiFetch<import('../types/api').SecurityFinding>(`/api/v1/findings/${encodeURIComponent(findingId)}/resolve`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

export async function reopenFinding(findingId: string): Promise<import('../types/api').SecurityFinding> {
  return apiFetch<import('../types/api').SecurityFinding>(`/api/v1/findings/${encodeURIComponent(findingId)}/reopen`, {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

