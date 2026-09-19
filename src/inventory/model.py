"""
inventory.model
~~~~~~~~~~~~~~~

Domain model for Phase 3.1: Fleet / Device Inventory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EnvironmentTier(str, Enum):
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    DEVELOPMENT = "DEVELOPMENT"
    LAB = "LAB"
    DMZ = "DMZ"
    CORE = "CORE"


class DevicePostureStatus(str, Enum):
    HEALTHY = "HEALTHY"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class DeviceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


@dataclass
class DeviceRecord:
    """First-class device inventory record."""
    device_id: str
    hostname: str
    vendor: str
    platform: str = "Unknown"
    version: str = "Unknown"
    environment: str = "PRODUCTION"
    location: str | None = None
    owner: str | None = None
    tags: list[str] = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""
    last_audit_id: str | None = None
    current_posture: DevicePostureStatus = DevicePostureStatus.UNKNOWN
    status: DeviceStatus = DeviceStatus.ACTIVE
