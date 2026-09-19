"""
query.schema
~~~~~~~~~~~~

Strict Pydantic schema for bounded natural-language query translation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StructuredQuerySchema(BaseModel):
    """Strictly bounded query parameters. Extra fields or raw SQL strings are forbidden."""

    intent_id: str | None = Field(default=None, description="Security intent ID (e.g. 'TELNET_DISABLED')")
    control_id: str | None = Field(default=None, description="Control ID (e.g. 'TLN-001')")
    status: str | None = Field(default=None, description="Compliance status: 'PASS', 'FAIL', 'OPEN'")
    severity: str | None = Field(default=None, description="Severity tier: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'")
    vendor: str | None = Field(default=None, description="Vendor filter (e.g. 'cisco', 'juniper')")
    environment: str | None = Field(default=None, description="Environment tag (e.g. 'PRODUCTION', 'DMZ')")
    device_id: str | None = Field(default=None, description="Specific device ID or hostname")
    keyword: str | None = Field(default=None, description="Safe text keyword filter")

    model_config = {
        "extra": "forbid",
    }
