"""
mapping.service
~~~~~~~~~~~~~~~

Orchestration layer for the AI Semantic Mapping lifecycle.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from src.mapping.ai_provider import AIMapper
from src.mapping.db import get_db, init_db
from src.mapping.model import (
    HumanApprovalState,
    PatternStatus,
    SemanticMapping,
    UnknownPattern,
)
from src.mapping.errors import ProviderNotConfiguredError


class SemanticMappingService:
    """Service to manage unknown patterns and their semantic mappings using SQLite."""

    def __init__(self, db_path: str, ai_mapper: AIMapper | None = None) -> None:
        self.db_path = db_path
        self.ai_mapper = ai_mapper
        init_db(self.db_path)

    def add_unknown_pattern(self, pattern: UnknownPattern) -> UnknownPattern:
        """Register a new unknown pattern in SQLite."""
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO unknown_patterns
                (id, vendor, raw_directive, source_name, section_context, status, first_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pattern.id,
                    pattern.vendor,
                    pattern.raw_directive,
                    pattern.source_name,
                    pattern.section_context,
                    pattern.status.value,
                    pattern.first_seen.isoformat()
                )
            )
            conn.commit()
        return pattern

    def get_unknown_pattern(self, pattern_id: str) -> UnknownPattern | None:
        """Retrieve an unknown pattern by ID."""
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM unknown_patterns WHERE id = ?", (pattern_id,)).fetchone()
            if not row:
                return None
            return UnknownPattern(
                id=row["id"],
                vendor=row["vendor"],
                raw_directive=row["raw_directive"],
                source_name=row["source_name"],
                section_context=row["section_context"],
                status=PatternStatus(row["status"]),
                first_seen=datetime.fromisoformat(row["first_seen"])
            )

    def propose_mapping(self, pattern_id: str) -> SemanticMapping:
        """Request an AI mapping proposal for an unknown pattern.

        Security Constraint
        -------------------
        The proposed mapping is ALWAYS forced to a PENDING state, regardless
        of what the AI provider returns. AI is never trusted directly.
        """
        if not self.ai_mapper:
            raise ProviderNotConfiguredError("AI Integration is not configured.")

        pattern = self.get_unknown_pattern(pattern_id)
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found.")

        with get_db(self.db_path) as conn:
            # Check for existing pending mapping
            row = conn.execute(
                "SELECT * FROM semantic_mappings WHERE pattern_id = ? AND approval_state = ?",
                (pattern_id, HumanApprovalState.PENDING.value)
            ).fetchone()

            if row:
                return self._row_to_mapping(row)

        # Get AI proposal
        mapping = self.ai_mapper.propose_mapping(pattern)

        # --- CRITICAL BOUNDARY ENFORCEMENT ---
        mapping.approval_state = HumanApprovalState.PENDING

        # Persist mapping proposal
        try:
            with get_db(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO semantic_mappings
                    (id, pattern_id, original_syntax, proposed_key, proposed_value,
                     confidence, explanation, approval_state, semantic_category,
                     mapping_version, usage_count, last_used_at, approved_by,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        mapping.id,
                        mapping.pattern_id,
                        mapping.original_syntax,
                        mapping.proposed_key,
                        mapping.proposed_value,
                        mapping.confidence,
                        mapping.explanation,
                        mapping.approval_state.value,
                        mapping.semantic_category.value if hasattr(mapping.semantic_category, 'value') else str(mapping.semantic_category),
                        mapping.mapping_version,
                        mapping.usage_count,
                        mapping.last_used_at.isoformat() if mapping.last_used_at else None,
                        mapping.approved_by,
                        mapping.created_at.isoformat(),
                        mapping.updated_at.isoformat(),
                    )
                )
                conn.commit()
        except sqlite3.IntegrityError:
            # Race condition: another pending mapping was inserted for this pattern
            with get_db(self.db_path) as conn:
                row = conn.execute(
                    "SELECT * FROM semantic_mappings WHERE pattern_id = ? AND approval_state = ?",
                    (pattern_id, HumanApprovalState.PENDING.value)
                ).fetchone()
                if row:
                    return self._row_to_mapping(row)
                raise  # Unlikely, but re-raise if it wasn't a duplicate pending

        return mapping

    def _row_to_mapping(self, row: sqlite3.Row) -> SemanticMapping:
        from src.mapping.model import SemanticCategory
        raw_cat = row["semantic_category"] if "semantic_category" in row.keys() and row["semantic_category"] else "OTHER"
        try:
            cat = SemanticCategory(raw_cat)
        except ValueError:
            cat = SemanticCategory.OTHER

        last_used = datetime.fromisoformat(row["last_used_at"]) if "last_used_at" in row.keys() and row["last_used_at"] else None

        return SemanticMapping(
            id=row["id"],
            pattern_id=row["pattern_id"],
            original_syntax=row["original_syntax"],
            proposed_key=row["proposed_key"],
            proposed_value=row["proposed_value"],
            confidence=row["confidence"],
            explanation=row["explanation"],
            approval_state=HumanApprovalState(row["approval_state"]),
            semantic_category=cat,
            mapping_version=row["mapping_version"] if "mapping_version" in row.keys() and row["mapping_version"] is not None else 1,
            usage_count=row["usage_count"] if "usage_count" in row.keys() and row["usage_count"] is not None else 0,
            last_used_at=last_used,
            approved_by=row["approved_by"] if "approved_by" in row.keys() else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


    def get_pending_mappings(self) -> list[SemanticMapping]:
        """Retrieve all mappings waiting for human approval."""
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM semantic_mappings WHERE approval_state = ?",
                (HumanApprovalState.PENDING.value,)
            ).fetchall()
            return [self._row_to_mapping(row) for row in rows]

    def get_mapping(self, mapping_id: str) -> SemanticMapping | None:
        """Retrieve a specific mapping by ID."""
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM semantic_mappings WHERE id = ?", (mapping_id,)).fetchone()
            if not row:
                return None
            return self._row_to_mapping(row)

    def record_mapping_usage(self, mapping_id: str) -> None:
        """Increment usage_count and set last_used_at for a mapping."""
        now_str = datetime.now(timezone.utc).isoformat()
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                UPDATE semantic_mappings
                SET usage_count = usage_count + 1, last_used_at = ?
                WHERE id = ?
                """,
                (now_str, mapping_id)
            )
            conn.commit()

    def get_approved_mappings(self, vendor: str) -> list[SemanticMapping]:
        """Retrieve all approved semantic mappings for a vendor."""
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT sm.*
                FROM semantic_mappings sm
                JOIN unknown_patterns up ON sm.pattern_id = up.id
                WHERE sm.approval_state = ? AND (up.vendor = ? OR up.vendor = 'ANY')
                """,
                (HumanApprovalState.APPROVED.value, vendor)
            ).fetchall()
            return [self._row_to_mapping(row) for row in rows]


    def get_known_raw_directives(self, vendor: str) -> set[str]:
        """Retrieve raw directives already recorded in unknown_patterns for a vendor."""
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                "SELECT raw_directive FROM unknown_patterns WHERE vendor = ?",
                (vendor,)
            ).fetchall()
            return {r["raw_directive"] for r in rows}

    def _build_patterns_query(self, vendor: str | None = None, status: str | None = None) -> tuple[str, list]:
        query = " FROM unknown_patterns WHERE 1=1"
        params = []
        if vendor:
            query += " AND vendor = ?"
            params.append(vendor)
        if status:
            query += " AND status = ?"
            params.append(status)
        return query, params

    def count_unknown_patterns(self, vendor: str | None = None, status: str | None = None) -> int:
        """Count unknown patterns matching the filters."""
        query_base, params = self._build_patterns_query(vendor, status)
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) as count" + query_base, params).fetchone()
            return row["count"]

    def get_unknown_patterns(
        self,
        vendor: str | None = None,
        status: str | None = None,
        sort_by: str = "first_seen",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0
    ) -> list[UnknownPattern]:
        """Retrieve unknown patterns with filtering, deterministic sorting, and pagination."""
        # Whitelist safe sort fields
        safe_sort_fields = {"first_seen", "vendor", "status"}
        if sort_by not in safe_sort_fields:
            sort_by = "first_seen"

        safe_sort_dirs = {"asc", "desc"}
        if sort_dir.lower() not in safe_sort_dirs:
            sort_dir = "desc"

        query_base, params = self._build_patterns_query(vendor, status)

        # We can safely interpolate sort_by and sort_dir since they are strictly validated against whitelists
        query = f"SELECT *{query_base} ORDER BY {sort_by} {sort_dir} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with get_db(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()

            patterns = []
            for row in rows:
                patterns.append(UnknownPattern(
                    id=row["id"],
                    vendor=row["vendor"],
                    raw_directive=row["raw_directive"],
                    source_name=row["source_name"],
                    section_context=row["section_context"],
                    status=PatternStatus(row["status"]),
                    first_seen=datetime.fromisoformat(row["first_seen"])
                ))
            return patterns

    def add_unknown_patterns_batch(self, patterns: list[UnknownPattern]) -> None:
        """Batch insert unknown patterns ignoring duplicates."""
        if not patterns:
            return

        with get_db(self.db_path) as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO unknown_patterns
                (id, vendor, raw_directive, source_name, section_context, status, first_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        p.id, p.vendor, p.raw_directive, p.source_name,
                        p.section_context, p.status.value, p.first_seen.isoformat()
                    )
                    for p in patterns
                ]
            )
            conn.commit()

    def approve_mapping(self, mapping_id: str) -> SemanticMapping:
        """Human approval of a proposed mapping."""
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM semantic_mappings WHERE id = ?", (mapping_id,)).fetchone()
            if not row:
                raise ValueError(f"Mapping {mapping_id} not found.")

            current_state = HumanApprovalState(row["approval_state"])
            if current_state != HumanApprovalState.PENDING:
                raise ValueError(f"Cannot approve mapping in state: {current_state.name}")

            conn.execute(
                "UPDATE semantic_mappings SET approval_state = ?, updated_at = ? WHERE id = ?",
                (HumanApprovalState.APPROVED.value, datetime.now(timezone.utc).isoformat(), mapping_id)
            )
            conn.execute(
                "UPDATE unknown_patterns SET status = ? WHERE id = ?",
                (PatternStatus.MAPPED.value, row["pattern_id"])
            )
            conn.commit()

        return self.get_mapping(mapping_id)

    def reject_mapping(self, mapping_id: str) -> SemanticMapping:
        """Human rejection of a proposed mapping."""
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM semantic_mappings WHERE id = ?", (mapping_id,)).fetchone()
            if not row:
                raise ValueError(f"Mapping {mapping_id} not found.")

            current_state = HumanApprovalState(row["approval_state"])
            if current_state != HumanApprovalState.PENDING:
                raise ValueError(f"Cannot reject mapping in state: {current_state.name}")

            conn.execute(
                "UPDATE semantic_mappings SET approval_state = ?, updated_at = ? WHERE id = ?",
                (HumanApprovalState.REJECTED.value, datetime.now(timezone.utc).isoformat(), mapping_id)
            )
            conn.execute(
                "UPDATE unknown_patterns SET status = ? WHERE id = ?",
                (PatternStatus.REJECTED.value, row["pattern_id"])
            )
            conn.commit()

        return self.get_mapping(mapping_id)

    def get_mapping_stats(self) -> dict:
        """Return aggregate statistics about unknown patterns and learned semantic mappings."""
        with get_db(self.db_path) as conn:
            total_patterns = conn.execute("SELECT COUNT(*) as c FROM unknown_patterns").fetchone()["c"]
            pending_patterns = conn.execute("SELECT COUNT(*) as c FROM unknown_patterns WHERE status = 'pending'").fetchone()["c"]
            mapped_patterns = conn.execute("SELECT COUNT(*) as c FROM unknown_patterns WHERE status = 'mapped'").fetchone()["c"]
            rejected_patterns = conn.execute("SELECT COUNT(*) as c FROM unknown_patterns WHERE status = 'rejected'").fetchone()["c"]

            total_mappings = conn.execute("SELECT COUNT(*) as c FROM semantic_mappings").fetchone()["c"]
            approved_mappings = conn.execute("SELECT COUNT(*) as c FROM semantic_mappings WHERE approval_state = 'approved'").fetchone()["c"]
            total_usage = conn.execute("SELECT COALESCE(SUM(usage_count), 0) as s FROM semantic_mappings").fetchone()["s"]

            # Vendor distribution
            vendor_rows = conn.execute("SELECT vendor, COUNT(*) as cnt FROM unknown_patterns GROUP BY vendor").fetchall()
            by_vendor = {r["vendor"]: r["cnt"] for r in vendor_rows}

            # Category distribution
            cat_rows = conn.execute("SELECT semantic_category, COUNT(*) as cnt FROM semantic_mappings WHERE approval_state = 'approved' GROUP BY semantic_category").fetchall()
            by_category = {r["semantic_category"]: r["cnt"] for r in cat_rows}

            approval_rate = (approved_mappings / total_mappings) if total_mappings > 0 else 0.0

            return {
                "total_patterns": total_patterns,
                "pending_patterns": pending_patterns,
                "mapped_patterns": mapped_patterns,
                "rejected_patterns": rejected_patterns,
                "total_mappings": total_mappings,
                "approved_mappings": approved_mappings,
                "approval_rate": round(approval_rate, 4),
                "total_mapping_reuse": total_usage,
                "patterns_by_vendor": by_vendor,
                "approved_by_category": by_category,
            }

    def get_mapping_usage(self, limit: int = 20) -> list[dict]:
        """Return the most frequently reused semantic mappings."""
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT sm.id, sm.original_syntax, sm.proposed_key, sm.proposed_value,
                       sm.semantic_category, sm.confidence, sm.usage_count, sm.last_used_at, up.vendor
                FROM semantic_mappings sm
                JOIN unknown_patterns up ON sm.pattern_id = up.id
                WHERE sm.approval_state = 'approved' AND sm.usage_count > 0
                ORDER BY sm.usage_count DESC, sm.last_used_at DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

