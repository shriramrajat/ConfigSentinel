"""
intelligence.model
~~~~~~~~~~~~~~~~~~

Domain models for Phase 2: Cross-Vendor Security Intelligence.

Design Intent:
- Vendor-neutral abstraction for security intent (e.g. TELNET_DISABLED, SSH_VERSION_ENFORCED).
- Explicit implementation capability statuses (SUPPORTED, PARTIAL, UNSUPPORTED, UNKNOWN).
- Strict separation between vendor-neutral intent and vendor-specific evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ImplementationStatus(str, Enum):
    """Capability status of a security intent on a vendor platform."""
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


@dataclass
class SecurityIntent:
    """Vendor-neutral security intent declaration."""
    id: str  # e.g., "TELNET_DISABLED"
    name: str  # e.g., "Telnet Management Disabled"
    category: str  # e.g., "MANAGEMENT_PLANE_SECURITY"
    description: str
    security_domain: str  # e.g., "Remote Management"
    related_control_ids: list[str] = field(default_factory=list)


@dataclass
class VendorImplementation:
    """Vendor-specific implementation capability for a security intent."""
    vendor: str
    platform: str
    intent_id: str
    implementation_status: ImplementationStatus
    syntax_example: str | None = None
    note: str | None = None


@dataclass
class SecurityPolicy:
    """High-level vendor-neutral security policy definition."""
    id: str
    name: str
    description: str
    required_intent_ids: list[str] = field(default_factory=list)


@dataclass
class VendorPolicyTranslation:
    """Translated policy requirements for a specific vendor."""
    vendor: str
    supported_intents: list[str] = field(default_factory=list)
    unsupported_intents: list[str] = field(default_factory=list)
    syntax_guidance: list[dict[str, str]] = field(default_factory=list)


@dataclass
class PolicyTranslationResult:
    """Complete cross-vendor policy translation response."""
    policy_id: str
    policy_name: str
    description: str
    translations: list[VendorPolicyTranslation] = field(default_factory=list)


@dataclass
class ControlDependencyNode:
    """Dependency relationship node between security controls."""
    control_id: str
    control_name: str
    depends_on: list[str] = field(default_factory=list)
    amplifies: list[str] = field(default_factory=list)
    threat_scenario: str = ""


@dataclass
class SimulationIntentChange:
    """Proposed security intent modification for simulation."""
    intent_id: str
    desired_status: str  # "PASS" | "FAIL"


@dataclass
class SimulationResult:
    """Deterministic what-if simulation output."""
    is_simulated: bool = True
    original_fail_count: int = 0
    projected_fail_count: int = 0
    original_pass_count: int = 0
    projected_pass_count: int = 0
    original_risk_score: float = 0.0
    projected_risk_score: float = 0.0
    resolved_control_ids: list[str] = field(default_factory=list)
    remaining_fail_control_ids: list[str] = field(default_factory=list)
    applied_intent_ids: list[str] = field(default_factory=list)
    security_impact: str = "NEUTRAL"
