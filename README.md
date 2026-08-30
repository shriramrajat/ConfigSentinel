# ConfigSentinel — Network Configuration Security and Compliance Auditor

## Problem Statement

| Field | Value |
|---|---|
| **PS ID** | SIH 26155 |
| **Org** | National Technical Research Organisation (NTRO) |
| **Category** | Software |
| **Theme** | Blockchain & Cybersecurity |

---

## Current Architecture

```
Raw configuration
       ↓
Vendor detection
       ↓
Vendor parser (Cisco or Juniper)
       ↓
NormalizedConfig
       ↓
Compliance Engine
       ↓
Compliance Rules
       ↓
Evidence + Remediation
```

### Important Architectural Principle

Compliance rules consume `NormalizedConfig`. They must not parse raw configuration directly. AI/LLM is **not** currently part of deterministic compliance evaluation.

---

## Supported Vendors

| Vendor | Parser | Controls evaluated |
|---|---|---|
| Cisco IOS / IOS-XE | `src/parsers/cisco.py` | SSH-001, TLN-001, EXEC-001, PWD-001, AAA-001 |
| Juniper JunOS | `src/parsers/juniper.py` | SSH-001, TLN-001, EXEC-001, PWD-001, AAA-001 |
| Others | — | Returns `NOT_APPLICABLE` for all controls |

---

## Current Implementation

| Component | Status |
|---|---|
| Ingestion (`loader.py`, `detector.py`) | ✅ Implemented |
| Cisco IOS / IOS-XE parser | ✅ Implemented |
| Juniper JunOS parser | ✅ Implemented |
| Vendor-neutral normalization model | ✅ Implemented |
| Compliance engine (`audit()`) | ✅ Implemented |
| `ComplianceResult` / `Evidence` / `Remediation` model | ✅ Implemented |
| SSH-001 — SSH Protocol Version | ✅ Implemented |
| TLN-001 — Telnet Must Be Disabled | ✅ Implemented |
| EXEC-001 — VTY Idle Session Timeout | ✅ Implemented |
| PWD-001 — Privileged Password Hashing | ✅ Implemented |
| AAA-001 — Remote AAA Authentication Must Be Primary | ✅ Implemented |
| HTTP API (`src/api/`) | ✅ Implemented (FastAPI) |
| Reporting / output layer | ❌ Not implemented |
| Web interface (frontend) | ❌ Not implemented — see `docs/FRONTEND.md` |
| AI-assisted normalization | ❌ Not in scope for deterministic engine |

---

## Current Controls

| Control | Name | Severity | Vendors |
|---|---|---|---|
| **SSH-001** | SSH Protocol Version Must Be 2 | HIGH | Cisco, Juniper |
| **TLN-001** | Telnet Must Be Disabled | CRITICAL | Cisco, Juniper |
| **EXEC-001** | VTY Idle Session Timeout Must Be Configured | HIGH | Cisco, Juniper |
| **PWD-001** | Privileged Exec / Root Password Must Use Strong Hashing | HIGH | Cisco, Juniper |
| **AAA-001** | Remote AAA Authentication Must Be Primary | HIGH | Cisco, Juniper |

---

## API

The FastAPI HTTP API is in `src/api/`. It exposes the existing pipeline over HTTP without modifying any compliance logic.

```bash
uvicorn src.api.main:app --reload
```

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness probe |
| `GET /version` | Product version |
| `POST /api/v1/audit` | Submit configuration text for compliance audit |

OpenAPI schema: `http://localhost:8000/openapi.json`
Frontend integration contract: [`docs/FRONTEND.md`](docs/FRONTEND.md)

---

## Testing

**Current full suite: 454 tests passing** (381 pre-existing + 73 new API tests).

To run tests from the repository root:

```bash
python -m pytest tests/ -q
```

Expected output:

```
454 passed in ~3s
```

---

## Current Limitations

- **No exact line numbers:** The backend does not track line positions. `evidence.raw_lines` contains text snippets, not line numbers.
- **Heuristic detection:** Vendor detection is heuristic. Unusual or heavily stripped configs may yield `"unknown"`.
- **Parsing scope:** Parsers extract hostname, top-level directives, and block sections relevant for compliance. They do not implement full vendor CLI grammars.
- **Juniper parser flattening:** Items nested more than one level deep inside JunOS blocks are captured under the enclosing top-level section. See `docs/FRONTEND.md` §12.
- **Unsupported vendors:** Any vendor other than Cisco and Juniper returns `not_applicable` for all controls.
- **No frontend yet:** The web interface is not implemented. See `docs/FRONTEND.md` for the integration contract.

---

## Detailed Documentation

| Document | Contents |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full pipeline, normalization model, parser behaviour, engine contract, design decisions |
| [`docs/CONTROLS.md`](docs/CONTROLS.md) | SSH-001, TLN-001, EXEC-001, PWD-001, AAA-001 — per-vendor behaviour, status tables, evidence |
| [`docs/FRONTEND.md`](docs/FRONTEND.md) | **Frontend integration contract** — API endpoints, TypeScript types, limitations, integration rules |
| [`docs/TESTING.md`](docs/TESTING.md) | Testing strategy, test breakdown, edge cases, coverage gaps |
| [`docs/CONTROL_ROADMAP.md`](docs/CONTROL_ROADMAP.md) | Future control candidates |
| [`docs/aaa-001-design.md`](docs/aaa-001-design.md) | AAA-001 design notes |
