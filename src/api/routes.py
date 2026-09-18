"""
api.routes
~~~~~~~~~~

FastAPI route definitions for the ConfigSentinel API.

Endpoints
---------
GET  /health          — Liveness probe.
GET  /version         — Product version information.
POST /api/v1/audit    — Run a compliance audit on submitted configuration text.

Transport contract
------------------
- All business logic is delegated to ``api.service``.
- Routes must not contain parser or compliance logic.
- Response models are declared on every route for accurate OpenAPI generation.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.api.config import API_VERSION, PRODUCT_DESCRIPTION, PRODUCT_NAME
from src.api.schemas import AuditRequest, AuditResponse, BulkAuditRequest, BulkAuditResponse, ErrorResponse
from src.api.service import run_audit
from src.api.errors import InvalidInputError
from fastapi.responses import JSONResponse as _JSONResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 OK when the API is reachable. No business logic is invoked.",
    tags=["Meta"],
    responses={200: {"description": "Service is healthy."}},
)
def health() -> JSONResponse:
    """Simple liveness check for load balancers and monitoring systems."""
    return JSONResponse(content={"status": "ok"})


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


@router.get(
    "/version",
    summary="API version",
    description="Returns the product name, API version, and a short description.",
    tags=["Meta"],
    responses={200: {"description": "Version information."}},
)
def version() -> JSONResponse:
    """Return product and API version information."""
    return JSONResponse(
        content={
            "product": PRODUCT_NAME,
            "version": API_VERSION,
            "description": PRODUCT_DESCRIPTION,
        }
    )


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


@router.post(
    "/api/v1/audit",
    response_model=AuditResponse,
    summary="Run a compliance audit",
    description=(
        "Submit raw network device configuration text for deterministic "
        "multi-vendor compliance auditing.  "
        "The backend automatically detects the vendor (Cisco or Juniper) and "
        "evaluates all active controls.  "
        "Returns per-control results with evidence and remediation guidance."
    ),
    tags=["Audit"],
    responses={
        200: {"description": "Audit completed successfully.", "model": AuditResponse},
        400: {"description": "Configuration text is empty or unusable.", "model": ErrorResponse},
        422: {"description": "Request body failed schema validation.", "model": ErrorResponse},
        500: {"description": "Unexpected internal error.", "model": ErrorResponse},
    },
)
def audit_config(request: AuditRequest) -> AuditResponse:
    """Run the full compliance pipeline on the submitted configuration text.

    The pipeline is:
        config_text → detect_vendor → parse (Cisco|Juniper) → audit() → results

    All compliance logic is deterministic and vendor-neutral.
    The frontend must not duplicate any compliance decisions.
    """
    return run_audit(request)


# ---------------------------------------------------------------------------
# Bulk Audit
# ---------------------------------------------------------------------------


@router.post(
    "/api/v1/audits/bulk",
    response_model=BulkAuditResponse,
    summary="Bulk compliance audit",
    description=(
        "Submit multiple device configurations in a single request. "
        "Each item is audited independently. Partial failures do not abort the batch — "
        "failed items carry an 'error' field. The overall HTTP status is 200 if any item "
        "succeeds, even when some items fail."
    ),
    tags=["Audit"],
    responses={
        200: {"description": "Bulk audit completed (may include per-item errors).", "model": BulkAuditResponse},
        422: {"description": "Request body failed schema validation.", "model": ErrorResponse},
        500: {"description": "Unexpected internal error.", "model": ErrorResponse},
    },
)
def bulk_audit(request: BulkAuditRequest) -> BulkAuditResponse:
    """Run a compliance audit on each config in the batch.

    Items are processed sequentially.  Each item produces either an AuditResponse
    or an error message.  The batch response always returns HTTP 200; per-item
    failures are surfaced in the ``error`` field of the corresponding result item.
    """
    from src.api.schemas import BulkAuditResultItem
    results = []
    for item in request.configs:
        try:
            audit_resp = run_audit(AuditRequest(
                config_text=item.config_text,
                source_name=item.source_name,
            ))
            results.append(BulkAuditResultItem(
                source_name=item.source_name,
                status="ok",
                result=audit_resp,
                error=None,
            ))
        except InvalidInputError as exc:
            results.append(BulkAuditResultItem(
                source_name=item.source_name,
                status="error",
                result=None,
                error=str(exc),
            ))
        except Exception as exc:  # noqa: BLE001
            results.append(BulkAuditResultItem(
                source_name=item.source_name,
                status="error",
                result=None,
                error=f"Internal error: {type(exc).__name__}",
            ))
    return BulkAuditResponse(
        total=len(results),
        succeeded=sum(1 for r in results if r.status == "ok"),
        failed=sum(1 for r in results if r.status == "error"),
        results=results,
    )
