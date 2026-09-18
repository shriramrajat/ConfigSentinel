"""
audit_store.db — SQLite persistence for audit results.

Schema
------
audits
  id           TEXT PRIMARY KEY   -- UUID
  vendor       TEXT               -- detected vendor
  hostname     TEXT               -- from config or null
  source_name  TEXT               -- from request or null
  created_at   TEXT               -- ISO-8601 UTC
  fail_count   INTEGER            -- denormalized for fast queries
  pass_count   INTEGER
  total        INTEGER
  result_json  TEXT               -- full AuditResponse JSON blob
"""

from __future__ import annotations

import contextlib
import sqlite3


def get_audit_db(db_path: str) -> contextlib.AbstractContextManager[sqlite3.Connection]:
    """Return a context manager yielding a connected SQLite connection."""

    @contextlib.contextmanager
    def _connect():
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    return _connect()


def init_audit_db(db_path: str) -> None:
    """Create the audits table if it does not already exist."""
    with get_audit_db(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audits (
                id          TEXT PRIMARY KEY,
                vendor      TEXT NOT NULL,
                hostname    TEXT,
                source_name TEXT,
                created_at  TEXT NOT NULL,
                fail_count  INTEGER NOT NULL DEFAULT 0,
                pass_count  INTEGER NOT NULL DEFAULT 0,
                total       INTEGER NOT NULL DEFAULT 0,
                result_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audits_created ON audits (created_at DESC)"
        )
        conn.commit()
