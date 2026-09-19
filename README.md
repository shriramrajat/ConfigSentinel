# ConfigSentinel

AI-Assisted Vendor-Agnostic Network Configuration Security & Compliance Auditor

Problem Statement: **SIH 26155** (National Technical Research Organisation - NTRO)

---

## Architecture Overview

```
Raw Configuration Text
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
Cross-Vendor Semantic Intelligence Layer
        ↓
Deterministic Analysis & What-If Simulation
        ↓
Bounded AI Explanation & Recommendation (Advisory Only)
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

### 5. Platform & Reporting
- **Bulk Ingestion:** Audits multi-device configuration archives simultaneously.
- **PDF Report Generation:** Executable ReportLab PDF generator rendering executive audit summaries, compliance breakdown tables, and remediations.
- **SaaS Frontend Interface:** React + Vite + TypeScript dark-theme security dashboard featuring single-file audit scanning, audit history, device dashboard, finding lifecycle, discovery queue, and cross-vendor intelligence tabs.

---

## AI Governance & Boundaries

> [!IMPORTANT]
> **AI IS NOT THE COMPLIANCE AUTHORITY.**
> AI does NOT determine PASS/FAIL status.
> AI does NOT assign or modify severity tiers.
> AI does NOT calculate risk scores.
> AI serves strictly as an advisory assistant for unknown pattern normalization mapping proposals and plain-English finding explanations.

---

## Technology Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy / SQLite, ReportLab
- **Frontend:** React 18, TypeScript, Vite, React Router, Vanilla CSS design system
- **Testing:** Pytest (552 passing tests)

---

## Quick Start & Verification

### Running Backend Tests
```bash
python -m pytest tests/ --tb=short -q
```
*Expected: 552 passed*

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

- [`docs/PHASE2_IMPLEMENTATION_PLAN.md`](docs/PHASE2_IMPLEMENTATION_PLAN.md) — Phase 2 Architecture & Objectives
- [`docs/PHASE2_IMPLEMENTATION_STATUS.md`](docs/PHASE2_IMPLEMENTATION_STATUS.md) — Phase 2 Sub-Phase Status
- [`docs/CROSS_VENDOR_INTELLIGENCE.md`](docs/CROSS_VENDOR_INTELLIGENCE.md) — Cross-Vendor Semantic Architecture
- [`docs/AI_GOVERNANCE.md`](docs/AI_GOVERNANCE.md) — Strict AI Security Boundaries
- [`docs/SIH_IMPLEMENTATION_STATUS.md`](docs/SIH_IMPLEMENTATION_STATUS.md) — Implementation Progress Overview
- [`docs/FINDING_LIFECYCLE.md`](docs/FINDING_LIFECYCLE.md) — SQLite Finding Lifecycle & Drift

---

## Limitations

- **Parser Scope:** Vendor parsers extract sections and directives relevant to compliance; full vendor CLI compiler grammars are not implemented.
- **Vendor Capability Coverage:** Certain legacy features or vendor-specific capabilities marked `UNSUPPORTED` or `UNKNOWN` require explicit syntax parser definitions.
