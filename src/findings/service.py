"""
findings.service
~~~~~~~~~~~~~~~~

Service for persistent security finding lifecycle management.

Lifecycle States
----------------
OPEN          — Active non-compliant finding detected in audit.
ACKNOWLEDGED  — Explicitly reviewed and acknowledged by security operator.
RESOLVED      — Control passed in subsequent audit or marked resolved.
REOPENED      — Previously resolved finding failed again in a new audit.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from src.api.schemas import AuditResponse
from src.findings.db import get_findings_db, init_findings_db


class FindingService:
    """Manage persistent security findings across device audits."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        init_findings_db(db_path)

    def sync_audit_findings(
        self,
        audit_response: AuditResponse | None = None,
        audit_id: str | None = None,
        device_id: str | None = None,
        compliance_results: list | None = None,
    ) -> dict[str, int]:
        """Synchronize findings state after an audit completes."""
        if audit_response is not None:
            audit_id_str = audit_response.summary.id
            dev_id = audit_response.summary.source_name or audit_response.summary.hostname or "unknown"
            results_list = audit_response.results
        else:
            audit_id_str = audit_id or "unknown-audit"
            dev_id = device_id or "unknown"
            results_list = compliance_results or []

        now_str = datetime.now(timezone.utc).isoformat()
        stats = {"created": 0, "updated": 0, "resolved": 0, "reopened": 0}

        with get_findings_db(self.db_path) as conn:
            for result in results_list:
                c_id = getattr(result, "control_id", None) or result.get("control_id") if isinstance(result, dict) else result.control_id
                c_status = getattr(result, "status", None) or result.get("status") if isinstance(result, dict) else result.status
                if hasattr(c_status, "value"):
                    c_status_str = c_status.value.lower()
                else:
                    c_status_str = str(c_status).lower()

                c_sev = getattr(result, "severity", None) or result.get("severity") if isinstance(result, dict) else result.severity
                if hasattr(c_sev, "value"):
                    c_sev_str = c_sev.value.upper()
                else:
                    c_sev_str = str(c_sev).upper()

                fingerprint = hashlib.sha256(f"{dev_id}::{c_id}".encode("utf-8")).hexdigest()
                row = conn.execute("SELECT * FROM security_findings WHERE fingerprint = ?", (fingerprint,)).fetchone()

                if c_status_str == "fail":
                    ev_data = getattr(result, "evidence", [])
                    rem_data = getattr(result, "remediations", [])
                    ev_json = json.dumps([e.model_dump() if hasattr(e, "model_dump") else e for e in ev_data])
                    rem_json = json.dumps([r.model_dump() if hasattr(r, "model_dump") else r for r in rem_data])

                    if not row:
                        # New open finding
                        conn.execute(
                            """
                            INSERT INTO security_findings
                            (id, fingerprint, device_id, control_id, severity, status,
                             first_seen, last_seen, first_seen_audit_id, last_seen_audit_id,
                             occurrence_count, evidence_json, remediation_json)
                            VALUES (?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, 1, ?, ?)
                            """,
                            (
                                str(uuid.uuid4()),
                                fingerprint,
                                dev_id,
                                c_id,
                                c_sev_str,
                                now_str,
                                now_str,
                                audit_id_str,
                                audit_id_str,
                                ev_json,
                                rem_json,
                            ),
                        )
                        stats["created"] += 1
                    else:
                        was_resolved = row["status"] == "RESOLVED"
                        new_status = "OPEN" if was_resolved else row["status"]
                        new_count = row["occurrence_count"] + 1
                        conn.execute(
                            """
                            UPDATE security_findings
                            SET status = ?, last_seen = ?, last_seen_audit_id = ?, occurrence_count = ?,
                                severity = ?, evidence_json = ?, remediation_json = ?
                            WHERE id = ?
                            """,
                            (new_status, now_str, audit_id_str, new_count, c_sev_str, ev_json, rem_json, row["id"]),
                        )
                        if was_resolved:
                            stats["reopened"] += 1
                        else:
                            stats["updated"] += 1

                elif c_status_str == "pass" and row:
                    # Resolve existing open/acknowledged finding
                    if row["status"] in ("OPEN", "ACKNOWLEDGED"):
                        conn.execute(
                            """
                            UPDATE security_findings
                            SET status = 'RESOLVED', resolved_at = ?
                            WHERE id = ?
                            """,
                            (now_str, row["id"]),
                        )
                        stats["resolved"] += 1

            conn.commit()

        return stats

    def list_findings(
        self,
        device_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Query persistent findings with filters and pagination."""
        query = "SELECT * FROM security_findings WHERE 1=1"
        params: list = []

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)
        if status:
            query += " AND status = ?"
            params.append(status.upper())
        if severity:
            query += " AND severity = ?"
            params.append(severity.lower())

        query += " ORDER BY last_seen DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with get_findings_db(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def count_findings(
        self,
        device_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> int:
        """Count findings matching filters."""
        query = "SELECT COUNT(*) as count FROM security_findings WHERE 1=1"
        params: list = []

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)
        if status:
            query += " AND status = ?"
            params.append(status.upper())
        if severity:
            query += " AND severity = ?"
            params.append(severity.lower())

        with get_findings_db(self.db_path) as conn:
            row = conn.execute(query, params).fetchone()
            return row["count"]

    def get_finding(self, finding_id: str) -> dict | None:
        """Retrieve a specific finding by ID."""
        with get_findings_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM security_findings WHERE id = ?", (finding_id,)).fetchone()
            if not row:
                return None
            return dict(row)

    def acknowledge_finding(self, finding_id: str) -> dict:
        """Mark a finding as ACKNOWLEDGED by an operator."""
        now_str = datetime.now(timezone.utc).isoformat()
        with get_findings_db(self.db_path) as conn:
            conn.execute(
                "UPDATE security_findings SET status = 'ACKNOWLEDGED', acknowledged_at = ? WHERE id = ?",
                (now_str, finding_id),
            )
            conn.commit()
        res = self.get_finding(finding_id)
        if not res:
            raise ValueError(f"Finding '{finding_id}' not found.")
        return res

    def resolve_finding(self, finding_id: str) -> dict:
        """Manually resolve a finding."""
        now_str = datetime.now(timezone.utc).isoformat()
        with get_findings_db(self.db_path) as conn:
            conn.execute(
                "UPDATE security_findings SET status = 'RESOLVED', resolved_at = ? WHERE id = ?",
                (now_str, finding_id),
            )
            conn.commit()
        res = self.get_finding(finding_id)
        if not res:
            raise ValueError(f"Finding '{finding_id}' not found.")
        return res

    def reopen_finding(self, finding_id: str) -> dict:
        """Reopen a resolved finding."""
        with get_findings_db(self.db_path) as conn:
            conn.execute(
                "UPDATE security_findings SET status = 'OPEN', resolved_at = NULL WHERE id = ?",
                (finding_id,),
            )
            conn.commit()
        res = self.get_finding(finding_id)
        if not res:
            raise ValueError(f"Finding '{finding_id}' not found.")
        return res
