"""
api.config
~~~~~~~~~~

Minimal read-only configuration for the ConfigSentinel API.

Intentionally small.  Do not add speculative options.  Only extend this
when a concrete runtime requirement demands it.

Environment variables
---------------------
CONFIGSENTINEL_VERSION
    Override the reported version string.  Defaults to the value baked into
    this module.  Useful in CI or Docker image builds.

CONFIGSENTINEL_ALLOW_ORIGINS
    Comma-separated list of allowed CORS origins.
    Default: * (allow all, appropriate for development / internal deployment).
    Set a restrictive list in production.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

#: Semantic version for the ConfigSentinel API / backend.
#: Bump this when the API contract changes in a breaking way.
API_VERSION: str = os.getenv("CONFIGSENTINEL_VERSION", "0.1.0")

#: Human-readable product name.
PRODUCT_NAME: str = "ConfigSentinel"

#: Short description surfaced through /version and OpenAPI.
PRODUCT_DESCRIPTION: str = (
    "Deterministic network configuration security and compliance auditing. "
    "Supports Cisco IOS/IOS-XE and Juniper JunOS."
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

_raw_origins = os.getenv("CONFIGSENTINEL_ALLOW_ORIGINS", "*")
ALLOW_ORIGINS: list[str] = (
    ["*"] if _raw_origins.strip() == "*" else [o.strip() for o in _raw_origins.split(",")]
)
