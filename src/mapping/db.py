"""
mapping.db
~~~~~~~~~~

SQLite schema and connection management for the Semantic Mapping domain.
"""

import sqlite3
import contextlib


def init_db(db_path: str) -> None:
    """Initialize the SQLite database with the required schema and migrations."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        # Create unknown_patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unknown_patterns (
                id TEXT PRIMARY KEY,
                vendor TEXT NOT NULL,
                raw_directive TEXT NOT NULL,
                source_name TEXT,
                section_context TEXT,
                status TEXT NOT NULL,
                first_seen TEXT NOT NULL
            )
        """)
        
        # Create semantic_mappings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_mappings (
                id TEXT PRIMARY KEY,
                pattern_id TEXT NOT NULL,
                original_syntax TEXT NOT NULL,
                proposed_key TEXT NOT NULL,
                proposed_value TEXT,
                confidence REAL NOT NULL,
                explanation TEXT NOT NULL,
                approval_state TEXT NOT NULL,
                semantic_category TEXT DEFAULT 'OTHER',
                mapping_version INTEGER DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                last_used_at TEXT,
                approved_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (pattern_id) REFERENCES unknown_patterns (id)
            )
        """)
        
        # Run defensive column migrations for existing databases
        cursor.execute("PRAGMA table_info(semantic_mappings)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        
        if "semantic_category" not in existing_cols:
            cursor.execute("ALTER TABLE semantic_mappings ADD COLUMN semantic_category TEXT DEFAULT 'OTHER'")
        if "mapping_version" not in existing_cols:
            cursor.execute("ALTER TABLE semantic_mappings ADD COLUMN mapping_version INTEGER DEFAULT 1")
        if "usage_count" not in existing_cols:
            cursor.execute("ALTER TABLE semantic_mappings ADD COLUMN usage_count INTEGER DEFAULT 0")
        if "last_used_at" not in existing_cols:
            cursor.execute("ALTER TABLE semantic_mappings ADD COLUMN last_used_at TEXT")
        if "approved_by" not in existing_cols:
            cursor.execute("ALTER TABLE semantic_mappings ADD COLUMN approved_by TEXT")

        # Create partial unique index to prevent duplicate pending mappings
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_pending_mapping
            ON semantic_mappings(pattern_id)
            WHERE approval_state = 'pending'
        """)
        
        # Indexes for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_semantic_mappings_approval_state
            ON semantic_mappings(approval_state)
        """)
        
        conn.commit()


@contextlib.contextmanager
def get_db(db_path: str):
    """Context manager for SQLite connections with enforced foreign keys."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()
