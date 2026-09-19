# ConfigSentinel — Adaptive Semantic Learning Architecture

## Overview

ConfigSentinel incorporates an adaptive semantic learning mechanism designed to continuously discover unknown configuration directives, propose typed security semantic categories using LLMs, enforce mandatory human approval, and persist approved mappings for zero-latency, offline cross-audit reuse.

---

## 1. Controlled Semantic Taxonomy

Free-text category names are prohibited. All proposed and persisted semantic mappings must belong to the controlled `SemanticCategory` enum (21 categories):

- `SSH_SECURITY`
- `TELNET_SECURITY`
- `AAA_AUTHENTICATION`
- `PASSWORD_SECURITY`
- `SESSION_TIMEOUT`
- `LOGGING`
- `NTP_TIME_SYNC`
- `SNMP_SECURITY`
- `HTTP_MANAGEMENT`
- `SERVICE_HARDENING`
- `ACCESS_CONTROL`
- `CRYPTOGRAPHY`
- `BANNER_SECURITY`
- `DNS_SECURITY`
- `NETWORK_MANAGEMENT`
- `AUTHORIZATION`
- `AUDIT_LOGGING`
- `REMOTE_ACCESS`
- `MANAGEMENT_PLANE_SECURITY`
- `OTHER`
- `UNRESOLVED`

---

## 2. Adaptive Learning Workflow

```text
Unknown Configuration Directive
              ↓
Search Persisted Approved Mappings (Vendor-Aware)
    ├── MATCH FOUND: Reuse Approved Semantic Mapping (No LLM Call)
    └── NO MATCH: Redact Secrets & Sanitize Prompt
              ↓
         Groq LLM Proposal
              ↓
         Confidence Score (HIGH / MEDIUM / LOW)
              ↓
         Status: PENDING
              ↓
      Operator Human Review
    ├── APPROVED → Persisted for Future Audit Reuse
    └── REJECTED → Preserved as Rejected, Never Reused
```

---

## 3. Persistent Semantic Reuse & Analytics

Approved mappings are stored in `mappings.db` with versioning, vendor isolation, and usage tracking (`usage_count`, `last_used_at`).

### API Endpoints:
- `GET /api/v1/mappings/stats` — Metrics on unknown patterns, pending, approved, rejected count, approval rate, and total reuses.
- `GET /api/v1/mappings/usage` — Usage statistics per approved semantic mapping.
