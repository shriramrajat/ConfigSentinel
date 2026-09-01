"""
api.mapping_routes
~~~~~~~~~~~~~~~~~~

FastAPI routes for the AI Semantic Mapping workflow.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.mapping_schemas import (
    ApproveMappingRequest,
    ProposeMappingRequest,
    RejectMappingRequest,
    SemanticMappingSchema,
)
from src.mapping.service import SemanticMappingService
from src.mapping.ai_provider import AIMapper

import os
from pathlib import Path

router = APIRouter(prefix="/api/v1/mappings", tags=["Mapping"])

# In-memory or local file service instance for structural proof-of-concept.
# A real implementation would inject this via Depends().
DEFAULT_PATH = str(Path(__file__).parent.parent.parent / "mappings.db")
DB_PATH = os.getenv("MAPPINGS_DB_PATH", DEFAULT_PATH)
_service = SemanticMappingService(db_path=DB_PATH, ai_mapper=AIMapper())


def _convert_mapping(mapping) -> SemanticMappingSchema:
    return SemanticMappingSchema(
        id=mapping.id,
        pattern_id=mapping.pattern_id,
        original_syntax=mapping.original_syntax,
        proposed_key=mapping.proposed_key,
        proposed_value=mapping.proposed_value,
        explanation=mapping.explanation,
        confidence=mapping.confidence,
        approval_state=mapping.approval_state.value,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )


@router.post("/propose", response_model=SemanticMappingSchema)
def propose_mapping(request: ProposeMappingRequest) -> SemanticMappingSchema:
    """Request the AI to propose a semantic mapping for an unknown pattern.
    
    The resulting mapping will ALWAYS be forced into a PENDING state.
    """
    try:
        mapping = _service.propose_mapping(request.pattern_id)
        return _convert_mapping(mapping)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/pending", response_model=list[SemanticMappingSchema])
def get_pending_mappings() -> list[SemanticMappingSchema]:
    """Retrieve all mappings waiting for human approval."""
    mappings = _service.get_pending_mappings()
    return [_convert_mapping(m) for m in mappings]


@router.post("/{mapping_id}/approve", response_model=SemanticMappingSchema)
def approve_mapping(mapping_id: str, request: ApproveMappingRequest) -> SemanticMappingSchema:
    """Human approval of a proposed mapping."""
    try:
        mapping = _service.approve_mapping(mapping_id)
        return _convert_mapping(mapping)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{mapping_id}/reject", response_model=SemanticMappingSchema)
def reject_mapping(mapping_id: str, request: RejectMappingRequest) -> SemanticMappingSchema:
    """Human rejection of a proposed mapping."""
    try:
        mapping = _service.reject_mapping(mapping_id)
        return _convert_mapping(mapping)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
