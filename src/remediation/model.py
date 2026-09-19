"""
remediation.model
~~~~~~~~~~~~~~~~~

Data models for Phase 3.3 Remediation Intelligence and 3.4 Verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VendorRemediationInstruction:
    vendor: str
    platform: str
    syntax: str
    verification_command: str
    preconditions: str = "Standard administrative privileges"


@dataclass
class RemediationObject:
    intent_id: str
    control_id: str
    title: str
    goal: str
    risk_notes: str
    instructions: list[VendorRemediationInstruction] = field(default_factory=list)


@dataclass
class RemediationVerificationResult:
    finding_id: str
    control_id: str
    status: str  # "FIX_VERIFIED" | "FIX_NOT_VERIFIED"
    previous_status: str
    current_status: str
    previous_risk_score: float
    current_risk_score: float
    evidence_note: str
    verification_timestamp: str
