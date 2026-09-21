"""
audit_store.service
~~~~~~~~~~~~~~~~~~~

Persist and retrieve AuditResponse objects from SQLite.

Design intent
-------------
- ``save_audit()`` writes the full JSON to the DB plus denormalized counts
  for fast listing queries.
- ``list_audits()`` returns lightweight ``AuditListItem`` objects — no JSON
  deserialization needed for a list view.
- ``get_audit()`` returns the full JSON blob for detail views.
- All operations are synchronous (SQLite is fast enough for this workload).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from src.audit_store.db import get_audit_db, init_audit_db
from src.api.schemas import AuditResponse
from src.mapping.redaction import redact_secrets


class AuditStoreService:
    """Persist and retrieve audit results in SQLite."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        init_audit_db(db_path)

    def save_audit(self, response: AuditResponse) -> str:
        """Persist an AuditResponse and return its generated ID."""
        audit_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        result_json = redact_secrets(response.model_dump_json())

        with get_audit_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO audits
                (id, vendor, hostname, source_name, created_at, fail_count, pass_count, total, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    response.summary.vendor,
                    response.summary.hostname,
                    response.summary.source_name,
                    created_at,
                    response.summary.fail_count,
                    response.summary.pass_count,
                    response.summary.total_controls,
                    result_json,
                ),
            )
            conn.commit()
        return audit_id

    def list_audits(
        self,
        vendor: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Return lightweight audit list items (no full JSON)."""
        query = (
            "SELECT id, vendor, hostname, source_name, created_at, "
            "fail_count, pass_count, total FROM audits WHERE 1=1"
        )
        params: list = []
        if vendor:
            query += " AND vendor = ?"
            params.append(vendor)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with get_audit_db(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def count_audits(self, vendor: str | None = None) -> int:
        """Return total number of audits (with optional vendor filter)."""
        query = "SELECT COUNT(*) as n FROM audits WHERE 1=1"
        params: list = []
        if vendor:
            query += " AND vendor = ?"
            params.append(vendor)
        with get_audit_db(self.db_path) as conn:
            row = conn.execute(query, params).fetchone()
            return row["n"]

    def get_audit(self, audit_id: str) -> AuditResponse | None:
        """Return full AuditResponse for a given ID, or None."""
        with get_audit_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT result_json FROM audits WHERE id = ?", (audit_id,)
            ).fetchone()
            if not row:
                return None
            try:
                return AuditResponse.model_validate_json(row["result_json"])
            except Exception:
                data = json.loads(row["result_json"])
                if isinstance(data, dict):
                    for res in data.get("results", []):
                        if isinstance(res, dict):
                            for ev in res.get("evidence", []):
                                if isinstance(ev, dict) and ("note" not in ev or ev["note"] is None):
                                    ev["note"] = ""
                return AuditResponse.model_validate(data)

    def device_summary(self) -> list[dict]:
        """Return per-device (source_name or hostname) aggregate statistics."""
        with get_audit_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT
                    COALESCE(source_name, hostname, 'unknown') AS device,
                    vendor,
                    COUNT(*)           AS audit_count,
                    MAX(created_at)    AS last_audit,
                    SUM(fail_count)    AS total_fails,
                    SUM(pass_count)    AS total_passes,
                    SUM(total)         AS total_controls
                FROM audits
                GROUP BY COALESCE(source_name, hostname, 'unknown'), vendor
                ORDER BY last_audit DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def get_audit_trends(self, limit: int = 30) -> list[dict]:
        """Return historical trend timeline of audit results."""
        with get_audit_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, vendor, COALESCE(source_name, hostname, 'unknown') as device,
                       created_at, fail_count, pass_count, total
                FROM audits
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_device_history(self, device_id: str, limit: int = 50) -> list[dict]:
        """Return full audit history timeline for a specific device identifier."""
        with get_audit_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, vendor, hostname, source_name, created_at,
                       fail_count, pass_count, total
                FROM audits
                WHERE COALESCE(source_name, hostname, 'unknown') = ?
                   OR hostname = ?
                   OR source_name = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (device_id, device_id, device_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]

