# ConfigSentinel — Phase 1 Architectural Implementation Plan

**Author:** Lead Software Architect & Security Engineer  
**Status:** Phase 1 Plan (Approved Baseline: Phase 0 Complete, 536 Tests Passing)  
**Target:** SIH Problem Statement SIH26155 — Adaptive Network Security Platform  

---

## 1. Executive Summary & Architectural Overview

Phase 0 established a deterministic multi-vendor compliance engine (Cisco, Juniper, Arista, FortiOS, PAN-OS) with exact line-number evidence, pre-LLM credential redaction, strict AI schema validation, human-approval mapping, SQLite audit persistence, binary PDF reporting, and a React frontend.

Phase 1 elevates ConfigSentinel from a single-audit compliance scanner into an **Adaptive Security Intelligence Platform**.

### Core Principles
1. **Deterministic Security Authority:** Rules in `src/compliance/` remain the absolute source of truth for PASS/FAIL decisions, severity, and risk calculation.
2. **AI as Semantic Discovery Only:** AI translates unknown vendor syntax into standardized semantic categories; AI *never* evaluates compliance or risk.
3. **Mandatory Human Approval:** Discovered pattern proposals remain `PENDING` until explicitly approved by an operator.
4. **Audit Reproducibility:** Historical audits, drift events, and persistent findings maintain exact immutability—never recomputed on old data.

---

## 2. Current Architecture Baseline (Phase 0)

### 2.1 Component Boundaries
```text
[Raw Configuration]
        │
        ▼
[Ingestion & Vendor Detector] (detector.py)
        │
        ▼
[Vendor Parser Dispatch] (cisco.py, juniper.py, arista.py, fortios.py, panos.py)
        │
        ▼
[NormalizedConfig Model] (ConfigItem, ConfigSection, line_numbers)
        │
        ├──────────────────────────────────────────┐
        ▼                                          ▼
[Semantic Mapping Injection]             [Passive Unknown Pattern Discovery]
(service.py & mappings.db)               (unknown_patterns & LLMMapper)
        │                                          │
        └──────────────────┬───────────────────────┘
                           ▼
            [Deterministic Compliance Engine] (engine.py & RULE_REGISTRY)
                           │
                           ▼
            [Deterministic Risk Engine] (risk/engine.py: severity * confidence)
                           │
                           ├─────────────────────────┐
                           ▼                         ▼
            [SQLite Persistence] (audits.db)   [Binary PDF & REST API]
```

### 2.2 Data Store Baseline
- **`audits.db` (SQLite):** Table `audits` storing `id`, `vendor`, `hostname`, `source_name`, `created_at`, `fail_count`, `pass_count`, `total`, `result_json`.
- **`mappings.db` (SQLite):** Tables `unknown_patterns` and `semantic_mappings` managing pattern discovery and human-approval lifecycle.

---

## 3. Phase 1 Technical Roadmap & Milestones

Phase 1 is divided into 10 controlled, test-driven milestones:

```text
Milestone 1.1: Adaptive Semantic Learning Foundation & Taxonomy
Milestone 1.2: Mapping Confidence Tiers & Learning Analytics
Milestone 1.3: Cross-Audit Semantic Reuse & Versioning
Milestone 1.4: Compliance History & Posture Trend APIs
Milestone 1.5: Configuration Fingerprinting
Milestone 1.6: Configuration Drift & Semantic Change Detection
Milestone 1.7: Posture Change & Degradation Detection
Milestone 1.8: Finding Lifecycle Management (OPEN/ACKNOWLEDGED/RESOLVED)
Milestone 1.9: Historical Intelligence & Finding Lifecycle Frontend
Milestone 1.10: Integration & Full Regression Verification
```

---

## 4. Extended Schema & Database Design

To support Phase 1 capabilities, SQLite schemas in `audits.db` and `mappings.db` (or unified `configsentinel.db`) will be extended cleanly:

### 4.1 `mappings.db` Extensions
- **`semantic_taxonomy` / Enum:** Controlled taxonomy (`SSH_SECURITY`, `TELNET_SECURITY`, `AAA_AUTHENTICATION`, `PASSWORD_SECURITY`, `SESSION_TIMEOUT`, `LOGGING`, `NTP_TIME_SYNC`, `SNMP_SECURITY`, `HTTP_MANAGEMENT`, `SERVICE_HARDENING`, `ACCESS_CONTROL`, `CRYPTOGRAPHY`, `BANNER_SECURITY`, `OTHER`).
- **`semantic_mappings` Table Additions:**
  - `semantic_category TEXT` (Typed category from taxonomy)
  - `mapping_version INTEGER DEFAULT 1`
  - `usage_count INTEGER DEFAULT 0`
  - `last_used_at TEXT`
  - `approved_by TEXT`

### 4.2 `audits.db` Additions
- **`config_fingerprints` Table:**
  - `id TEXT PRIMARY KEY`, `device_id TEXT`, `audit_id TEXT`, `sha256 TEXT`, `created_at TEXT`.
- **`drift_events` Table:**
  - `id TEXT PRIMARY KEY`, `device_id TEXT`, `previous_audit_id TEXT`, `current_audit_id TEXT`, `timestamp TEXT`, `change_type TEXT` (`ADDED` | `REMOVED` | `MODIFIED`), `raw_line TEXT`, `security_impact TEXT` (`IMPROVEMENT` | `DEGRADATION` | `NEUTRAL`), `affected_control_id TEXT`.
- **`security_findings` Table:**
  - `id TEXT PRIMARY KEY`, `fingerprint TEXT UNIQUE` (`device_id + control_id + line_identifier`), `device_id TEXT`, `control_id TEXT`, `severity TEXT`, `status TEXT` (`OPEN` | `ACKNOWLEDGED` | `RESOLVED`), `first_seen TEXT`, `last_seen TEXT`, `occurrence_count INTEGER`, `resolved_at TEXT`, `acknowledged_at TEXT`, `evidence_json TEXT`, `remediation_json TEXT`.

---

## 5. API Extensions

```text
# Learning & Analytics
GET  /api/v1/mappings/stats          — Mapping learning analytics & reuse metrics
GET  /api/v1/mappings/taxonomy       — Allowed semantic categories

# Historical Posture & Trends
GET  /api/v1/audits/trends           — System-wide compliance & risk trends over time
GET  /api/v1/devices/{device_id}/history — Per-device historical audit timeline

# Drift & Posture Delta
GET  /api/v1/devices/{device_id}/drift   — Configuration & semantic drift events
GET  /api/v1/devices/{device_id}/posture — Posture delta between audits

# Finding Lifecycle
GET  /api/v1/findings                — Query persistent findings (filter by status, severity, device)
GET  /api/v1/findings/{finding_id}   — Detailed finding record
POST /api/v1/findings/{finding_id}/acknowledge — Mark finding acknowledged
POST /api/v1/findings/{finding_id}/resolve     — Mark finding resolved
POST /api/v1/findings/{finding_id}/reopen      — Reopen resolved finding
```

---

## 6. Testing & Backward Compatibility Strategy

1. **Zero Test Regressions:** All existing 536 Phase 0 backend unit and integration tests must pass continuously after every milestone.
2. **Deterministic Security Integrity:** Unit tests will verify that AI predictions never override deterministic rule outputs.
3. **Frontend Build Integrity:** `npm --prefix frontend run build` must compile with 0 TypeScript/Vite errors at every frontend milestone.
4. **Database Migration Safety:** Table alterations and new table initializations will use `CREATE TABLE IF NOT EXISTS` and defensive column checks to ensure smooth local and production upgrades.
