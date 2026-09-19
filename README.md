# ConfigSentinel

AI-Assisted Vendor-Agnostic Network Configuration Security & Compliance Operations Platform

Problem Statement: **SIH 26155** (National Technical Research Organisation - NTRO)

---

## Architecture Overview

```
Raw Configuration Text / Multi-Device Uploads
        ↓
Vendor Detection & Registration
        ↓
Vendor Parser (Cisco, Juniper, Arista, FortiOS, PAN-OS)
        ↓
NormalizedConfig Model
        ↓
Deterministic Compliance Engine (Rule Registry)
        ↓
Risk Engine / Findings Lifecycle / Evidence / PDF Report
        ↓
Cross-Vendor Security Intelligence & What-If Simulation
        ↓
Fleet Inventory / Priority Risk Queue / Baseline Drift / Remediation Verification
        ↓
Bounded Natural-Language Query Layer & Operations Dashboard
```

---

## Supported Vendors

- **Cisco IOS / IOS-XE**
- **Juniper JunOS**
- **Arista EOS**
- **Fortinet FortiOS**
- **Palo Alto PAN-OS**

---

## Core Capabilities & Features

### 1. Deterministic Compliance Core
- **Authoritative Compliance:** Rules in `src/compliance/` are 100% source of truth for `PASS`, `FAIL`, `NEEDS_REVIEW`, and `NOT_APPLICABLE`.
- **Line-Number Evidence:** Exact configuration line numbers linked directly to observed vs. expected evidence snippets.
- **14 Active Rules:** Covering SSH hardening, Telnet prohibition, VTY session timeouts, secret password encryption, remote AAA authentication, HTTP web management, remote syslog logging, NTP time synchronization, SNMP community security, banner policies, timezone enforcement, and unnecessary services.

### 2. Risk Engine & Finding Lifecycle
- **Deterministic Risk Scoring:** Derived from severity and confidence factors.
- **Finding Lifecycle:** Persistent SQLite tracking of security findings across `OPEN`, `ACKNOWLEDGED`, and `RESOLVED` states with deduplication fingerprints.
- **Configuration Fingerprinting & Drift Detection:** Detailed structural configuration diffs and posture trend tracking across successive audits.

### 3. Adaptive Semantic Mapping & AI Boundary
- **Unknown Syntax Discovery:** Automatically captures unknown CLI directives into a review queue.
- **Adaptive LLM Proposal:** Proposes semantic normalization keys for unknown CLI directives.
- **Human-in-the-Loop Governance:** AI proposals require explicit human approval before being persisted and reused.
- **Pre-LLM Secret Redaction:** All passphrases, secrets, and private keys are redacted before sending data to LLM APIs.
- **Strict Schema Enforcement:** All LLM outputs use Pydantic v2 schemas with `extra="forbid"`.

### 4. Cross-Vendor Security Intelligence (Phase 2)
- **Vendor-Neutral Security Intents:** Canonical security intent definitions (e.g. `TELNET_DISABLED`, `SSH_VERSION_ENFORCED`, `PASSWORD_ENCRYPTION_ENABLED`, `AAA_AUTHENTICATION_ENABLED`).
- **Control Coverage Matrix:** Dynamic cross-vendor capability matrix reflecting actual parser capabilities.
- **Security Policy Translation:** Translates high-level organizational security policy declarations into vendor-specific CLI configuration requirements.
- **What-If Compliance Simulator:** Deterministic simulation engine predicting projected compliance scores and risk reduction without mutating original audit data or history.
- **Bounded AI Security Explanations:** Plain-English explanations of findings and risk impacts with pre-canned deterministic fallbacks.
- **Security Control Dependency Chains:** Deterministic threat scenario models demonstrating risk amplification paths.

### 5. Production Security Operations (Phase 3)
- **Fleet Device Inventory:** SQLite device registry with environment tagging (`PRODUCTION`, `DMZ`, `CORE`, `STAGING`, `LAB`) and posture state.
- **Operator Priority Queue:** Ranks findings into priority tiers (P1 Critical -> P4 Low) based on deterministic risk, recurrence, and attack chain amplifications.
- **Remediation Intelligence & Verification:** Multi-vendor remediation guidance across 5 vendors + post-fix audit comparator producing `FIX VERIFIED` or `FIX NOT VERIFIED`.
- **Immutable Configuration Baselines:** Versioned baselines (v1, v2) with structural drift detection.
- **Bounded Natural-Language Security Query Layer:** Plain English search translated strictly to Pydantic schemas; blocks SQL injection attempts.
- **Security Operations Dashboard:** Integrated React UI (`frontend/src/pages/Operations.tsx`) for fleet inventory, priority queue, remediation verification, and NL search.
- **Operational Exports & Webhooks:** JSON/CSV exporters + sanitized SIEM webhook notification dispatcher.
- **Production Hardening:** Audit trail logger, Zip Slip path extraction bounds, file upload bounds, and security middleware.

---

## AI Governance & Boundaries

> [!IMPORTANT]
> **AI IS NOT THE COMPLIANCE AUTHORITY.**
> AI does NOT determine PASS/FAIL status.
> AI does NOT assign or modify severity tiers.
> AI does NOT calculate risk scores.
> AI does NOT generate or execute raw SQL.
> AI serves strictly as an advisory assistant for unknown pattern normalization mapping proposals, plain-English finding explanations, and natural-language query parameter extraction.

---

## Technology Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy / SQLite, ReportLab
- **Frontend:** React 18, TypeScript, Vite, React Router, Vanilla CSS design system
- **Testing:** Pytest (566 passing tests)

---

## Quick Start & Verification

### Running Backend Tests
```bash
python -m pytest tests/ --tb=short -q
```
*Expected: 566 passed*

### Building Frontend Bundle
```bash
npm --prefix frontend run build
```
*Expected: Built cleanly in `dist/`*

### Starting Application
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 10000
```
Open Swagger UI: `http://localhost:10000/docs`

---

## Documentation Index

- [`docs/PHASE3_IMPLEMENTATION_PLAN.md`](docs/PHASE3_IMPLEMENTATION_PLAN.md) — Phase 3 Architecture & Plan
- [`docs/PHASE3_IMPLEMENTATION_STATUS.md`](docs/PHASE3_IMPLEMENTATION_STATUS.md) — Phase 3 Implementation Matrix
- [`docs/SECURITY_OPERATIONS.md`](docs/SECURITY_OPERATIONS.md) — Security Operations Architecture
- [`docs/REMEDIATION_MODEL.md`](docs/REMEDIATION_MODEL.md) — Remediation & Verification Model
- [`docs/QUERY_SECURITY.md`](docs/QUERY_SECURITY.md) — Bounded Query Security & Sanitization
- [`docs/CROSS_VENDOR_INTELLIGENCE.md`](docs/CROSS_VENDOR_INTELLIGENCE.md) — Cross-Vendor Semantic Architecture
- [`docs/AI_GOVERNANCE.md`](docs/AI_GOVERNANCE.md) — Strict AI Security Boundaries
- [`docs/SIH_IMPLEMENTATION_STATUS.md`](docs/SIH_IMPLEMENTATION_STATUS.md) — Overall Implementation Status
