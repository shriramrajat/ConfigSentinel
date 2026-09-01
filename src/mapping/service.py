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
            raise ValueError("No AIMapper configured.")
            
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
                     confidence, explanation, approval_state, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        mapping.created_at.isoformat(),
                        mapping.updated_at.isoformat()
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
        return SemanticMapping(
            id=row["id"],
            pattern_id=row["pattern_id"],
            original_syntax=row["original_syntax"],
            proposed_key=row["proposed_key"],
            proposed_value=row["proposed_value"],
            confidence=row["confidence"],
            explanation=row["explanation"],
            approval_state=HumanApprovalState(row["approval_state"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
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
        
    def approve_mapping(self, mapping_id: str) -> SemanticMapping:
        """Human approval of a proposed mapping.
        
        Only after this step can the mapping be utilized by the
        deterministic compliance engine in future scans.
        """
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM semantic_mappings WHERE id = ?", (mapping_id,)).fetchone()
            if not row:
                raise ValueError(f"Mapping {mapping_id} not found.")
                
            current_state = HumanApprovalState(row["approval_state"])
            if current_state != HumanApprovalState.PENDING:
                raise ValueError(f"Cannot approve mapping in state: {current_state.name}")
                
            # Transactionally update mapping and pattern
            conn.execute(
                "UPDATE semantic_mappings SET approval_state = ?, updated_at = ? WHERE id = ?",
                (HumanApprovalState.APPROVED.value, datetime.now(timezone.utc).isoformat(), mapping_id)
            )
            conn.execute(
                "UPDATE unknown_patterns SET status = ? WHERE id = ?",
                (PatternStatus.MAPPED.value, row["pattern_id"])
            )
            conn.commit()
            
        # Return updated mapping
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
                
            # Transactionally update mapping and pattern
            conn.execute(
                "UPDATE semantic_mappings SET approval_state = ?, updated_at = ? WHERE id = ?",
                (HumanApprovalState.REJECTED.value, datetime.now(timezone.utc).isoformat(), mapping_id)
            )
            conn.execute(
                "UPDATE unknown_patterns SET status = ? WHERE id = ?",
                (PatternStatus.REJECTED.value, row["pattern_id"])
            )
            conn.commit()
            
        # Return updated mapping
        return self.get_mapping(mapping_id)
