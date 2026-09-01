"""
api.mapping_schemas
~~~~~~~~~~~~~~~~~~~

Pydantic models for the mapping workflow API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class UnknownPatternSchema(BaseModel):
    """Schema representing an unrecognized configuration directive."""
    
    id: str
    vendor: str
    raw_directive: str
    source_name: str | None
    section_context: str | None
    status: str
    first_seen: datetime


class SemanticMappingSchema(BaseModel):
    """Schema representing an AI-proposed semantic mapping."""
    
    id: str
    pattern_id: str
    original_syntax: str
    proposed_key: str
    proposed_value: str | None
    explanation: str
    confidence: float
    approval_state: str
    created_at: datetime
    updated_at: datetime


class ProposeMappingRequest(BaseModel):
    """Request body for generating a mapping proposal."""
    
    pattern_id: Annotated[
        str,
        Field(description="ID of the unknown pattern to map."),
    ]


class ApproveMappingRequest(BaseModel):
    """Placeholder request body for future approval metadata if needed."""
    pass


class RejectMappingRequest(BaseModel):
    """Placeholder request body for future rejection metadata (e.g. reason)."""
    pass
