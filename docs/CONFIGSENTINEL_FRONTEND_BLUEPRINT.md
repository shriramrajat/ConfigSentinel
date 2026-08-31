# ConfigSentinel — Frontend UI/UX Blueprint

> **Version:** 1.0 | **Backend:** 0.1.0 | **Date:** 2026-08-31

---

## 1. Repository Understanding

### 1.1 What ConfigSentinel Does

ConfigSentinel is a **deterministic** network configuration security and compliance auditing engine. An operator pastes or uploads raw configuration text from a Cisco IOS/IOS-XE or Juniper JunOS device. The backend detects the vendor automatically, parses the configuration, evaluates all compliance controls, and returns a structured compliance report with evidence and remediation guidance. Every decision is reproducible — there is no AI, no probabilistic scoring.

### 1.2 Supported Vendors

| Vendor | Detection | Controls Evaluated |
|---|---|---|
| Cisco IOS / IOS-XE | Heuristic detection | SSH-001, TLN-001, EXEC-001, PWD-001, AAA-001 |
| Juniper JunOS | Heuristic detection | SSH-001, TLN-001, EXEC-001, PWD-001, AAA-001 |
| Unknown / Other | Heuristic fails | All controls -> `not_applicable` |

### 1.3 Active Compliance Controls (5 Total)

| Control ID | Name | Severity | Framework Refs |
|---|---|---|---|
| `SSH-001` | SSH Protocol Version Must Be 2 | `high` | CIS-IOS-L2-1.1.1, NIST-AC-17(2), ISO27001-A.9.4.2 |
| `TLN-001` | Telnet Must Be Disabled | `critical` | CIS-IOS-L2-1.3.1, NIST-AC-17(2), ISO27001-A.9.4.2 |
| `EXEC-001` | VTY Idle Session Timeout Must Be Configured | `high` | CIS-IOS-L2-2.1.1, NIST-AC-17(2) |
| `PWD-001` | Privileged Password Hashing | `high` | CIS-IOS-L2-2.1.1, CIS-JUNOS-L2-2.1.1 |
| `AAA-001` | Remote AAA Authentication Must Be Primary | `high` | (see docs/aaa-001-design.md) |

### 1.4 Status Values (Exhaustive)

| Value | Meaning | UI Treatment |
|---|---|---|
| `pass` | Control satisfied | Green |
| `fail` | Control violated | Red |
| `not_applicable` | Control not relevant to this vendor | Grey / neutral |
| `needs_review` | Ambiguous — human inspection required | Amber |

### 1.5 Severity Values (Exhaustive)

| Value | Current Use |
|---|---|
| `critical` | TLN-001 only |
| `high` | SSH-001, EXEC-001, PWD-001, AAA-001 |
| `medium` | No current controls — reserved |
| `low` | No current controls — reserved |
| `info` | Engine error fallback only |

---

## 2. API Capabilities — Verified Against Source

### POST /api/v1/audit Request

```
{ config_text: string, source_name?: string }
```

### POST /api/v1/audit Response

```
AuditResponse {
  summary {
    vendor               "cisco" | "juniper" | "unknown"
    hostname             string | null
    source_name          string | null
    total_controls       number  (always 5 with current registry)
    pass_count           number
    fail_count           number
    needs_review_count   number
    not_applicable_count number
    severity_distribution  { critical?: n, high?: n, medium?: n, low?: n, info?: n }
  }
  results[] {
    control_id           string   e.g. "SSH-001"
    control_name         string
    description          string
    severity             "critical"|"high"|"medium"|"low"|"info"
    status               "pass"|"fail"|"not_applicable"|"needs_review"
    vendor               string
    hostname             string | null
    evidence[] {
      control_id         string
      section_name       string | null
      raw_lines          string[]   TEXT SNIPPETS — NOT line numbers
      observed           string | null
      expected           string | null
      note               string
    }
    remediations[] {
      vendor             string  "cisco"|"juniper"|"any"
      guidance           string
      config_hint        string | null   ADVISORY ONLY
    }
    framework_refs       string[]
  }
}
```

### What Does NOT Exist in the API

- No security score or compliance percentage
- No historical scan records or audit IDs
- No authentication tokens or user accounts
- No device inventory or device management
- No saved/persistent reports
- No real-time progress events
- No AI summaries
- No exact line numbers (raw_lines = text snippets only)

---

## 3. Frontend Tech Stack — Existing Foundation (Do Not Rebuild)

