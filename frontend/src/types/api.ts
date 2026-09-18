/**
 * src/types/api.ts
 *
 * TypeScript type definitions that exactly mirror the ConfigSentinel backend
 * Pydantic schemas (src/api/schemas.py) and the frontend contract in
 * docs/FRONTEND.md.
 *
 * Rules enforced here:
 *  - Do NOT add fields that don't exist in the backend response.
 *  - Do NOT invent security scores, fabricated line numbers, or derived metrics.
 *  - Do NOT add status or severity values beyond what the backend defines.
 *  - If the backend changes a field, update this file to match — do not paper
 *    over the mismatch in components.
 *
 * Source of truth: docs/FRONTEND.md §4, §6, and src/api/schemas.py
 */

// ---------------------------------------------------------------------------
// Shared enumerations
// ---------------------------------------------------------------------------

/** Compliance evaluation outcome for a single control. */
export type ComplianceStatus =
  | 'pass'
  | 'fail'
  | 'not_applicable'
  | 'needs_review'

/**
 * Business-impact severity of a security control.
 * Severity is a static property of the CONTROL, not the finding.
 * A PASS result still has a severity — it communicates how important that
 * control is, not whether it failed.
 */
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'

/** Detected vendor identifier returned by the backend. */
export type Vendor = 'cisco' | 'juniper' | 'unknown'

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

/**
 * Request body for POST /api/v1/audit.
 *
 * The frontend submits raw configuration text. The backend is responsible
 * for vendor detection and parsing — the frontend must NOT pre-process
 * the configuration text.
 */
export interface AuditRequest {
  /** Raw device configuration text. Must be non-empty. */
  config_text: string
  /**
   * Optional human-readable label for traceability (e.g. filename or
   * device name). Not used for parsing decisions.
   */
  source_name?: string
}

// ---------------------------------------------------------------------------
// Response sub-types
// ---------------------------------------------------------------------------

/**
 * Evidence linking a compliance decision back to the configuration.
 *
 * IMPORTANT — traceability limitation:
 * `raw_lines` contains verbatim configuration text snippets, NOT line numbers.
 * The backend does not track byte offsets or line numbers. Do not fabricate
 * line numbers from `raw_lines` content.
 */
export interface Evidence {
  /** Control this evidence belongs to (e.g. "SSH-001"). */
  control_id: string
  /** Config section the item was drawn from, or null for global items. */
  section_name: string | null
  /**
   * Verbatim configuration line(s) used by the rule.
   * Empty array signals absence evidence (the directive was not found).
   * These are text snippets — exact line numbers are NOT available.
   */
  raw_lines: string[]
  /** Value the rule actually found. null when the directive was absent. */
  observed: string | null
  /** Value or condition the rule required. null when not applicable. */
  expected: string | null
  /** Human-readable explanation of why the rule reached its conclusion. */
  note: string
}

/**
 * Corrective guidance for a non-compliant control.
 *
 * WARNING: config_hint is ADVISORY ONLY. It must NEVER be applied
 * automatically. Display it as a read-only example with a clear label.
 */
export interface Remediation {
  /** Target vendor, e.g. "cisco". "any" means all vendors. */
  vendor: string
  /** Actionable plain-English instructions. */
  guidance: string
  /**
   * Example configuration snippet illustrating the required change.
   * Advisory only — must NOT be applied automatically.
   */
  config_hint: string | null
}

/** Result produced by a single compliance rule evaluation. */
export interface ComplianceResult {
  /** Unique control identifier (e.g. "SSH-001"). */
  control_id: string
  /** Short human-readable control name (e.g. "SSH Protocol Version"). */
  control_name: string
  /** Plain-English description of what the control checks. */
  description: string
  severity: Severity
  /**
   * Compliance outcome.
   * IMPORTANT: `not_applicable` is NOT a failure. The control simply
   * does not apply to this vendor.
   */
  status: ComplianceStatus
  /** Vendor identifier from the evaluated configuration. */
  vendor: string
  /** Device hostname from the configuration, or null if absent. */
  hostname: string | null
  evidence: Evidence[]
  /**
   * Corrective guidance. Empty array when status === "pass".
   * config_hint fields are advisory only — never auto-apply.
   */
  remediations: Remediation[]
  /** Compliance framework references (e.g. ["CIS-IOS-L2-1.1.1", "NIST-AC-17(2)"]). */
  framework_refs: string[]
}

/**
 * High-level audit summary for dashboard display.
 *
 * All counts are derived from actual ComplianceResult values.
 * No scores or security metrics are invented beyond what the results contain.
 * DO NOT calculate a "security score" from these numbers.
 */
export interface AuditSummary {
  /** Detected vendor: "cisco" | "juniper" | "unknown" */
  vendor: string
  /** Device hostname from the configuration, or null. */
  hostname: string | null
  /** Echoes the request source_name, or null. */
  source_name: string | null
  /** Total number of controls evaluated. */
  total_controls: number
  /** Controls with status "pass". */
  pass_count: number
  /** Controls with status "fail". */
  fail_count: number
  /** Controls with status "needs_review". */
  needs_review_count: number
  /**
   * Controls with status "not_applicable".
   * NOT a failure count — these controls simply don't apply to this vendor.
   */
  not_applicable_count: number
  /**
   * Count of controls per severity tier (critical/high/medium/low/info).
   * Includes ALL statuses — use pass/fail counts for compliance posture.
   */
  severity_distribution: Record<string, number>
}

/** Complete response from POST /api/v1/audit. */
export interface AuditResponse {
  summary: AuditSummary
  results: ComplianceResult[]
}

// ---------------------------------------------------------------------------
// Version / Health types
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: 'ok'
}

export interface VersionResponse {
  product: string
  version: string
  description: string
}

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

/** Inner error object returned by the backend on all error responses. */
// ---------------------------------------------------------------------------
// Mapping & Discovery types
// ---------------------------------------------------------------------------

export interface UnknownPattern {
  id: string
  vendor: string
  raw_directive: string
  source_name: string | null
  section_context: string | null
  status: 'PENDING' | 'MAPPED' | 'REJECTED'
  first_seen: string
}

export interface PaginatedUnknownPattern {
  items: UnknownPattern[]
  total: number
  limit: number
  offset: number
}

export interface SemanticMapping {
  id: string
  pattern_id: string
  original_syntax: string
  proposed_key: string
  proposed_value: string | null
  explanation: string
  confidence: number
  approval_state: 'PENDING' | 'APPROVED' | 'REJECTED'
  created_at: string
  updated_at: string
}

export interface ErrorDetail {
  /**
   * Machine-readable error code.
   * One of: "INVALID_INPUT" | "VALIDATION_ERROR" | "INTERNAL_ERROR"
   */
  code: string
  /** Human-readable message. Safe to display in the UI. */
  message: string
}

/** Envelope for all error responses from the backend. */
export interface ErrorResponse {
  error: ErrorDetail
}

export interface AuditListItem {
  id: string
  vendor: string
  hostname: string | null
  source_name: string | null
  created_at: string
  fail_count: number
  pass_count: number
  total: number
}

export interface AuditListResponse {
  total: number
  limit: number
  offset: number
  items: AuditListItem[]
}

export interface DeviceSummary {
  device: string
  vendor: string
  audit_count: number
  last_audit: string
  total_fails: number
  total_passes: number
  total_controls: number
}

export interface DeviceDashboardResponse {
  devices: DeviceSummary[]
}

