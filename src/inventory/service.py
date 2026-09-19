"""
inventory.service
~~~~~~~~~~~~~~~~~

Service layer for managing the Fleet Device Inventory in SQLite.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.inventory.model import DevicePostureStatus, DeviceRecord, DeviceStatus


def init_inventory_db(db_path: str) -> None:
    """Ensure the devices table exists in SQLite."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
                device_id       TEXT PRIMARY KEY,
                hostname        TEXT NOT NULL,
                vendor          TEXT NOT NULL,
                platform        TEXT NOT NULL DEFAULT 'Unknown',
                version         TEXT NOT NULL DEFAULT 'Unknown',
                environment     TEXT NOT NULL DEFAULT 'PRODUCTION',
                location        TEXT,
                owner           TEXT,
                tags_json       TEXT NOT NULL DEFAULT '[]',
                first_seen      TEXT NOT NULL,
                last_seen       TEXT NOT NULL,
                last_audit_id   TEXT,
                current_posture TEXT NOT NULL DEFAULT 'UNKNOWN',
                status          TEXT NOT NULL DEFAULT 'ACTIVE'
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_vendor ON devices (vendor)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_env ON devices (environment)")
        conn.commit()
    finally:
        conn.close()


class DeviceInventoryService:
    """Manager for fleet device records."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))
        self.db_path = db_path
        init_inventory_db(self.db_path)

    def register_or_update_device(
        self,
        hostname: str,
        vendor: str,
        platform: str = "Unknown",
        version: str = "Unknown",
        environment: str = "PRODUCTION",
        location: str | None = None,
        owner: str | None = None,
        tags: list[str] | None = None,
        last_audit_id: str | None = None,
        current_posture: str | DevicePostureStatus = DevicePostureStatus.UNKNOWN,
    ) -> DeviceRecord:
        """Create or update a device record by hostname."""
        tags_list = tags or []
        now = datetime.now(timezone.utc).isoformat()
        posture_str = current_posture.value if isinstance(current_posture, DevicePostureStatus) else current_posture

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM devices WHERE hostname = ?", (hostname,))
            row = cur.fetchone()

            if row:
                device_id = row["device_id"]
                first_seen = row["first_seen"]
                cur.execute(
                    """
                    UPDATE devices
                    SET vendor = ?, platform = ?, version = ?, environment = ?, location = ?, owner = ?,
                        tags_json = ?, last_seen = ?, last_audit_id = COALESCE(?, last_audit_id), current_posture = ?
                    WHERE device_id = ?
                    """,
                    (
                        vendor,
                        platform,
                        version,
                        environment,
                        location,
                        owner,
                        json.dumps(tags_list),
                        now,
                        last_audit_id,
                        posture_str,
                        device_id,
                    ),
                )
            else:
                device_id = f"dev-{uuid.uuid4().hex[:8]}"
                first_seen = now
                cur.execute(
                    """
                    INSERT INTO devices (
                        device_id, hostname, vendor, platform, version, environment,
                        location, owner, tags_json, first_seen, last_seen, last_audit_id, current_posture, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        device_id,
                        hostname,
                        vendor,
                        platform,
                        version,
                        environment,
                        location,
                        owner,
                        json.dumps(tags_list),
                        first_seen,
                        now,
                        last_audit_id,
                        posture_str,
                        DeviceStatus.ACTIVE.value,
                    ),
                )
            conn.commit()

            return DeviceRecord(
                device_id=device_id,
                hostname=hostname,
                vendor=vendor,
                platform=platform,
                version=version,
                environment=environment,
                location=location,
                owner=owner,
                tags=tags_list,
                first_seen=first_seen,
                last_seen=now,
                last_audit_id=last_audit_id,
                current_posture=DevicePostureStatus(posture_str) if posture_str in DevicePostureStatus.__members__ else DevicePostureStatus.UNKNOWN,
                status=DeviceStatus.ACTIVE,
            )
        finally:
            conn.close()

    def get_device(self, device_id: str) -> DeviceRecord | None:
        """Fetch device by ID or hostname."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM devices WHERE device_id = ? OR hostname = ?", (device_id, device_id))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_record(row)
        finally:
            conn.close()

    def list_devices(
        self,
        vendor: str | None = None,
        environment: str | None = None,
        posture: str | None = None,
        search: str | None = None,
    ) -> list[DeviceRecord]:
        """List and filter fleet devices."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            query = "SELECT * FROM devices WHERE 1=1"
            params: list[str] = []

            if vendor:
                query += " AND LOWER(vendor) = LOWER(?)"
                params.append(vendor)
            if environment:
                query += " AND LOWER(environment) = LOWER(?)"
                params.append(environment)
            if posture:
                query += " AND UPPER(current_posture) = UPPER(?)"
                params.append(posture)
            if search:
                query += " AND (hostname LIKE ? OR location LIKE ? OR owner LIKE ?)"
                pattern = f"%{search}%"
                params.extend([pattern, pattern, pattern])

            query += " ORDER BY hostname ASC"
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            return [self._row_to_record(r) for r in rows]
        finally:
            conn.close()

    def _row_to_record(self, row: sqlite3.Row) -> DeviceRecord:
        tags = json.loads(row["tags_json"]) if row["tags_json"] else []
        posture = row["current_posture"]
        posture_enum = DevicePostureStatus(posture) if posture in [e.value for e in DevicePostureStatus] else DevicePostureStatus.UNKNOWN
        status = row["status"]
        status_enum = DeviceStatus(status) if status in [e.value for e in DeviceStatus] else DeviceStatus.ACTIVE

        return DeviceRecord(
            device_id=row["device_id"],
            hostname=row["hostname"],
            vendor=row["vendor"],
            platform=row["platform"],
            version=row["version"],
            environment=row["environment"],
            location=row["location"],
            owner=row["owner"],
            tags=tags,
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
            last_audit_id=row["last_audit_id"],
            current_posture=posture_enum,
            status=status_enum,
        )
