"""
mapping.model
~~~~~~~~~~~~~

Domain models for the AI Semantic Mapping architecture.

These models represent unknown configuration patterns and proposed
semantic mappings before they are integrated into the deterministic
compliance engine.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


class PatternStatus(enum.Enum):
    """Lifecycle status of an unknown pattern."""
    PENDING = "pending"
    MAPPED = "mapped"
    REJECTED = "rejected"


class HumanApprovalState(enum.Enum):
    """Approval state of a proposed semantic mapping."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SemanticCategory(enum.Enum):
    """Controlled taxonomy of network security directive semantics."""
    SSH_SECURITY = "SSH_SECURITY"
    TELNET_SECURITY = "TELNET_SECURITY"
    AAA_AUTHENTICATION = "AAA_AUTHENTICATION"
    PASSWORD_SECURITY = "PASSWORD_SECURITY"
    SESSION_TIMEOUT = "SESSION_TIMEOUT"
    LOGGING = "LOGGING"
    NTP_TIME_SYNC = "NTP_TIME_SYNC"
    SNMP_SECURITY = "SNMP_SECURITY"
    HTTP_MANAGEMENT = "HTTP_MANAGEMENT"
    SERVICE_HARDENING = "SERVICE_HARDENING"
    ACCESS_CONTROL = "ACCESS_CONTROL"
    CRYPTOGRAPHY = "CRYPTOGRAPHY"
    BANNER_SECURITY = "BANNER_SECURITY"
    DNS_SECURITY = "DNS_SECURITY"
    NETWORK_MANAGEMENT = "NETWORK_MANAGEMENT"
    AUTHORIZATION = "AUTHORIZATION"
    AUDIT_LOGGING = "AUDIT_LOGGING"
    REMOTE_ACCESS = "REMOTE_ACCESS"
    MANAGEMENT_PLANE_SECURITY = "MANAGEMENT_PLANE_SECURITY"
    OTHER = "OTHER"
    UNRESOLVED = "UNRESOLVED"


@dataclass
class UnknownPattern:
    """An unrecognized configuration directive that could not be parsed."""
    
    vendor: str
    raw_directive: str
    source_name: str | None = None
    section_context: str | None = None
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: PatternStatus = field(default=PatternStatus.PENDING)
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SemanticMapping:
    """A proposed translation from raw syntax to the vendor-neutral model.
    
    This is strictly a proposal. It does NOT assert compliance PASS/FAIL,
    does NOT define severity, and MUST NOT be used by the compliance engine
    until `approval_state` is HumanApprovalState.APPROVED.
    """
    
    pattern_id: str
    original_syntax: str
    proposed_key: str
    proposed_value: str | None
    explanation: str
    confidence: float
    
    semantic_category: SemanticCategory = field(default=SemanticCategory.OTHER)
    mapping_version: int = 1
    usage_count: int = 0
    last_used_at: datetime | None = None
    approved_by: str | None = None
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    approval_state: HumanApprovalState = field(default=HumanApprovalState.PENDING)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
