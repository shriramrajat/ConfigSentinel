"""
scheduling.model
~~~~~~~~~~~~~~~~

Domain models for Phase 3.6 Scheduled & Continuous Audit Architecture.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScheduleInterval(str, Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MANUAL = "MANUAL"


class JobStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


@dataclass
class AuditScheduleJob:
    job_id: str
    device_id: str
    interval: ScheduleInterval
    last_run: str | None
    next_run: str | None
    status: JobStatus
    created_at: str
