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

    id: Annotated[str, Field(max_length=64)]
    vendor: Annotated[str, Field(max_length=32)]
    raw_directive: Annotated[str, Field(max_length=1024)]
    source_name: Annotated[str | None, Field(max_length=255)] = None
    section_context: Annotated[str | None, Field(max_length=512)] = None
    status: Annotated[str, Field(max_length=32)]
    first_seen: datetime


class PaginatedUnknownPatternSchema(BaseModel):
    """Schema for paginated discovery queue response."""

    items: list[UnknownPatternSchema]
    total: int
    limit: int
    offset: int


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
