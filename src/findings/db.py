"""
findings.db
~~~~~~~~~~~

SQLite persistence and schema management for persistent Finding Lifecycle.
"""

from __future__ import annotations

import contextlib
import sqlite3


def init_findings_db(db_path: str) -> None:
    """Initialize security_findings and finding_events tables in SQLite."""
    with get_findings_db(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS security_findings (
                id TEXT PRIMARY KEY,
                fingerprint TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                control_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                first_seen_audit_id TEXT,
                last_seen_audit_id TEXT,
                occurrence_count INTEGER NOT NULL DEFAULT 1,
                resolved_at TEXT,
                acknowledged_at TEXT,
                evidence_json TEXT,
                remediation_json TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_findings_device_status
            ON security_findings(device_id, status)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_findings_status
            ON security_findings(status)
            """
        )

        table_info = cursor.execute("PRAGMA table_info(security_findings)").fetchall()
        cols = {row["name"] for row in table_info}
        if "first_seen_audit_id" not in cols:
            cursor.execute("ALTER TABLE security_findings ADD COLUMN first_seen_audit_id TEXT")
        if "last_seen_audit_id" not in cols:
            cursor.execute("ALTER TABLE security_findings ADD COLUMN last_seen_audit_id TEXT")

        conn.commit()


@contextlib.contextmanager
def get_findings_db(db_path: str):
    """Context manager for findings SQLite connection."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()
