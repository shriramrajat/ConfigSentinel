"""
api.schemas
~~~~~~~~~~~

Pydantic models that define the public API contract.

Design rules
------------
- Models mirror the *actual* backend dataclasses exactly.
- No field is invented that doesn't have a backend meaning.
- No fake scoring or fabricated values.
- Use explicit types — avoid ``dict[str, Any]`` for the top-level response.
- All field docstrings must match the compliance model docstrings.

Compliance status values (authoritative)
-----------------------------------------
    PASS           — Configuration satisfies the control requirement.
    FAIL           — Configuration violates the control requirement.
    NOT_APPLICABLE — Control does not apply to this vendor.  Not a failure.
    NEEDS_REVIEW   — Value found but ambiguous; human review required.

Severity values (authoritative)
--------------------------------
    critical / high / medium / low / info
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class AuditRequest(BaseModel):
    """Request body for POST /api/v1/audit.

    The frontend submits raw configuration text obtained from the operator
    (paste, file upload, textarea, etc.).  The backend is responsible for
    vendor detection and parsing — the frontend must NOT pre-process the
    configuration text.

    Fields
    ------
    config_text:
        Raw configuration text of the network device.
        Must be non-empty UTF-8 text.
    source_name:
        Optional human-readable label for this configuration (e.g. filename,
        device name, or "Paste from clipboard").  Used for traceability in
        the response.  Not used for parsing decisions.
    """

    config_text: Annotated[
        str,
        Field(
            description="Raw configuration text of the network device (UTF-8).",
            min_length=1,
        ),
    ]
    source_name: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Optional label for traceability (e.g. filename or device name). "
                "Not used for parsing."
            ),
        ),
    ] = None


# ---------------------------------------------------------------------------
# Response sub-models
# ---------------------------------------------------------------------------


class EvidenceSchema(BaseModel):
    """Evidence linking a compliance decision back to the configuration.

    Traceability note
    -----------------
    ``raw_lines`` contains the verbatim configuration line(s) that the rule
    used to make its decision.
    ``line_number`` is the 1-based line number in the original configuration
    file, when available.  It is ``null`` for rules that aggregate across
    multiple lines or when the parser did not produce line information.
    """

    control_id: Annotated[str, Field(description="Control this evidence belongs to (e.g. 'SSH-001').")]
    section_name: Annotated[
        str | None,
        Field(description="Config section the item was drawn from, or null for global items."),
    ]
    raw_lines: Annotated[
        list[str],
        Field(
            description=(
                "Verbatim configuration line(s) used by the rule.  "
                "Empty list signals absence evidence (the directive was not found).  "
                "These are text snippets — exact line numbers are not available."
            )
        ),
    ]
    observed: Annotated[
        str | None,
        Field(description="Value the rule actually found. Null when the directive was absent."),
    ]
    expected: Annotated[
        str | None,
        Field(description="Value or condition the rule required. Null when not applicable."),
    ]
    note: Annotated[
        str,
        Field(description="Human-readable explanation of why the rule reached its conclusion."),
    ]
    line_number: Annotated[
        int | None,
        Field(
            default=None,
            description=(
                "1-based line number in the original configuration file where the "
                "relevant directive was found.  Null when not available (absence evidence "
                "or multi-line aggregation)."
            ),
        ),
    ] = None


class RemediationSchema(BaseModel):
    """Corrective guidance for a non-compliant control.

    IMPORTANT: ``config_hint`` must never be applied automatically.
    It is advisory only — an operator must review and adapt it.
    """

    vendor: Annotated[
        str,
        Field(description="Vendor this remediation targets (e.g. 'cisco'). 'any' means all vendors."),
    ]
    guidance: Annotated[
        str,
        Field(description="Actionable plain-English instructions."),
    ]
    config_hint: Annotated[
        str | None,
        Field(
            description=(
                "Example configuration snippet illustrating the required change.  "
                "Advisory only — must NOT be applied automatically."
            )
        ),
    ]


class ComplianceResultSchema(BaseModel):
    """Result produced by a single compliance rule evaluation."""

    control_id: Annotated[str, Field(description="Unique control identifier (e.g. 'SSH-001').")]
    control_name: Annotated[str, Field(description="Short human-readable control name.")]
    description: Annotated[str, Field(description="Plain-English description of what the control checks.")]
    severity: Annotated[
        str,
        Field(description="Business-impact severity: critical | high | medium | low | info."),
    ]
    status: Annotated[
        str,
        Field(
            description=(
                "Compliance outcome: pass | fail | not_applicable | needs_review. "
                "not_applicable is NOT a failure — the control does not apply to this vendor."
            )
        ),
    ]
    vendor: Annotated[str, Field(description="Vendor identifier from the evaluated configuration.")]
    hostname: Annotated[
        str | None,
        Field(description="Device hostname from the configuration, or null if absent."),
    ]
    evidence: Annotated[list[EvidenceSchema], Field(description="Evidence records for this result.")]
    remediations: Annotated[
        list[RemediationSchema],
        Field(description="Corrective guidance. Empty when status is 'pass'."),
    ]
    framework_refs: Annotated[
        list[str],
        Field(description="Compliance framework references (e.g. CIS, NIST)."),
    ]
    risk_score: Annotated[
        float,
        Field(
            description=(
                "Deterministic risk score in [0.0, 1.0]. "
                "0.0 for PASS/NOT_APPLICABLE/NEEDS_REVIEW. "
                "Computed as severity_base × confidence_factor for FAIL results."
            )
        ),
    ] = 0.0
    risk_level: Annotated[
        str,
        Field(
            description=(
                "Discrete risk level: critical | high | medium | low | info. "
                "Derived from risk_score. Always 'info' for non-FAIL results."
            )
        ),
    ] = "info"


class FrameworkSummary(BaseModel):
    """Per-framework compliance breakdown.

    Derived from the framework_refs of each ComplianceResult.
    Counts only rules that carry a reference to this framework.
    NOT_APPLICABLE results are excluded from all counts.
    """

    framework: Annotated[str, Field(description="Framework identifier (e.g. 'CIS', 'NIST', 'DISA-STIG').")]
    total: Annotated[int, Field(description="Controls tagged with this framework (excluding NOT_APPLICABLE).")]
    passed: Annotated[int, Field(description="Controls tagged with this framework that passed.")]
    failed: Annotated[int, Field(description="Controls tagged with this framework that failed.")]
    needs_review: Annotated[int, Field(description="Controls tagged with this framework needing review.")]


class AuditSummary(BaseModel):
    """High-level dashboard counts derived from the compliance results.

    These values are computed from the actual ComplianceResult list.
    No scores or metrics are invented beyond what the results contain.
    """

    vendor: Annotated[str, Field(description="Detected vendor identifier.")]
    hostname: Annotated[
        str | None,
        Field(description="Device hostname, or null if not present in the configuration."),
    ]
    source_name: Annotated[
        str | None,
        Field(description="The source_name supplied in the request, if any."),
    ]
    total_controls: Annotated[int, Field(description="Total number of controls evaluated.")]
    pass_count: Annotated[int, Field(description="Controls with status 'pass'.")]
    fail_count: Annotated[int, Field(description="Controls with status 'fail'.")]
    needs_review_count: Annotated[int, Field(description="Controls with status 'needs_review'.")]
    not_applicable_count: Annotated[int, Field(description="Controls with status 'not_applicable'. Not a failure count.")]

    severity_distribution: Annotated[
        dict[str, int],
        Field(
            description=(
                "Count of controls in each severity tier (critical/high/medium/low/info). "
                "Includes all statuses — use pass/fail counts for compliance posture."
            )
        ),
    ]
    framework_results: Annotated[
        list[FrameworkSummary],
        Field(
            description=(
                "Per-framework compliance breakdown. "
                "Each entry covers controls tagged with that framework. "
                "NOT_APPLICABLE controls are excluded."
            )
        ),
    ] = []


class AuditResponse(BaseModel):
    """Complete response for POST /api/v1/audit."""

    summary: Annotated[AuditSummary, Field(description="High-level audit summary for dashboard display.")]
    results: Annotated[
        list[ComplianceResultSchema],
        Field(description="Per-control compliance results in evaluation order."),
    ]


# ---------------------------------------------------------------------------
# Error model (matches the error.py contract)
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Inner error object."""

    code: Annotated[str, Field(description="Machine-readable error code.")]
    message: Annotated[str, Field(description="Human-readable error message safe for client rendering.")]


