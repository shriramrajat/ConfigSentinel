# ConfigSentinel â€” Frontend Integration Contract

> **Status:** Authoritative API contract for frontend developers.
> **Backend version:** 0.1.0
> **Audience:** Rohan, Matin, and any frontend developer consuming this API.

---

## 1. Overview

ConfigSentinel is a **deterministic** network configuration security and compliance auditing engine.
It accepts raw configuration text from a Cisco IOS/IOS-XE or Juniper JunOS device and returns a structured compliance report.

The backend is **not AI-assisted**. Every compliance decision is deterministic and reproducible.

---

## 2. Backend Base URL

| Environment | Base URL |
|---|---|
| Local development | `http://localhost:8000` |
| Production | **Must be supplied via frontend environment configuration.** |

> [!IMPORTANT]
> The production URL must never be hardcoded in the frontend codebase.
> Use an environment variable such as `VITE_API_BASE_URL` or `NEXT_PUBLIC_API_URL`.

---

## 3. Endpoints

### 3.1 `GET /health`

**Purpose:** Liveness check. Use to verify the backend is reachable before any user action.

**Request:** None.

**Response `200 OK`:**
```json
{ "status": "ok" }
```

**Errors:** None under normal conditions.

---

### 3.2 `GET /version`

**Purpose:** Retrieve product and API version for display or compatibility checks.

**Request:** None.

**Response `200 OK`:**
```json
{
  "product": "ConfigSentinel",
  "version": "0.1.0",
  "description": "Deterministic network configuration security and compliance auditing. Supports Cisco IOS/IOS-XE and Juniper JunOS."
}
```

---

### 3.3 `POST /api/v1/audit`

**Purpose:** Submit raw configuration text for compliance auditing. Returns a full compliance report.

**Content-Type:** `application/json`

**Request body:**
```json
{
  "config_text": "<raw configuration text string>",
  "source_name": "<optional label for traceability>"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `config_text` | `string` | âœ… | Raw device configuration text. Must be non-empty. |
| `source_name` | `string \| null` | âŒ | Optional label (filename, device name, "paste"). Used in response for traceability. Not used for parsing. |

**Response `200 OK`:** See [Â§6 â€” Response Types](#6-response-types)

**Error responses:**

| Status | Code | When |
|---|---|---|
| `400` | `INVALID_INPUT` | `config_text` is empty or whitespace-only |
| `422` | `VALIDATION_ERROR` | Request body fails schema validation (missing `config_text`, wrong type) |
| `500` | `INTERNAL_ERROR` | Unexpected backend fault |

---

## 4. Request Types (TypeScript)

```typescript
interface AuditRequest {
  config_text: string;       // Required. Raw device configuration text.
  source_name?: string;      // Optional. Label for traceability.
}
```

---

## 5. Compliance Concepts

### 5.1 Compliance Status

Every control evaluation produces exactly one of these statuses:

| Status | Value | Meaning | Is a Failure? |
|---|---|---|---|
| Pass | `"pass"` | Configuration satisfies the control requirement. | No |
| Fail | `"fail"` | Configuration violates the control requirement. | **Yes** |
| Not Applicable | `"not_applicable"` | Control does not apply to this vendor. | **No** |
| Needs Review | `"needs_review"` | Value found but ambiguous; human review required. | Uncertain â€” flag for operator |

> [!IMPORTANT]
> `not_applicable` **must not be treated as a failure** in the UI.
> A Cisco-only control evaluated against a Juniper device returns `not_applicable` â€” this is expected and correct.

### 5.2 Severity

Severity communicates risk priority, independent of pass/fail status.

| Value | Meaning |
|---|---|
| `"critical"` | Immediate risk; highest priority remediation |
| `"high"` | Significant risk |
| `"medium"` | Moderate risk |
| `"low"` | Minor risk |
| `"info"` | Informational |

> [!NOTE]
> Severity is a static property of the **control**, not the finding.
> A PASS result still has a severity â€” it tells you how important that control is.

### 5.3 Active Controls

| Control ID | Name | Severity | Vendors |
|---|---|---|---|
| `SSH-001` | SSH Protocol Version | `high` | Cisco, Juniper |
| `TLN-001` | Telnet Must Be Disabled | `critical` | Cisco, Juniper |
| `EXEC-001` | VTY Idle Session Timeout | `high` | Cisco, Juniper |
| `PWD-001` | Privileged Password Hashing | `high` | Cisco, Juniper |
| `AAA-001` | Remote AAA Authentication Must Be Primary | `high` | Cisco, Juniper |

---

## 6. Response Types (TypeScript)

```typescript
// Full response from POST /api/v1/audit
interface AuditResponse {
  summary: AuditSummary;
  results: ComplianceResult[];
}

