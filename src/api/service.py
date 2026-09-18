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
    FrameworkSummary,
    RemediationSchema,
)
from src.compliance.engine import audit
from src.compliance.model import ComplianceResult, ComplianceStatus
from src.compliance.registry import RULE_REGISTRY
from src.ingestion.detector import detect_vendor
from src.parsers.cisco import parse_cisco
from src.parsers.juniper import parse_juniper
from src.mapping.service import SemanticMappingService
from src.mapping.model import SemanticMapping, UnknownPattern
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


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

    # --- Phase 5.1: Semantic Injection Layer --------------------------------
    mapping_svc = None
    try:
        db_path = os.getenv("MAPPINGS_DB_PATH", str(Path(__file__).parent.parent.parent / "mappings.db"))
        mapping_svc = SemanticMappingService(db_path=db_path)
        approved_mappings = mapping_svc.get_approved_mappings(normalized.vendor)
        normalized = _apply_semantic_mappings(normalized, approved_mappings)
    except Exception as e:
        logger.error("Failed to inject semantic mappings: %s", str(e))

    # --- Compliance engine --------------------------------------------------
    results: list[ComplianceResult] = audit(normalized, RULE_REGISTRY)

    # --- Phase 6.1: Unknown Directive Discovery -----------------------------
    try:
        if mapping_svc:
            _discover_unknown_patterns(normalized, results, mapping_svc)
    except Exception as e:
        logger.error("Failed to discover unknown patterns: %s", str(e))

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
# Internal converters and helpers
# ---------------------------------------------------------------------------

def _apply_semantic_mappings(
    config: NormalizedConfig, approved_mappings: list[SemanticMapping]
) -> NormalizedConfig:
    """Inject approved semantic mappings into the NormalizedConfig."""
    if not approved_mappings:
        return config

    mapping_dict: dict[str, SemanticMapping] = {}
    ambiguous_syntax: set[str] = set()

    for mapping in approved_mappings:
        syntax = mapping.original_syntax.strip()
        if syntax in ambiguous_syntax:
            continue
        if syntax in mapping_dict:
            existing = mapping_dict[syntax]
            if (existing.proposed_key != mapping.proposed_key or
                existing.proposed_value != mapping.proposed_value):
                ambiguous_syntax.add(syntax)
                del mapping_dict[syntax]
        else:
            mapping_dict[syntax] = mapping

    if not mapping_dict:
        return config

    def _apply_to_item(item):
        syntax = item.raw_line.strip()
        if syntax in mapping_dict:
            mapping = mapping_dict[syntax]
            item.key = mapping.proposed_key
            item.value = mapping.proposed_value

    for item in config.global_items:
        _apply_to_item(item)
    for section in config.sections:
        for item in section.items:
            _apply_to_item(item)

    return config

def _discover_unknown_patterns(
    config: NormalizedConfig,
    results: list[ComplianceResult],
    mapping_svc: SemanticMappingService
) -> None:
    """Passively discover unmapped configuration directives and persist them."""
    if config.vendor == "unknown":
        return

    # 1. Collect evaluated lines (Evidence subtraction)
    recognized_lines = set()
    for result in results:
        for evidence in result.evidence:
            for raw_line in evidence.raw_lines:
                recognized_lines.add(raw_line.strip())

    # 2. Find parsed lines that were not recognized
    candidates_by_line: dict[str, UnknownPattern] = {}

    def _check_item(item, context: str | None = None):
        line = item.raw_line.strip()
        if not line:
            return
        if line not in recognized_lines and line not in candidates_by_line:
            candidates_by_line[line] = UnknownPattern(
                vendor=config.vendor,
                raw_directive=item.raw_line,  # Preserve original, don't strip
                source_name=config.source_file,
                section_context=context
            )

    for item in config.global_items:
        _check_item(item)

    for section in config.sections:
        for item in section.items:
            _check_item(item, context=section.name)

    if not candidates_by_line:
        return

    # 3. Deduplicate against existing patterns in DB
    existing = mapping_svc.get_known_raw_directives(config.vendor)

    new_patterns = []
    for line, pattern in candidates_by_line.items():
        if line not in existing and pattern.raw_directive not in existing:
            new_patterns.append(pattern)

    # 4. Persist
    if new_patterns:
        mapping_svc.add_unknown_patterns_batch(new_patterns)



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
                line_number=e.line_number,
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
    Framework breakdown is derived from framework_refs on each result.
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

    # Per-framework breakdown — derived from framework_refs prefix matching.
    # Map each framework_ref string to a canonical framework label.
    def _framework_label(ref: str) -> str:
        ref_upper = ref.upper()
        if ref_upper.startswith("CIS"):
            return "CIS"
        if ref_upper.startswith("NIST"):
            return "NIST"
        if ref_upper.startswith("DISA"):
            return "DISA-STIG"
        if ref_upper.startswith("ISO"):
            return "ISO-27001"
        return ref.split("-")[0].upper()

    framework_buckets: dict[str, dict[str, int]] = {}
    for r in results:
        if r.status == ComplianceStatus.NOT_APPLICABLE:
            continue
        seen_frameworks: set[str] = set()
        for ref in r.framework_refs:
            label = _framework_label(ref)
            if label in seen_frameworks:
                continue
            seen_frameworks.add(label)
            if label not in framework_buckets:
                framework_buckets[label] = {"total": 0, "passed": 0, "failed": 0, "needs_review": 0}
            framework_buckets[label]["total"] += 1
            if r.status == ComplianceStatus.PASS:
                framework_buckets[label]["passed"] += 1
            elif r.status == ComplianceStatus.FAIL:
                framework_buckets[label]["failed"] += 1
            elif r.status == ComplianceStatus.NEEDS_REVIEW:
                framework_buckets[label]["needs_review"] += 1

    framework_results = [
        FrameworkSummary(
            framework=label,
            total=counts["total"],
            passed=counts["passed"],
            failed=counts["failed"],
            needs_review=counts["needs_review"],
        )
        for label, counts in sorted(framework_buckets.items())
    ]

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
        framework_results=framework_results,
    )
