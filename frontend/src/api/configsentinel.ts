/**
 * src/api/configsentinel.ts
 *
 * Typed API functions for the ConfigSentinel backend.
 *
 * Every function in this file corresponds to one backend endpoint.
 * Components and hooks must use these functions — never call apiFetch directly
 * from a component or page.
 *
 * Endpoints covered:
 *   GET  /health          → healthCheck()
 *   GET  /version         → getVersion()
 *   POST /api/v1/audit    → auditConfig()
 */

import { apiFetch } from './client'
import type {
  AuditRequest,
  AuditResponse,
  HealthResponse,
  VersionResponse,
  PaginatedUnknownPattern,
  SemanticMapping,
} from '../types/api'

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

/**
 * Check if the ConfigSentinel backend is reachable.
 *
 * Use before any user-initiated audit to surface a clear "backend unavailable"
 * message rather than a cryptic network error.
 */
export async function healthCheck(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health')
}

// ---------------------------------------------------------------------------
// Version
// ---------------------------------------------------------------------------

/**
 * Retrieve product name and API version from the backend.
 *
 * Useful for displaying version info in footers or about screens.
 */
export async function getVersion(): Promise<VersionResponse> {
  return apiFetch<VersionResponse>('/version')
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

/**
 * Submit raw network device configuration text for compliance auditing.
 *
 * The backend automatically detects the vendor (Cisco or Juniper) and
 * evaluates all active compliance controls. Returns a structured report
 * with per-control results, evidence, and remediation guidance.
 *
 * Rules the frontend must follow:
 *  - Submit the raw config text exactly as the user provided it.
 *  - Do NOT pre-process or parse the configuration text.
 *  - Do NOT derive compliance status from the returned evidence fields.
 *  - Do NOT invent security scores from the summary counts.
 *  - Treat status "not_applicable" as neutral — not a failure.
 *  - Treat evidence.raw_lines as text snippets only — not line numbers.
 *  - Display config_hint with a clear "advisory only" label.
 *
 * @param request - The audit request with config_text and optional source_name.
 * @returns AuditResponse with summary and per-control results.
 * @throws ApiError if the backend returns a non-2xx response.
 */
export async function auditConfig(request: AuditRequest): Promise<AuditResponse> {
  return apiFetch<AuditResponse>('/api/v1/audit', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// ---------------------------------------------------------------------------
// Discovery & Mapping
// ---------------------------------------------------------------------------

export async function getDiscoveredPatterns(params: { vendor?: string; status?: string; limit?: number; offset?: number; sort_by?: string; sort_dir?: string }): Promise<PaginatedUnknownPattern> {
  const query = new URLSearchParams()
  if (params.vendor) query.append("vendor", params.vendor)
  if (params.status) query.append("status", params.status)
  if (params.limit !== undefined) query.append("limit", params.limit.toString())
  if (params.offset !== undefined) query.append("offset", params.offset.toString())
  if (params.sort_by) query.append("sort_by", params.sort_by)
  if (params.sort_dir) query.append("sort_dir", params.sort_dir)
  return apiFetch<PaginatedUnknownPattern>(`/api/v1/mappings/discovered?${query.toString()}`)
}

export async function proposeMapping(patternId: string): Promise<SemanticMapping> {
  return apiFetch<SemanticMapping>("/api/v1/mappings/propose", {
    method: "POST",
    body: JSON.stringify({ pattern_id: patternId }),
  })
}

export async function approveMapping(mappingId: string): Promise<SemanticMapping> {
  return apiFetch<SemanticMapping>(`/api/v1/mappings/${mappingId}/approve`, {
    method: "POST",
    body: JSON.stringify({}),
  })
}

export async function rejectMapping(mappingId: string): Promise<SemanticMapping> {
  return apiFetch<SemanticMapping>(`/api/v1/mappings/${mappingId}/reject`, {
    method: "POST",
    body: JSON.stringify({}),
  })
}