interface AuditSummary {
  vendor: string;                        // Detected vendor: "cisco" | "juniper" | "unknown"
  hostname: string | null;               // Device hostname from config, or null
  source_name: string | null;            // Echoes the request source_name, or null
  total_controls: number;                // Total number of controls evaluated
  pass_count: number;                    // Controls with status "pass"
  fail_count: number;                    // Controls with status "fail"
  needs_review_count: number;            // Controls with status "needs_review"
  not_applicable_count: number;          // Controls with status "not_applicable" â€” NOT a failure count
  severity_distribution: {              // Count of controls per severity tier (all statuses)
    [severity: string]: number;
  };
}

interface ComplianceResult {
  control_id: string;                    // e.g. "SSH-001"
  control_name: string;                  // e.g. "SSH Protocol Version"
  description: string;                   // Plain-English description of what the control checks
  severity: "critical" | "high" | "medium" | "low" | "info";
  status: "pass" | "fail" | "not_applicable" | "needs_review";
  vendor: string;                        // Vendor identifier from the configuration
  hostname: string | null;              // Device hostname, or null
  evidence: Evidence[];
  remediations: Remediation[];          // Empty when status === "pass"
  framework_refs: string[];             // e.g. ["CIS-IOS-L2-1.1.1", "NIST-AC-17(2)"]
}

interface Evidence {
  control_id: string;                   // Matches parent result's control_id
  section_name: string | null;          // Config section, or null for global items
  raw_lines: string[];                  // Verbatim config lines used by the rule (may be empty)
  observed: string | null;             // Value actually found. null when directive was absent.
  expected: string | null;             // Value the rule required. null when not applicable.
  note: string;                         // Human-readable explanation of the rule's conclusion
}

interface Remediation {
  vendor: string;                       // Target vendor, e.g. "cisco". "any" means all vendors.
  guidance: string;                     // Actionable plain-English instructions
  config_hint: string | null;          // Example config snippet. Advisory only â€” never auto-apply.
}

// Error response (all error status codes)
interface ErrorResponse {
  error: {
    code: string;    // Machine-readable: "INVALID_INPUT" | "VALIDATION_ERROR" | "INTERNAL_ERROR"
    message: string; // Human-readable. Safe to display in the UI.
  };
}
```

---

## 7. Evidence and Traceability

### What evidence provides

- `raw_lines`: The verbatim configuration line(s) that the rule used to make its decision. Use this to highlight the relevant config text in the UI.
- `observed`: The value found (e.g. `"v1"` for SSH version 1).
- `expected`: The value required (e.g. `"v2"`).
- `note`: A complete human-readable explanation of why the rule concluded what it did.

### What evidence does NOT provide

> [!WARNING]
> **The backend does not track exact line numbers.**
>
> `raw_lines` contains text snippets, not line positions.
> The frontend must NOT fabricate line numbers by scanning `raw_lines` against the original text.
>
> If the frontend needs to highlight lines in a config viewer, it must use string matching against the submitted `config_text`, acknowledging that line numbers are approximate.

### Absence evidence

When a required directive is **absent** from the configuration:
- `raw_lines` is an empty array `[]`.
- `observed` is `null`.
- `expected` describes what was required.
- `note` explains the absence.

This is intentional â€” absence of a required directive is still a compliance finding.

---

## 8. Remediation Guidance

Remediations are only present when `status === "fail"` or `status === "needs_review"`.

- `guidance`: Specific, actionable instructions for the operator.
- `config_hint`: An example configuration snippet showing the required change.

> [!CAUTION]
> `config_hint` is **advisory only**. It must never be applied automatically.
> Display it as a code snippet with a clear "example only" label.
> The operator must review and adapt it to their specific environment.

---

## 9. Empty States

| Scenario | Meaning |
|---|---|
| `fail_count === 0` | No compliance failures detected. All applicable controls passed. |
| `results` is empty | No rules evaluated (this should not normally occur). |
| `not_applicable_count === total_controls` | All controls returned `not_applicable` â€” the vendor was not recognised. No compliance verdict is possible. |
| `needs_review_count > 0` | Some findings require human inspection. Not automatic failures. |

> [!NOTE]
> When `vendor === "unknown"`, all controls will return `not_applicable`.
> The frontend should display a clear message explaining the vendor was not recognised,
> rather than showing a compliance report with all controls marked unknown.

---

## 10. Error Handling

All error responses share the same envelope:

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Configuration text is empty or contains only whitespace."
  }
}
```

| HTTP Status | Error Code | Typical Cause | Frontend action |
|---|---|---|---|
| `400` | `INVALID_INPUT` | Empty or whitespace-only `config_text` | Show validation message, prompt re-entry |
| `422` | `VALIDATION_ERROR` | Missing or wrong-type request field | Log and show generic input error |
| `500` | `INTERNAL_ERROR` | Unexpected backend fault | Show error toast; offer retry |

