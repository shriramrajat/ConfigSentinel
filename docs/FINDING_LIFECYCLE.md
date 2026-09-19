# ConfigSentinel — Security Finding Lifecycle Management

## Overview

ConfigSentinel provides end-to-end persistent tracking of security findings across device audit histories.

---

## 1. Finding Lifecycle State Machine

```text
       ┌───────────┐
       │   OPEN    │ ◄────────────────────────┐
       └─────┬─────┘                          │
             │                                │
      Operator Acknowledge            Control Fails Again
             │                                │
             ▼                                │
      ┌──────────────┐                        │
      │ ACKNOWLEDGED │                        │
      └──────┬───────┘                        │
             │                                │
   Control Passes in Audit / Manual Resolve   │
             │                                │
             ▼                                │
       ┌───────────┐                          │
       │ RESOLVED  ├──────────────────────────┘
       └───────────┘
```

---

## 2. Stable Finding Correlation

Findings are correlated across audits using a stable fingerprint:
`SHA-256(device_id + "::" + control_id)`

When the same control fails in subsequent audits:
- The existing finding is updated rather than creating a duplicate.
- `occurrence_count` is incremented.
- `last_seen` and `last_seen_audit_id` are updated.

If a control passes, the finding transitions to `RESOLVED` automatically. If it fails again later, it transitions back to `OPEN` (`reopened`).

---

## 3. API Endpoints

- `GET /api/v1/findings` — Query findings with device, status, and severity filters.
- `GET /api/v1/findings/{finding_id}` — Get detailed finding record.
- `POST /api/v1/findings/{finding_id}/acknowledge` — Transition finding to `ACKNOWLEDGED`.
- `POST /api/v1/findings/{finding_id}/resolve` — Transition finding to `RESOLVED`.
- `POST /api/v1/findings/{finding_id}/reopen` — Transition finding to `OPEN`.
