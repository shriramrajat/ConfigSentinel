"""
scheduling.service
~~~~~~~~~~~~~~~~~~

Audit Scheduling & Recurring Audit State Service.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.scheduling.model import AuditScheduleJob, JobStatus, ScheduleInterval


def init_schedules_db(db_path: str) -> None:
    """Ensure schedules table exists in SQLite."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_schedules (
                job_id      TEXT PRIMARY KEY,
                device_id   TEXT NOT NULL,
                interval    TEXT NOT NULL DEFAULT 'DAILY',
                last_run    TEXT,
                next_run    TEXT,
                status      TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at  TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


class AuditScheduleService:
    """Manager for device audit job schedules."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))
        self.db_path = db_path
        init_schedules_db(self.db_path)

    def create_schedule(
        self,
        device_id: str,
        interval: ScheduleInterval | str = ScheduleInterval.DAILY,
    ) -> AuditScheduleJob:
        """Create or update an audit schedule for a device."""
        now = datetime.now(timezone.utc)
        int_val = interval.value if isinstance(interval, ScheduleInterval) else interval

        if int_val == "HOURLY":
            next_dt = now + timedelta(hours=1)
        elif int_val == "WEEKLY":
            next_dt = now + timedelta(days=7)
        else:
            next_dt = now + timedelta(days=1)

        job_id = f"job-{uuid.uuid4().hex[:8]}"

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO audit_schedules (job_id, device_id, interval, last_run, next_run, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (job_id, device_id, int_val, None, next_dt.isoformat(), JobStatus.ACTIVE.value, now.isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

        return AuditScheduleJob(
            job_id=job_id,
            device_id=device_id,
            interval=ScheduleInterval(int_val) if int_val in [e.value for e in ScheduleInterval] else ScheduleInterval.DAILY,
            last_run=None,
            next_run=next_dt.isoformat(),
            status=JobStatus.ACTIVE,
            created_at=now.isoformat(),
        )

    def list_schedules(self) -> list[AuditScheduleJob]:
        """List all configured audit schedules."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM audit_schedules ORDER BY created_at DESC")
            rows = cur.fetchall()
            return [
                AuditScheduleJob(
                    job_id=r["job_id"],
                    device_id=r["device_id"],
                    interval=ScheduleInterval(r["interval"]) if r["interval"] in [e.value for e in ScheduleInterval] else ScheduleInterval.DAILY,
                    last_run=r["last_run"],
                    next_run=r["next_run"],
                    status=JobStatus(r["status"]) if r["status"] in [e.value for e in JobStatus] else JobStatus.ACTIVE,
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        finally:
            conn.close()
