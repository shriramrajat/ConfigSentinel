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
    UnknownPatternSchema,
    PaginatedUnknownPatternSchema,
)
from src.mapping.service import SemanticMappingService
from src.mapping.llm_provider import LLMMapper
from src.mapping.errors import LLMIntegrationError, ProviderNotConfiguredError

import os
from pathlib import Path

router = APIRouter(prefix="/api/v1/mappings", tags=["Mapping"])

# In-memory or local file service instance for structural proof-of-concept.
# A real implementation would inject this via Depends().
DEFAULT_PATH = str(Path(__file__).parent.parent.parent / "mappings.db")
DB_PATH = os.getenv("MAPPINGS_DB_PATH", DEFAULT_PATH)

ai_api_key = os.getenv("AI_API_KEY")
if ai_api_key:
    _ai_mapper = LLMMapper(
        api_key=ai_api_key,
        model=os.getenv("AI_MODEL", "gpt-4o"),
        base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    )
else:
    _ai_mapper = None

_service = SemanticMappingService(db_path=DB_PATH, ai_mapper=_ai_mapper)


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


def _convert_unknown_pattern(pattern) -> UnknownPatternSchema:
    return UnknownPatternSchema(
        id=pattern.id,
        vendor=pattern.vendor,
        raw_directive=pattern.raw_directive,
        source_name=pattern.source_name,
        section_context=pattern.section_context,
        status=pattern.status.value,
        first_seen=pattern.first_seen,
    )


@router.post("/propose", response_model=SemanticMappingSchema)
def propose_mapping(request: ProposeMappingRequest) -> SemanticMappingSchema:
    """Request the AI to propose a semantic mapping for an unknown pattern.

    The resulting mapping will ALWAYS be forced into a PENDING state.
    """
    try:
        mapping = _service.propose_mapping(request.pattern_id)
        return _convert_mapping(mapping)
    except ProviderNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMIntegrationError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/pending", response_model=list[SemanticMappingSchema])
def get_pending_mappings() -> list[SemanticMappingSchema]:
    """Retrieve all mappings waiting for human approval."""
    mappings = _service.get_pending_mappings()
    return [_convert_mapping(m) for m in mappings]


@router.get("/discovered", response_model=PaginatedUnknownPatternSchema)
def get_discovered_patterns(
    vendor: str | None = None,
    status: str | None = None,
    sort_by: str = "first_seen",
    sort_dir: str = "desc",
    limit: int = 100,
    offset: int = 0
) -> PaginatedUnknownPatternSchema:
    """Retrieve discovered unknown configuration directives with pagination and filtering."""
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be non-negative")

    total = _service.count_unknown_patterns(vendor, status)
    patterns = _service.get_unknown_patterns(vendor, status, sort_by, sort_dir, limit, offset)

    return PaginatedUnknownPatternSchema(
        items=[_convert_unknown_pattern(p) for p in patterns],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/discovered/{pattern_id}", response_model=UnknownPatternSchema)
def get_discovered_pattern(pattern_id: str) -> UnknownPatternSchema:
    """Retrieve a specific discovered unknown configuration directive."""
    pattern = _service.get_unknown_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found.")
    return _convert_unknown_pattern(pattern)


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
