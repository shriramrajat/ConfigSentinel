"""
risk.engine
~~~~~~~~~~~

Deterministic risk scoring for compliance findings.

Formula
-------
Only FAIL results receive a non-zero risk score.  PASS, NEEDS_REVIEW,
and NOT_APPLICABLE produce a score of 0.0 and level INFO.

For FAIL results:

    base_score = severity_base_score[severity]
    risk_score  = base_score × confidence_factor

Where confidence_factor accounts for whether the finding came from a
deterministic rule (1.0), an AI-approved mapping (0.9), or a source
whose confidence is unknown (0.75).

Risk level thresholds (deterministic, derived from risk_score):
    >= 0.85 → CRITICAL
    >= 0.65 → HIGH
    >= 0.40 → MEDIUM
    >= 0.15 → LOW
    <  0.15 → INFO

Rationale
---------
The formula is intentionally simple to remain auditable and explainable.
Complexity would invite gaming.  Each parameter is documented below.

Severity base scores:
    CRITICAL → 1.00
    HIGH     → 0.80
    MEDIUM   → 0.55
    LOW      → 0.30
    INFO     → 0.10

Confidence factor:
    DETERMINISTIC → 1.0  (rule produced a definitive FAIL from parsed config)
    AI_APPROVED   → 0.9  (AI-mapped and human-approved, small residual uncertainty)
    DEFAULT       → 0.75 (conservative default for unknown source)
"""

from __future__ import annotations

from enum import Enum

from src.compliance.model import ComplianceResult, ComplianceStatus, Severity


class RiskLevel(str, Enum):
    """Deterministic risk level derived from risk_score."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ---------------------------------------------------------------------------
# Configuration tables — modify here to adjust thresholds globally
# ---------------------------------------------------------------------------

_SEVERITY_BASE: dict[Severity, float] = {
    Severity.CRITICAL: 1.00,
    Severity.HIGH: 0.80,
    Severity.MEDIUM: 0.55,
    Severity.LOW: 0.30,
    Severity.INFO: 0.10,
}

_RISK_THRESHOLDS: list[tuple[float, RiskLevel]] = [
    (0.85, RiskLevel.CRITICAL),
    (0.65, RiskLevel.HIGH),
    (0.40, RiskLevel.MEDIUM),
    (0.15, RiskLevel.LOW),
    (0.00, RiskLevel.INFO),
]

# Confidence factors — kept low-variance to prevent gaming
_CONFIDENCE_DETERMINISTIC: float = 1.0
_CONFIDENCE_AI_APPROVED: float = 0.9
_CONFIDENCE_DEFAULT: float = 0.75


def _risk_level(score: float) -> RiskLevel:
    """Map a continuous risk score to a discrete risk level."""
    for threshold, level in _RISK_THRESHOLDS:
        if score >= threshold:
            return level
    return RiskLevel.INFO


def compute_risk(result: ComplianceResult) -> tuple[float, RiskLevel]:
    """Compute deterministic risk score and level for a compliance result.

    Parameters
    ----------
    result:
        A :class:`~compliance.model.ComplianceResult` from the compliance engine.

    Returns
    -------
    tuple[float, RiskLevel]
        ``(risk_score, risk_level)`` where risk_score is in [0.0, 1.0].
        Non-FAIL results always return ``(0.0, RiskLevel.INFO)``.
    """
    if result.status != ComplianceStatus.FAIL:
        return 0.0, RiskLevel.INFO

    base = _SEVERITY_BASE.get(result.severity, _SEVERITY_BASE[Severity.MEDIUM])

    # Confidence factor: currently all rules are deterministic (1.0).
    # When AI-assisted mapping is in play this will be lowered to 0.9.
    confidence = _CONFIDENCE_DETERMINISTIC

    score = round(base * confidence, 4)
    return score, _risk_level(score)
