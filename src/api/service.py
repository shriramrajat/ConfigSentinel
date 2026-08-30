"""
api.service
~~~~~~~~~~~

Thin orchestration layer between the HTTP transport and the compliance pipeline.

Responsibilities
----------------
- Accept raw configuration TEXT (not filesystem paths).
- Detect vendor.
- Dispatch to the correct vendor parser.
- Run the compliance engine.
- Convert backend dataclasses → API Pydantic schemas.
- Raise InvalidInputError for problems that must produce a 400 response.

This module must NOT:
- Contain parser logic.
- Contain compliance rule logic.
- Contain vendor-specific audit logic.
- Expose filesystem paths to callers.

The conversion from backend dataclasses to API schemas lives here because it
is a transport concern: how backend types map to JSON wire types.
"""

from __future__ import annotations

import dataclasses

from src.api.errors import InvalidInputError
from src.api.schemas import (
    AuditRequest,
    AuditResponse,
    AuditSummary,
    ComplianceResultSchema,
    EvidenceSchema,
    RemediationSchema,
)
from src.compliance.engine import audit
from src.compliance.model import ComplianceResult, ComplianceStatus
from src.compliance.registry import RULE_REGISTRY
from src.ingestion.detector import detect_vendor
from src.parsers.cisco import parse_cisco
from src.parsers.juniper import parse_juniper


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_audit(request: AuditRequest) -> AuditResponse:
    """Run the full compliance pipeline for a configuration text request.

    Parameters
    ----------
    request:
        Validated AuditRequest from the HTTP layer.

    Returns
    -------
    AuditResponse
        Serialisable audit response including summary and per-control results.

    Raises
    ------
    InvalidInputError
        When the configuration text cannot be used (empty after stripping,
        or vendor is unknown/unsupported for auditing).
    """
    config_text = request.config_text.strip()
    if not config_text:
        raise InvalidInputError(
            "Configuration text is empty or contains only whitespace. "
            "Please provide a non-empty device configuration."
        )

    # --- Vendor detection ---------------------------------------------------
    vendor = detect_vendor(config_text)

    # --- Parse --------------------------------------------------------------
    if vendor == "cisco":
        normalized = parse_cisco(config_text)
    elif vendor == "juniper":
        normalized = parse_juniper(config_text)
    else:
        # Unknown vendor: still run the engine — rules will return NOT_APPLICABLE.
        # This is the correct behaviour; rules self-select based on vendor.
        # We attempt a best-effort cisco parse for structural extraction,
        # then override vendor to "unknown" so rules correctly return NOT_APPLICABLE.
        _parsed = parse_cisco(config_text)
        normalized = dataclasses.replace(_parsed, vendor="unknown")

    # Attach the source_name as the source_file for traceability.
    # This is a label only — it is NOT a filesystem path.
    normalized.source_file = request.source_name

    # --- Compliance engine --------------------------------------------------
    results: list[ComplianceResult] = audit(normalized, RULE_REGISTRY)

    # --- Convert to schemas -------------------------------------------------
    result_schemas = [_convert_result(r) for r in results]
    summary = _build_summary(
        vendor=normalized.vendor,
        hostname=normalized.hostname,
        source_name=request.source_name,
        results=results,
    )

    return AuditResponse(summary=summary, results=result_schemas)


# ---------------------------------------------------------------------------
# Internal converters
# ---------------------------------------------------------------------------


def _convert_result(result: ComplianceResult) -> ComplianceResultSchema:
    """Convert a ComplianceResult dataclass → ComplianceResultSchema."""
    return ComplianceResultSchema(
        control_id=result.control_id,
        control_name=result.control_name,
        description=result.description,
        severity=result.severity.value,
        status=result.status.value,
        vendor=result.vendor,
        hostname=result.hostname,
        evidence=[
            EvidenceSchema(
                control_id=e.control_id,
                section_name=e.section_name,
                raw_lines=list(e.raw_lines),
                observed=e.observed,
                expected=e.expected,
                note=e.note,
            )
            for e in result.evidence
        ],
        remediations=[
            RemediationSchema(
                vendor=r.vendor,
                guidance=r.guidance,
                config_hint=r.config_hint,
            )
            for r in result.remediations
        ],
        framework_refs=list(result.framework_refs),
    )


def _build_summary(
    vendor: str,
    hostname: str | None,
    source_name: str | None,
    results: list[ComplianceResult],
) -> AuditSummary:
    """Derive AuditSummary from the actual result list.

    No invented metrics.  Counts are derived from ComplianceStatus values.
    """
    pass_count = sum(1 for r in results if r.status == ComplianceStatus.PASS)
    fail_count = sum(1 for r in results if r.status == ComplianceStatus.FAIL)
    needs_review_count = sum(1 for r in results if r.status == ComplianceStatus.NEEDS_REVIEW)
    not_applicable_count = sum(1 for r in results if r.status == ComplianceStatus.NOT_APPLICABLE)

    # Severity distribution across ALL results (regardless of pass/fail).
    severity_distribution: dict[str, int] = {}
    for r in results:
        key = r.severity.value
        severity_distribution[key] = severity_distribution.get(key, 0) + 1

    return AuditSummary(
        vendor=vendor,
        hostname=hostname,
        source_name=source_name,
        total_controls=len(results),
        pass_count=pass_count,
        fail_count=fail_count,
        needs_review_count=needs_review_count,
        not_applicable_count=not_applicable_count,
        severity_distribution=severity_distribution,
    )
