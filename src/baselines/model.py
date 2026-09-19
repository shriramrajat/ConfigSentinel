"""
baselines.model
~~~~~~~~~~~~~~~

Data models for Phase 3.5 Configuration Baselines.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BaselineStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"


@dataclass
class BaselineRecord:
    baseline_id: str
    device_id: str
    version: int  # 1, 2, 3...
    created_at: str
    created_by: str
    fingerprint: str
    status: BaselineStatus
    pass_count: int
    fail_count: int
    config_text: str


@dataclass
class BaselineComparisonResult:
    baseline_id: str
    device_id: str
    baseline_version: int
    is_compliant_with_baseline: bool
    added_directives: list[str]
    removed_directives: list[str]
    modified_directives: list[dict[str, str]]
    security_drift_detected: bool
