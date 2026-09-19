"""
drift.engine
~~~~~~~~~~~~

Deterministic configuration fingerprinting, drift detection, and posture change analysis.

Design Intent
-------------
- Configuration fingerprints use SHA-256 over normalized canonical key/value tuples
  so whitespace or comment differences do not produce fake drift.
- Drift detection compares consecutive NormalizedConfig objects to find added,
  removed, and modified directives.
- Security impact classification compares deterministic ComplianceResult lists
  from consecutive audits to categorize posture change as SECURITY_IMPROVEMENT,
  SECURITY_DEGRADATION, or NEUTRAL. Zero LLM dependency.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

from src.compliance.model import ComplianceResult, ComplianceStatus
from src.normalization.model import NormalizedConfig


class SecurityImpact(str, Enum):
    """Deterministic security impact classification of a configuration drift."""
    SECURITY_IMPROVEMENT = "SECURITY_IMPROVEMENT"
    SECURITY_DEGRADATION = "SECURITY_DEGRADATION"
    NEUTRAL = "NEUTRAL"


@dataclass
class DriftItem:
    """A single configuration change detected between two audits."""
    change_type: str  # "ADDED" | "REMOVED" | "MODIFIED"
    key: str
    old_value: str | None = None
    new_value: str | None = None
    raw_line: str | None = None


@dataclass
class PostureDelta:
    """Deterministic security posture comparison between two consecutive audits."""
    previous_audit_id: str | None
    current_audit_id: str
    security_impact: SecurityImpact
    new_failures: list[str] = field(default_factory=list)
    resolved_failures: list[str] = field(default_factory=list)
    previous_fail_count: int = 0
    current_fail_count: int = 0
    previous_pass_count: int = 0
    current_pass_count: int = 0
    drift_items: list[DriftItem] = field(default_factory=list)


def compute_config_fingerprint(config: NormalizedConfig) -> str:
    """Compute deterministic SHA-256 fingerprint over normalized config items."""
    canonical_items: list[str] = []

    for item in config.global_items:
        canonical_items.append(f"GLOBAL::{item.key.strip().lower()}={ (item.value or '').strip().lower() }")

    for section in config.sections:
        for item in section.items:
            canonical_items.append(f"SECTION::{section.name.strip().lower()}::{item.key.strip().lower()}={ (item.value or '').strip().lower() }")

    canonical_items.sort()
    canonical_payload = "\n".join(canonical_items)
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def detect_config_drift(prev_config: NormalizedConfig, curr_config: NormalizedConfig) -> list[DriftItem]:
    """Compare two NormalizedConfig objects and return list of drift items."""
    drift: list[DriftItem] = []

    def _build_item_map(cfg: NormalizedConfig) -> dict[str, str | None]:
        m: dict[str, str | None] = {}
        for item in cfg.global_items:
            m[f"global::{item.key.strip().lower()}"] = item.value
        for sec in cfg.sections:
            for item in sec.items:
                m[f"sec::{sec.name.strip().lower()}::{item.key.strip().lower()}"] = item.value
        return m

    prev_map = _build_item_map(prev_config)
    curr_map = _build_item_map(curr_config)

    # Detect added and modified
    for key, val in curr_map.items():
        if key not in prev_map:
            drift.append(DriftItem(change_type="ADDED", key=key, new_value=val))
        elif prev_map[key] != val:
            drift.append(DriftItem(change_type="MODIFIED", key=key, old_value=prev_map[key], new_value=val))

    # Detect removed
    for key, val in prev_map.items():
        if key not in curr_map:
            drift.append(DriftItem(change_type="REMOVED", key=key, old_value=val))

    return drift


def compute_posture_delta(
    prev_results: list[ComplianceResult] | None,
    curr_results: list[ComplianceResult],
    previous_audit_id: str | None = None,
    current_audit_id: str = "",
    drift_items: list[DriftItem] | None = None,
) -> PostureDelta:
    """Compute deterministic posture delta between previous and current compliance results."""
    curr_fails = {r.control_id for r in curr_results if r.status == ComplianceStatus.FAIL}
    curr_passes = {r.control_id for r in curr_results if r.status == ComplianceStatus.PASS}

    if not prev_results:
        return PostureDelta(
            previous_audit_id=previous_audit_id,
            current_audit_id=current_audit_id,
            security_impact=SecurityImpact.NEUTRAL,
            new_failures=[],
            resolved_failures=[],
            previous_fail_count=0,
            current_fail_count=len(curr_fails),
            previous_pass_count=0,
            current_pass_count=len(curr_passes),
            drift_items=drift_items or [],
        )

    prev_fails = {r.control_id for r in prev_results if r.status == ComplianceStatus.FAIL}
    prev_passes = {r.control_id for r in prev_results if r.status == ComplianceStatus.PASS}

    new_failures = sorted(list(curr_fails - prev_fails))
    resolved_failures = sorted(list(prev_fails - curr_fails))

    if len(new_failures) > len(resolved_failures):
        impact = SecurityImpact.SECURITY_DEGRADATION
    elif len(resolved_failures) > len(new_failures):
        impact = SecurityImpact.SECURITY_IMPROVEMENT
    else:
        impact = SecurityImpact.NEUTRAL

    return PostureDelta(
        previous_audit_id=previous_audit_id,
        current_audit_id=current_audit_id,
        security_impact=impact,
        new_failures=new_failures,
        resolved_failures=resolved_failures,
        previous_fail_count=len(prev_fails),
        current_fail_count=len(curr_fails),
        previous_pass_count=len(prev_passes),
        current_pass_count=len(curr_passes),
        drift_items=drift_items or [],
    )