| Layer | Technology | Status |
|---|---|---|
| Framework | React 19 + Vite 8 | Installed |
| Language | TypeScript 6 (strict) | Configured — 0 errors |
| Routing | React Router v7 | Wired |
| Server state | TanStack React Query v5 | Wired |
| Styling | Tailwind CSS v4 | Configured |
| Linting | oxlint | Configured |

### Foundation Files (Touch Only if Extending)

```
frontend/src/
  api/client.ts            ApiError class, apiFetch()
  api/configsentinel.ts    healthCheck(), getVersion(), auditConfig()
  types/api.ts             All TypeScript types — exact mirror of backend schemas
  hooks/useAudit.ts        useMutation for POST /api/v1/audit
  hooks/useVersion.ts      useQuery for GET /version
  lib/queryClient.ts       QueryClient configuration
  layouts/RootLayout.tsx   Shell (to be updated with real header/footer)
  routes/index.tsx         / -> Home
  pages/Home.tsx           Placeholder — to be replaced
  main.tsx                 Providers: BrowserRouter + QueryClientProvider
  App.tsx                  AppRoutes renderer
  index.css                Tailwind import + box-sizing reset
```

---

## 4. UX Goals

1. **Information before decoration.** Compliance findings are serious operational data. The UI must communicate data precisely.
2. **Operator-grade clarity.** Every finding must answer: what failed, why, which config lines caused it, how to fix it.
3. **Honest empty states.** `not_applicable` is neutral — not a pass, not a failure.
4. **Single workflow.** Submit config -> audit -> review results -> drill into findings.
5. **Zero data fabrication.** No invented counts, scores, or line numbers.

---

## 5. Design System

### 5.1 Typography

Add to `index.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
```

| Element | Font | Weight | Size |
|---|---|---|---|
| Product name | Inter | 700 | 1.5rem |
| Section headings | Inter | 600 | 1.125rem |
| Body / labels | Inter | 400 | 0.875rem |
| Code / config blocks | JetBrains Mono | 400 | 0.8125rem |
| Control IDs | JetBrains Mono | 500 | 0.8125rem |

### 5.2 Colour Palette (CSS Custom Properties)

Dark mode only. Add to `:root` in `index.css`:

```css
:root {
  --cs-bg-base:       #0a0d12;   /* page background */
  --cs-bg-surface:    #111520;   /* cards, panels */
  --cs-bg-elevated:   #1a1f2e;   /* code blocks, inputs */
  --cs-bg-subtle:     #1e2435;   /* hover states */

  --cs-border:        #252b3b;
  --cs-border-strong: #2e3650;

  --cs-text-primary:   #e2e8f0;
  --cs-text-secondary: #94a3b8;
  --cs-text-muted:     #475569;

  --cs-accent:       #3b7cf8;
  --cs-accent-hover: #2563eb;

  --cs-pass:      #22c55e;  --cs-pass-bg:   #052e16;
  --cs-fail:      #ef4444;  --cs-fail-bg:   #2d0707;
  --cs-review:    #f59e0b;  --cs-review-bg: #2d1c02;
  --cs-na:        #475569;  --cs-na-bg:     #111827;

  --cs-sev-critical: #f43f5e;
  --cs-sev-high:     #f97316;
  --cs-sev-medium:   #eab308;
  --cs-sev-low:      #22c55e;
  --cs-sev-info:     #64748b;
}
```

### 5.3 Status Badge Spec

| Status | Background | Text | Label |
|---|---|---|---|
| `pass` | `--cs-pass-bg` | `--cs-pass` | PASS |
| `fail` | `--cs-fail-bg` | `--cs-fail` | FAIL |
| `needs_review` | `--cs-review-bg` | `--cs-review` | REVIEW |
| `not_applicable` | `--cs-na-bg` | `--cs-na` | N/A |

### 5.4 Severity Indicator Spec

Small coloured dot + uppercase label. Severity is a **control property**, not a finding property.

```
 CRITICAL   (--cs-sev-critical)
 HIGH       (--cs-sev-high)
 MEDIUM     (--cs-sev-medium)
 LOW        (--cs-sev-low)
 INFO       (--cs-sev-info)
```

### 5.5 Component Tokens