The `message` field is safe to display directly in the UI.

---

## 11. Vendor Detection

The backend detects vendor automatically from the configuration text. The frontend does not need to (and must not) perform vendor detection.

| Detected vendor | Meaning |
|---|---|
| `"cisco"` | Cisco IOS or IOS-XE â€” full parsing and compliance evaluation |
| `"juniper"` | Juniper JunOS â€” full parsing and compliance evaluation |
| `"unknown"` | No vendor markers recognised â€” all controls return `not_applicable` |

---

## 12. Known Backend Limitations

> [!NOTE]
> These limitations are documented here to prevent the frontend from making incorrect assumptions.
> Do not work around these limitations in the frontend â€” work with what the API actually provides.

### No exact line numbers
The backend parsers do not track byte offsets or line numbers.
`raw_lines` contains text snippets only. Exact line navigation is not available.

### Juniper path flattening
The Juniper parser flattens nested blocks (e.g. `system > services > ssh`) into the enclosing top-level section.
Evidence from Juniper configs shows `section_name: "system"` for directives that are deeply nested inside it.

### Cisco token splitting
The Cisco parser tokenises on the first whitespace. Multi-word directives like `ip ssh version 2` are stored as `key: "ip"`, `value: "ssh version 2"`. Rules compensate for this internally. The frontend should not interpret raw evidence keys.

### Unsupported vendors
Any vendor other than `"cisco"` and `"juniper"` returns `vendor: "unknown"` and all controls return `not_applicable`.

### Source file path not available
When configuration is submitted as text, there is no filesystem path. `source_name` is a user-supplied label for display purposes, not a path.

### Heuristic detection
Vendor detection is heuristic â€” unusual or heavily stripped configs may not be detected correctly. Stripped or truncated configs may yield `"unknown"`.

---

## 13. API Examples

### Example: Cisco audit request

```bash
curl -X POST http://localhost:8000/api/v1/audit \
  -H "Content-Type: application/json" \
  -d '{
    "config_text": "version 17.9\nhostname LAB-ROUTER\nip ssh version 2\nend",
    "source_name": "lab-router.conf"
  }'
```

### Example: Successful audit response (abbreviated)

```json
{
  "summary": {
    "vendor": "cisco",
    "hostname": "LAB-ROUTER",
    "source_name": "lab-router.conf",
    "total_controls": 5,
    "pass_count": 1,
    "fail_count": 3,
    "needs_review_count": 0,
    "not_applicable_count": 1,
    "severity_distribution": {
      "high": 4,
      "critical": 1
    }
  },
  "results": [
    {
      "control_id": "SSH-001",
      "control_name": "SSH Protocol Version",
      "description": "SSH must be configured to use protocol version 2 exclusively...",
      "severity": "high",
      "status": "pass",
      "vendor": "cisco",
      "hostname": "LAB-ROUTER",
      "evidence": [
        {
          "control_id": "SSH-001",
          "section_name": null,
          "raw_lines": ["ip ssh version 2"],
          "observed": "ssh version 2",
          "expected": "ssh version 2",
          "note": "SSH version 2 is explicitly configured globally."
        }
      ],
      "remediations": [],
      "framework_refs": ["CIS-IOS-L2-1.1.1", "NIST-AC-17(2)", "ISO27001-A.9.4.2"]
    }
  ]
}
```

### Example: Error response

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Configuration text is empty or contains only whitespace. Please provide a non-empty device configuration."
  }
}
```

---

## 14. Frontend Integration Rules

> [!IMPORTANT]
> The following rules are **mandatory**. Violations invalidate the compliance product.

1. **The frontend must not duplicate compliance logic.**
   All compliance decisions come from the API. Do not re-implement rule logic in JavaScript/TypeScript.

2. **The frontend must not calculate status independently.**
   Use the `status` field from each `ComplianceResult`. Do not derive status from evidence fields.

3. **The frontend must not invent scores.**
   The API does not return a security score. Do not calculate one from pass/fail counts.
   A number like "60% secure" is misleading and must not appear in the UI.

4. **The frontend must not directly import Python code.**
   The backend is Python. The frontend communicates only through HTTP JSON.

5. **The frontend must only consume documented API contracts.**
   Do not depend on undocumented response fields. They may change without notice.

6. **The frontend must treat `not_applicable` as neutral.**
   `not_applicable` controls must not be shown as failures or included in failure counts.

7. **The frontend must not auto-apply `config_hint`.**
   Remediation config hints are display-only suggestions. Never send them back to a device automatically.

8. **The frontend must not fabricate line numbers.**
   Evidence provides text snippets, not line positions. If highlighting in a config viewer, use text search and label it as approximate.

---

## 15. OpenAPI Schema

The full machine-readable schema is available at:

```
GET http://localhost:8000/openapi.json
```

Interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