class ErrorResponse(BaseModel):
    """Envelope for all error responses."""

    error: ErrorDetail


# ---------------------------------------------------------------------------
# Bulk Audit schemas
# ---------------------------------------------------------------------------


class BulkAuditConfigItem(BaseModel):
    """A single configuration entry in a bulk audit request."""

    config_text: Annotated[
        str,
        Field(description="Raw configuration text for this device.", min_length=1),
    ]
    source_name: Annotated[
        str | None,
        Field(
            default=None,
            description="Optional label for this device (e.g. hostname or filename).",
        ),
    ] = None


class BulkAuditRequest(BaseModel):
    """Request body for POST /api/v1/audits/bulk.

    Submits 1–50 device configurations for parallel auditing.
    """

    configs: Annotated[
        list[BulkAuditConfigItem],
        Field(
            description="List of device configurations to audit.",
            min_length=1,
            max_length=50,
        ),
    ]


class BulkAuditResultItem(BaseModel):
    """Result for a single configuration in a bulk audit."""

    source_name: Annotated[
        str | None,
        Field(description="The source_name from the request item, if provided."),
    ]
    status: Annotated[
        str,
        Field(description="'ok' if audit succeeded, 'error' if this item failed."),
    ]
    result: Annotated[
        AuditResponse | None,
        Field(description="Full audit result, or null if status is 'error'."),
    ] = None
    error: Annotated[
        str | None,
        Field(description="Error message if status is 'error', null otherwise."),
    ] = None


class BulkAuditResponse(BaseModel):
    """Response for POST /api/v1/audits/bulk."""

    total: Annotated[int, Field(description="Total number of configs submitted.")]
    succeeded: Annotated[int, Field(description="Number of successfully audited configs.")]
    failed: Annotated[int, Field(description="Number of configs that failed to audit.")]
    results: Annotated[
        list[BulkAuditResultItem],
        Field(description="Per-item audit results in submission order."),
    ]