| Component | Background | Border | Radius |
|---|---|---|---|
| Card | `--cs-bg-surface` | `--cs-border` | 0.5rem |
| Code block | `--cs-bg-elevated` | none | 0.375rem |
| Input / Textarea | `--cs-bg-elevated` | `--cs-border` | 0.375rem |
| Primary button | `--cs-accent` | none | 0.375rem |
| Ghost button | transparent | `--cs-border` | 0.375rem |

### 5.6 Motion

Minimal and purposeful:
- Status badge: `transition: background-color 150ms ease`
- Accordion expand: `transition: opacity 150ms ease`
- Loading skeleton: CSS pulse animation only
- No decorative animations

---

## 6. Route Map

```
/     Audit page — config input + results (single route)
```

No other routes. The backend has no persistence, no audit IDs, no authentication.

Routes that must NOT be implemented:
- `/results/:id` — backend has no persistence
- `/login` — no authentication
- `/dashboard` — no historical data
- `/history` — no audit history

---

## 7. Page Responsibilities

### pages/Home.tsx (replace placeholder)

Responsibilities:
1. Render `AuditForm`
2. Drive `useAudit()` mutation on submit
3. Show loading state while audit is in-flight
4. Show error state with backend message on failure
5. Show empty state before first audit
6. Show `AuditResults` when data is available
7. Provide "Run New Audit" reset

Does NOT:
- Contain any compliance logic
- Calculate derived metrics from pass/fail counts
- Store results anywhere beyond React Query mutation state

---

## 8. Component Hierarchy

```
App
+-- BrowserRouter
    +-- QueryClientProvider
        +-- AppRoutes
            +-- RootLayout                  [layouts/RootLayout.tsx]   MODIFY
                +-- AppHeader               [layouts/AppHeader.tsx]    NEW
                |   +-- BackendStatus       (uses useVersion)
                +-- Outlet
                |   +-- Home               [pages/Home.tsx]            REPLACE
                |       +-- AuditForm      [components/AuditForm.tsx]  NEW
                |       +-- AuditResults   [components/AuditResults.tsx] NEW
                |           +-- DeviceInfo       [components/DeviceInfo.tsx]
                |           +-- ResultsSummary   [components/ResultsSummary.tsx]
                |           +-- ResultsTable     [components/ResultsTable.tsx]
                |               +-- FindingDetail [components/FindingDetail.tsx]
                |                   +-- EvidenceBlock
                |                   +-- RemediationBlock
                +-- AppFooter              [layouts/AppFooter.tsx]     NEW
```

### Component Boundaries

| Component | Props In | Renders | Must NOT Do |
|---|---|---|---|
| `AuditForm` | `onSubmit`, `isPending` | Textarea, source name, submit button | API calls |
| `AuditResults` | `AuditResponse` | Full result panel | Compliance logic |
| `ResultsSummary` | `AuditSummary` | Four count cards | Derive scores |
| `DeviceInfo` | `AuditSummary` | Vendor, hostname, source | Interpret vendor |
| `ResultsTable` | `ComplianceResult[]` | Accordion rows | Recalculate status |
| `FindingDetail` | `ComplianceResult` | Evidence + remediation | Auto-apply config_hint |
| `EvidenceBlock` | `Evidence[]` | Config snippets, observed, note | Add line numbers |
| `RemediationBlock` | `Remediation[]` | Guidance + advisory code | Apply or modify |

---

## 9. Audit Workflow — UI States

### Empty State (before first audit)

- AuditForm visible with placeholder text
- Submit disabled until textarea has content
- Instructional text: "Paste a Cisco IOS or Juniper JunOS configuration to begin."

### Loading State (isPending === true)

- Textarea + submit button disabled
- Five skeleton rows pulsing below form
- Label: "Auditing configuration..."

### Error State (isError === true)

- Form re-enabled
- Error panel shows `error.message` (safe from ApiError)
- Differentiate by `error.code`:
  - `INVALID_INPUT` -> "Configuration text is empty or unusable. Please re-enter."
  - `INTERNAL_ERROR` -> "Backend error. Please try again."
  - Other -> show `error.message` as-is

### Success State (isSuccess === true)

- AuditForm stays visible (collapsed or scrolled above)
- DeviceInfo row: vendor, hostname, source_name
- ResultsSummary: 4 count cards
- ResultsTable: 5 accordion rows (one per control)
- "Run New Audit" button -> calls `useAudit().reset()`

### Unknown Vendor State (data.summary.vendor === "unknown")

- Warning banner above results table:
  "Vendor not recognised — all controls returned Not Applicable. ConfigSentinel supports Cisco IOS/IOS-XE and Juniper JunOS only."
