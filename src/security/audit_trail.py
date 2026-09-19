"""
security.audit_trail
~~~~~~~~~~~~~~~~~~~~

Persistent Audit Trail Logger for Security Operations.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from src.mapping.redaction import redact_secrets


def init_audit_trail_db(db_path: str) -> None:
    """Ensure audit_trail table exists in SQLite."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_trail (
                entry_id     TEXT PRIMARY KEY,
                actor        TEXT NOT NULL,
                timestamp    TEXT NOT NULL,
                operation    TEXT NOT NULL,
                device_id    TEXT,
                finding_id   TEXT,
                before_state TEXT,
                after_state  TEXT,
                result       TEXT NOT NULL DEFAULT 'SUCCESS'
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_trail_ts ON audit_trail (timestamp DESC)")
        conn.commit()
    finally:
        conn.close()


class AuditTrailService:
    """Logger for administrative security operations."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))
        self.db_path = db_path
        init_audit_trail_db(self.db_path)

    def log_action(
        self,
        actor: str,
        operation: str,
        device_id: str | None = None,
        finding_id: str | None = None,
        before_state: str | dict | None = None,
        after_state: str | dict | None = None,
        result: str = "SUCCESS",
    ) -> str:
        """Record an immutable audit log entry with secret redaction."""
        now = datetime.now(timezone.utc).isoformat()
        entry_id = f"log-{uuid.uuid4().hex[:8]}"

        b_str = json.dumps(before_state) if isinstance(before_state, dict) else (before_state or "")
        a_str = json.dumps(after_state) if isinstance(after_state, dict) else (after_state or "")

        # Redact any secrets before storing in audit trail
        b_clean = redact_secrets(b_str) if b_str else None
        a_clean = redact_secrets(a_str) if a_str else None

        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO audit_trail (
                    entry_id, actor, timestamp, operation, device_id, finding_id, before_state, after_state, result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (entry_id, actor, now, operation, device_id, finding_id, b_clean, a_clean, result),
            )
            conn.commit()
        finally:
            conn.close()

        return entry_id

    def get_recent_logs(self, limit: int = 50) -> list[dict]:
        """Fetch recent security operations logs."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM audit_trail ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
