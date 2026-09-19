# ConfigSentinel Phase 3 — Production Security Operations Plan

## Objective
Transform ConfigSentinel into a Security Operations Platform for continuous network configuration security management.

## Core Capabilities
- **3.1 Device Inventory:** First-class device registry with SQLite persistence.
- **3.2 Risk Queue & Prioritization:** Operator queue ranked deterministically by risk score, finding age, recurrence, and attack chain dependencies.
- **3.3 Remediation Intelligence:** Multi-vendor remediation guidance across Cisco, Juniper, Arista, FortiOS, and PAN-OS.
- **3.4 Remediation Verification:** Post-remediation audit comparator producing `FIX VERIFIED` or `FIX NOT VERIFIED`.
- **3.5 Configuration Baselines:** Immutable approved baselines with versioning (v1, v2) and baseline drift comparison.
- **3.6 Audit Scheduling Model:** Domain model and job state tracker for recurring audits.
- **3.7 Fleet-Wide Security Posture:** Aggregated metrics (Healthy, Needs Attention, Critical, open findings).
- **3.8 Bounded Natural-Language Query Layer:** Bounded NL query translation to `StructuredQuerySchema` with parameterized query execution; blocks arbitrary SQL injection.
- **3.9 Security Operations Dashboard:** React UI dashboard (`frontend/src/pages/Operations.tsx`).
- **3.10 Exporters & Webhooks:** JSON/CSV exporters + SIEM webhook notifier with secret redaction.
- **3.11 Production Hardening:** Audit trail logger, zip slip extraction protection, upload size bounds.