- Results table still shown (all N/A rows)

---

## 10. Configuration Input

### Input Methods

1. **Textarea (primary):** Monospace font, min 8 rows, resizable vertically.
2. **File upload (Phase 3):** Drag-and-drop or click. Reads as UTF-8 text, populates textarea. Filename becomes `source_name`.

No vendor dropdown — backend auto-detects.

### Source Name Field

- Optional text input
- Placeholder: "e.g. router-01.conf or device name"
- Maps to `source_name` in request
- Shown in DeviceInfo panel after audit

### Client-Side Validation (Only)

| Condition | Message |
|---|---|
| `config_text.trim() === ""` | "Configuration text is required." |
| `config_text.trim().length < 10` | "Configuration text is too short." |

All substantive validation is backend responsibility.

---

## 11. Evidence Presentation Rules

```
evidence.section_name   "Section: <name>" or "Global" when null
evidence.raw_lines[]    Code block labelled "Configuration snippet"
                        If empty array -> show "Directive not found in configuration"
                        NEVER label as "Line N"
evidence.observed       "Found: <value>" or "Found: not present" if null
evidence.expected       "Required: <value>"
evidence.note           Always shown as plain text
```

Absence evidence (raw_lines is empty array, observed is null):
- Do NOT render an empty code block
- Show: "Directive not found in configuration"

---

## 12. Remediation Presentation Rules

```
remediation.vendor       Badge: "Cisco" | "Juniper" | "All vendors"
remediation.guidance     Paragraph text
remediation.config_hint  Code block with mandatory banner:
                         "Advisory only - do not apply without review"
                         If config_hint is null -> no code block rendered
```

`remediations` is empty for `pass` results — do not render the remediation section.

---

## 13. AppHeader

```
[shield] ConfigSentinel                  v0.1.0  [green dot] Connected
```

- Product name with inline SVG shield icon (left)
- Version from `useVersion()` (right)
- Backend status: loading -> pulsing grey dot | success -> green dot | error -> red dot + "Backend unavailable"
- No navigation links (single-page app)

---

## 14. ResultsSummary Cards

Four cards in a row (4x1 desktop, 2x2 mobile):

| Card | Source Field | Colour |
|---|---|---|
| Pass | `summary.pass_count` | Green |
| Fail | `summary.fail_count` | Red |
| Needs Review | `summary.needs_review_count` | Amber |
| Not Applicable | `summary.not_applicable_count` | Grey |

No percentages. No scores. Raw counts only.

`severity_distribution` may be shown as secondary text ("4 high, 1 critical") — informational only.

---

## 15. ResultsTable Layout

Accordion-style. Each row = one ComplianceResult.

```
Control ID | Control Name                  | Severity | Status
---------- | ----------------------------- | -------- | ------
SSH-001    | SSH Protocol Version           |  HIGH   | [PASS]
TLN-001    | Telnet Must Be Disabled        |  CRIT   | [FAIL]  v  <- expanded
           |-- Evidence ──────────────────────────────────────────
           |   Section: global
           |   [Configuration snippet]
           |   transport input telnet
           |   [/snippet]
           |   Found: telnet  |  Required: ssh or none
           |   Note: Telnet is permitted on VTY 0 4.
           |
           |-- Remediation (Cisco) ─────────────────────────────
           |   Configure all VTY lines to accept SSH only.
           |   [! Advisory only - do not apply without review]
           |   line vty 0 4
           |    transport input ssh
EXEC-001   | VTY Idle Session Timeout       |  HIGH   | [FAIL]
PWD-001    | Privileged Password Hashing    |  HIGH   | [REVIEW]
AAA-001    | Remote AAA Authentication      |  HIGH   | [PASS]
```

Default sort: API evaluation order (authoritative). Do not reorder.

Optional filter bar (Phase 3, client-only):
```
[ All ] [ Fail ] [ Needs Review ] [ Pass ] [ N/A ]
```

---

## 16. Framework References Display

Display as read-only badges inside expanded FindingDetail:
```
[CIS-IOS-L2-1.3.1]  [NIST-AC-17(2)]  [ISO27001-A.9.4.2]
```

Informational labels only. No URLs (backend provides none).

---

## 17. Responsive Strategy

| Breakpoint | Layout |
|---|---|
| < 640px | Single column. Summary 2x2. Table: card-per-control stacked. |
| 640px-1024px | Single column. Full table. Summary 4x1. |
| > 1024px | Max-width 1024px centred. Full table layout. |

