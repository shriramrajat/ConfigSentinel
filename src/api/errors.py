"""
api.errors
~~~~~~~~~~

Centralised error codes, exception classes, and FastAPI exception handlers.

Error contract
--------------
Every error response sent to the client has this shape:

    {
      "error": {
        "code": "<ERROR_CODE>",
        "message": "<human-readable, safe for client rendering>"
      }
    }

HTTP status mapping
-------------------
400 INVALID_INPUT        — Structurally malformed request body.
422 VALIDATION_ERROR     — Request body parsed but failed field-level validation.
500 INTERNAL_ERROR       — Unexpected backend fault (safe message, no traceback).

Design rules
------------
- No Python tracebacks reach the client.
- No local filesystem paths reach the client.
- No internal exception type names reach the client.
- The 'message' field must be safe to render in a browser or mobile app.
"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Error code constants
# ---------------------------------------------------------------------------

CODE_INVALID_INPUT = "INVALID_INPUT"
CODE_VALIDATION_ERROR = "VALIDATION_ERROR"
CODE_INTERNAL_ERROR = "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# Internal domain exceptions (raised inside service.py, caught by handlers)
# ---------------------------------------------------------------------------


class ConfigSentinelError(Exception):
    """Base for all application-level errors."""


class InvalidInputError(ConfigSentinelError):
    """Raised when configuration text is empty, unreadable, or otherwise unusable."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# Response builder helpers
# ---------------------------------------------------------------------------


def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# (register these on the FastAPI application instance in main.py)
# ---------------------------------------------------------------------------


async def handle_invalid_input(request: Request, exc: InvalidInputError) -> JSONResponse:
    """Convert InvalidInputError → 400 INVALID_INPUT."""
    return JSONResponse(
        status_code=400,
        content=_error_body(CODE_INVALID_INPUT, exc.message),
    )


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic validation errors → 422 VALIDATION_ERROR.

    The raw Pydantic error details are collapsed into a single safe message
    so that internal field names and schema details are not exposed verbatim.
    A sanitised summary is included to help the client understand what went wrong.
    """
    # Build a concise summary without leaking internal paths.
    errors = exc.errors()
    if errors:
        first = errors[0]
        loc = " → ".join(str(p) for p in first.get("loc", []) if p != "body")
        msg = f"Field '{loc}': {first.get('msg', 'invalid value')}." if loc else first.get("msg", "Invalid request.")
    else:
        msg = "Request validation failed."

    return JSONResponse(
        status_code=422,
        content=_error_body(CODE_VALIDATION_ERROR, msg),
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions → 500 INTERNAL_ERROR.

    Logs the full traceback server-side.  Sends a safe, generic message
    to the client — no tracebacks, no internal state.
    """
    logger.exception("Unhandled exception during request %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=_error_body(
            CODE_INTERNAL_ERROR,
            "An unexpected error occurred. Please retry or contact support.",
        ),
    )
