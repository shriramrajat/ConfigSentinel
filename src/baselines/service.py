"""
baselines.service
~~~~~~~~~~~~~~~~~

Immutable Configuration Baseline Management and Drift Comparison Service.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.api.schemas import AuditRequest
from src.api.service import run_audit
from src.baselines.model import BaselineComparisonResult, BaselineRecord, BaselineStatus
from src.drift.engine import detect_config_drift
from src.mapping.redaction import redact_secrets


def init_baselines_db(db_path: str) -> None:
    """Ensure baselines table exists in SQLite."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS baselines (
                baseline_id TEXT PRIMARY KEY,
                device_id   TEXT NOT NULL,
                version     INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL,
                created_by  TEXT NOT NULL DEFAULT 'secops_admin',
                fingerprint TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'APPROVED',
                pass_count  INTEGER NOT NULL DEFAULT 0,
                fail_count  INTEGER NOT NULL DEFAULT 0,
                config_text TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_baselines_device ON baselines (device_id, version DESC)")
        conn.commit()
    finally:
        conn.close()


def _parse_vendor_config(vendor: str | None, config_text: str):
    from src.ingestion.detector import detect_vendor
    v = (vendor or str(detect_vendor(config_text))).lower()
    if "juniper" in v:
        from src.parsers.juniper import parse_juniper
        return parse_juniper(config_text)
    elif "arista" in v:
        from src.parsers.arista import parse_arista
        return parse_arista(config_text)
    elif "forti" in v:
        from src.parsers.fortios import parse_fortios
        return parse_fortios(config_text)
    elif "pan" in v:
        from src.parsers.panos import parse_panos
        return parse_panos(config_text)
    else:
        from src.parsers.cisco import parse_cisco
        return parse_cisco(config_text)


class BaselineService:
    """Manager for immutable device configuration baselines."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))
        self.db_path = db_path
        init_baselines_db(self.db_path)

    def create_baseline(
        self,
        device_id: str,
        config_text: str,
        created_by: str = "secops_admin",
        vendor: str | None = None,
    ) -> BaselineRecord:
        """Create a new immutable baseline version for a device."""
        now = datetime.now(timezone.utc).isoformat()
        audit_res = run_audit(AuditRequest(config_text=config_text, vendor=vendor), persist=False)
        fp = hashlib.sha256(config_text.encode("utf-8")).hexdigest()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT MAX(version) as max_v FROM baselines WHERE device_id = ?", (device_id,))
            row = cur.fetchone()
            next_version = (row["max_v"] or 0) + 1 if row else 1

            # Archive older baselines for this device
            cur.execute("UPDATE baselines SET status = 'ARCHIVED' WHERE device_id = ? AND status = 'APPROVED'", (device_id,))

            baseline_id = f"base-{uuid.uuid4().hex[:8]}"
            cur.execute(
                """
                INSERT INTO baselines (
                    baseline_id, device_id, version, created_at, created_by,
                    fingerprint, status, pass_count, fail_count, config_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    baseline_id,
                    device_id,
                    next_version,
                    now,
                    created_by,
                    fp,
                    BaselineStatus.APPROVED.value,
                    audit_res.summary.pass_count,
                    audit_res.summary.fail_count,
                    config_text,
                ),
            )
            conn.commit()

            return BaselineRecord(
                baseline_id=baseline_id,
                device_id=device_id,
                version=next_version,
                created_at=now,
                created_by=created_by,
                fingerprint=fp,
                status=BaselineStatus.APPROVED,
                pass_count=audit_res.summary.pass_count,
                fail_count=audit_res.summary.fail_count,
                config_text=config_text,
            )
        finally:
            conn.close()

    def get_latest_baseline(self, device_id: str) -> BaselineRecord | None:
        """Fetch the active approved baseline for a device."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM baselines WHERE device_id = ? AND status = 'APPROVED' ORDER BY version DESC LIMIT 1", (device_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            conn.close()

    def compare_with_baseline(
        self,
        device_id: str,
        current_config_text: str,
        vendor: str | None = None,
    ) -> BaselineComparisonResult:
        """Compare a candidate current configuration against the approved baseline."""
        baseline = self.get_latest_baseline(device_id)
        if not baseline:
            # Baseline does not exist yet; auto-baseline
            baseline = self.create_baseline(device_id, current_config_text, vendor=vendor)

        norm_base = _parse_vendor_config(vendor, baseline.config_text)
        norm_curr = _parse_vendor_config(vendor, current_config_text)

        drift_items = detect_config_drift(norm_base, norm_curr)

        added = [redact_secrets(f"{d.key} ({d.new_value or ''})") for d in drift_items if d.change_type == "ADDED"]
        removed = [redact_secrets(f"{d.key} ({d.old_value or ''})") for d in drift_items if d.change_type == "REMOVED"]
        modified = [
            {
                "directive": d.key,
                "old_value": redact_secrets(d.old_value or ""),
                "new_value": redact_secrets(d.new_value or ""),
            }
            for d in drift_items
            if d.change_type == "MODIFIED"
        ]

        sec_drift = len(added) > 0 or len(removed) > 0 or len(modified) > 0

        return BaselineComparisonResult(
            baseline_id=baseline.baseline_id,
            device_id=device_id,
            baseline_version=baseline.version,
            is_compliant_with_baseline=not sec_drift,
            added_directives=added,
            removed_directives=removed,
            modified_directives=modified,
            security_drift_detected=sec_drift,
        )

    def _row_to_record(self, row: sqlite3.Row) -> BaselineRecord:
        st = row["status"]
        st_enum = BaselineStatus(st) if st in [e.value for e in BaselineStatus] else BaselineStatus.APPROVED
        return BaselineRecord(
            baseline_id=row["baseline_id"],
            device_id=row["device_id"],
            version=row["version"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            fingerprint=row["fingerprint"],
            status=st_enum,
            pass_count=row["pass_count"],
            fail_count=row["fail_count"],
            config_text=row["config_text"],
        )