No horizontal scrolling on any breakpoint.

---

## 18. Data Flow

```
User submits config text
  -> AuditForm.onSubmit(config_text, source_name)
    -> useAudit().mutate({ config_text, source_name })
      -> auditConfig() -> POST /api/v1/audit
        -> Backend: detect_vendor -> parse -> audit engine -> results
        -> AuditResponse returned
          -> useAudit().data populated
            -> Home renders AuditResults(data)
              -> DeviceInfo(data.summary)
              -> ResultsSummary(data.summary)
              -> ResultsTable(data.results)
                -> FindingDetail(result) -- expanded on click
                  -> EvidenceBlock(result.evidence)
                  -> RemediationBlock(result.remediations)
```

All values rendered directly from API fields. No derived metrics. No invented fields.

---

## 19. Backend Dependencies (Features Blocked on Backend Work)

| Feature | Status | Required Backend Work |
|---|---|---|
| Audit history | [BACKEND DEPENDENCY] | Persistence layer + audit IDs |
| Multi-device batch | [BACKEND DEPENDENCY] | Batch endpoint |
| Exact line numbers in evidence | [BACKEND DEPENDENCY] | Parser line tracking |
| User authentication | [BACKEND DEPENDENCY] | Auth system |
| Streaming progress | [BACKEND DEPENDENCY] | SSE or WebSocket endpoint |
| Additional controls | [BACKEND DEPENDENCY] | New rule implementations |
| Export to PDF/JSON | [BACKEND DEPENDENCY] | Export endpoint (or frontend JSON serialisation of response) |

---

## 20. Implementation Order

### Phase 1 — Core Audit Workflow

1. `index.css` — Add Google Fonts import + CSS custom properties (design tokens)
2. `layouts/AppHeader.tsx` — Product name + BackendStatus using `useVersion()`
3. `layouts/AppFooter.tsx` — Minimal footer text
4. `layouts/RootLayout.tsx` — Compose AppHeader + Outlet + AppFooter
5. `components/AuditForm.tsx` — Controlled textarea + source name + submit. Callback-based.
6. `pages/Home.tsx` — Wire `useAudit()`. Render form + four UI states.

### Phase 2 — Results Display

7. `components/StatusBadge.tsx` — Four status variants
8. `components/SeverityIndicator.tsx` — Dot + label
9. `components/DeviceInfo.tsx` — Vendor, hostname, source_name
10. `components/ResultsSummary.tsx` — Four count cards
11. `components/EvidenceBlock.tsx` — Evidence with conditional code block
12. `components/RemediationBlock.tsx` — Guidance + advisory code hint
13. `components/FindingDetail.tsx` — Accordion: EvidenceBlock + RemediationBlock
14. `components/ResultsTable.tsx` — Accordion table of all 5 controls
15. `components/AuditResults.tsx` — Composes all result components. Unknown-vendor banner.

### Phase 3 — Polish

16. Loading skeleton (5 animated rows while isPending)
17. Error state with per-error-code messaging (`INVALID_INPUT` vs `INTERNAL_ERROR`)
18. Filter bar above results table (client-only)
19. File upload / drag-and-drop (reads as text, populates textarea)
20. Copy-to-clipboard for config_hint code blocks
21. Unknown-vendor state with clear explanation
22. All-pass success confirmation banner

---

## 21. Validation Gates

After each phase:

```bash
npx tsc --noEmit   # 0 errors required
npm run build      # must succeed
npm run lint       # must pass
```

Manual verification checklist:
- Empty submission -> client validation fires, no API call
- Valid Cisco config -> correct results rendered
- Valid Juniper config -> correct results rendered
- Unknown vendor config -> unknown-vendor banner shown, not an error
- Backend offline -> error state with clear message
- `not_applicable` results -> grey/neutral, NOT red
- `needs_review` results -> amber, NOT red
- `config_hint` -> advisory banner always visible
- `raw_lines` empty -> "Directive not found" shown, no empty code block
- No percentage, score, or fabricated metric anywhere in UI

---

## 22. Explicit Exclusions

Must not appear in any form:

- Security scores or compliance percentages
- Security posture gauges or dials
- AI-generated summaries or suggestions
- Historical trend charts
- User login or authentication UI
- Device inventory screens
- Auto-remediation or config deployment controls
- Real-time scanning progress indicators
- Fabricated line numbers in evidence display
