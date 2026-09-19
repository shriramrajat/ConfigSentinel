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

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse

from src.api.config import API_VERSION, PRODUCT_DESCRIPTION, PRODUCT_NAME
from src.api.schemas import AuditRequest, AuditResponse, BulkAuditRequest, BulkAuditResponse, ErrorResponse
from src.api.service import run_audit
from src.api.errors import InvalidInputError
from src.audit_store.service import AuditStoreService
from src.reporting.report_generator import generate_html_report
from pathlib import Path
import os

router = APIRouter()


def _get_audit_store() -> AuditStoreService:
    audit_db_path = os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))
    return AuditStoreService(db_path=audit_db_path)


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


# ---------------------------------------------------------------------------
# Audit History
# ---------------------------------------------------------------------------


@router.get(
    "/api/v1/audits",
    summary="List past audits",
    description="Returns a paginated list of past audits in reverse-chronological order.",
    tags=["History"],
)
def list_audits(
    vendor: str | None = Query(default=None, description="Filter by vendor."),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> JSONResponse:
    """Return lightweight audit list items for the history/dashboard view."""
    store = _get_audit_store()
    items = store.list_audits(vendor=vendor, limit=limit, offset=offset)
    total = store.count_audits(vendor=vendor)
    return JSONResponse(content={"total": total, "limit": limit, "offset": offset, "items": items})


@router.get(
    "/api/v1/audits/{audit_id}",
    summary="Get a past audit by ID",
    description="Returns the full AuditResponse for a past audit.",
    tags=["History"],
)
def get_audit(audit_id: str) -> JSONResponse:
    """Return the full audit result for a specific ID."""
    store = _get_audit_store()
    result = store.get_audit(audit_id)
    if result is None:
        return JSONResponse(status_code=404, content={"detail": f"Audit '{audit_id}' not found."})
    return JSONResponse(content=result.model_dump())


@router.get(
    "/api/v1/audits/trends",
    summary="Compliance & risk trend timeline",
    description="Returns historical compliance and risk trends across past audits.",
    tags=["History"],
)
def audit_trends(limit: int = Query(default=30, ge=1, le=200)) -> JSONResponse:
    """Return historical audit trend data."""
    store = _get_audit_store()
    trends = store.get_audit_trends(limit=limit)
    return JSONResponse(content={"trends": trends})


@router.get(
    "/api/v1/devices",
    summary="Device summary dashboard",
    description="Returns per-device aggregate statistics across all past audits.",
    tags=["Dashboard"],
)
def device_dashboard() -> JSONResponse:
    """Return per-device aggregate statistics for the dashboard."""
    store = _get_audit_store()
    devices = store.device_summary()
    return JSONResponse(content={"devices": devices})


@router.get(
    "/api/v1/devices/{device_id}/history",
    summary="Per-device historical audit timeline",
    description="Returns the historical audit log for a specific device.",
    tags=["Dashboard"],
)
def device_history(device_id: str, limit: int = Query(default=50, ge=1, le=200)) -> JSONResponse:
    """Return historical audit log for a device."""
    store = _get_audit_store()
    history = store.get_device_history(device_id=device_id, limit=limit)
    return JSONResponse(content={"device": device_id, "history": history})


@router.get(
    "/api/v1/devices/{device_id}/drift",
    summary="Configuration drift detection",
    description="Detect configuration drift between consecutive audits for a device.",
    tags=["Dashboard"],
)
def device_drift(device_id: str) -> JSONResponse:
    """Compute configuration drift between the last two audits of a device."""
    from src.drift.engine import compute_config_fingerprint, detect_config_drift
    from src.ingestion.detector import detect_vendor
    from src.parsers.cisco import parse_cisco
    from src.parsers.juniper import parse_juniper
    from src.parsers.arista import parse_arista
    from src.parsers.fortios import parse_fortios
    from src.parsers.panos import parse_panos

    store = _get_audit_store()
    history = store.get_device_history(device_id=device_id, limit=2)
    if len(history) < 2:
        return JSONResponse(content={"device": device_id, "drift": [], "message": "At least 2 audits required for drift calculation."})

    curr_audit = store.get_audit(history[0]["id"])
    prev_audit = store.get_audit(history[1]["id"])

    if not curr_audit or not prev_audit:
        return JSONResponse(content={"device": device_id, "drift": []})

    # Best-effort parse over evidence raw lines to reconstruct NormalizedConfig
    def _reconstruct_cfg(audit_resp, vendor_str):
        all_lines = []
        for r in audit_resp.results:
            for e in r.evidence:
                all_lines.extend(e.raw_lines)
        raw_text = "\n".join(all_lines) if all_lines else "hostname " + (audit_resp.summary.hostname or "device")
        if vendor_str == "juniper":
            return parse_juniper(raw_text)
        elif vendor_str == "arista":
            return parse_arista(raw_text)
        elif vendor_str == "fortinet":
            return parse_fortios(raw_text)
        elif vendor_str == "panos":
            return parse_panos(raw_text)
        return parse_cisco(raw_text)

    curr_cfg = _reconstruct_cfg(curr_audit, curr_audit.summary.vendor)
    prev_cfg = _reconstruct_cfg(prev_audit, prev_audit.summary.vendor)

    drift_items = detect_config_drift(prev_cfg, curr_cfg)
    return JSONResponse(content={
        "device": device_id,
        "previous_audit_id": history[1]["id"],
        "current_audit_id": history[0]["id"],
        "previous_fingerprint": compute_config_fingerprint(prev_cfg),
        "current_fingerprint": compute_config_fingerprint(curr_cfg),
        "drift_count": len(drift_items),
        "drift": [
            {
                "change_type": d.change_type,
                "key": d.key,
                "old_value": d.old_value,
                "new_value": d.new_value,
            }
            for d in drift_items
        ]
    })


@router.get(
    "/api/v1/devices/{device_id}/posture",
    summary="Security posture delta comparison",
    description="Compute posture change and security impact between consecutive audits.",
    tags=["Dashboard"],
)
def device_posture(device_id: str) -> JSONResponse:
    """Compute posture delta between last two audits of a device."""
    from src.drift.engine import compute_posture_delta
    from src.compliance.model import ComplianceResult, ComplianceStatus, Severity

    store = _get_audit_store()
    history = store.get_device_history(device_id=device_id, limit=2)
    if len(history) < 1:
        return JSONResponse(status_code=404, content={"detail": f"Device '{device_id}' has no audit records."})

    curr_audit = store.get_audit(history[0]["id"])
    if not curr_audit:
        return JSONResponse(status_code=404, content={"detail": f"Audit record missing."})

    def _convert_schema_results(schema_results):
        res = []
        for r in schema_results:
            status_enum = ComplianceStatus(r.status)
            sev_enum = Severity(r.severity)
            res.append(ComplianceResult(
                control_id=r.control_id,
                control_name=r.control_name,
                description=r.description,
                severity=sev_enum,
                status=status_enum,
                vendor=r.vendor,
                hostname=r.hostname,
            ))
        return res

    curr_res = _convert_schema_results(curr_audit.results)

    if len(history) < 2:
        delta = compute_posture_delta(None, curr_res, current_audit_id=history[0]["id"])
    else:
        prev_audit = store.get_audit(history[1]["id"])
        prev_res = _convert_schema_results(prev_audit.results) if prev_audit else None
        delta = compute_posture_delta(prev_res, curr_res, previous_audit_id=history[1]["id"], current_audit_id=history[0]["id"])

    return JSONResponse(content={
        "device": device_id,
        "previous_audit_id": delta.previous_audit_id,
        "current_audit_id": delta.current_audit_id,
        "security_impact": delta.security_impact.value,
        "new_failures": delta.new_failures,
        "resolved_failures": delta.resolved_failures,
        "previous_fail_count": delta.previous_fail_count,
        "current_fail_count": delta.current_fail_count,
        "previous_pass_count": delta.previous_pass_count,
        "current_pass_count": delta.current_pass_count,
    })


def _get_finding_service():
    from src.findings.service import FindingService
    audit_db_path = os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))
    return FindingService(db_path=audit_db_path)


# ---------------------------------------------------------------------------
# Finding Lifecycle API
# ---------------------------------------------------------------------------


@router.get(
    "/api/v1/findings",
    summary="List persistent security findings",
    description="Query persistent security findings across devices with filtering and pagination.",
    tags=["Findings"],
)
def list_findings(
    device_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> JSONResponse:
    """Return paginated security findings matching filters."""
    svc = _get_finding_service()
    items = svc.list_findings(device_id=device_id, status=status, severity=severity, limit=limit, offset=offset)
    total = svc.count_findings(device_id=device_id, status=status, severity=severity)
    return JSONResponse(content={"total": total, "limit": limit, "offset": offset, "findings": items})


@router.get(
    "/api/v1/findings/{finding_id}",
    summary="Get persistent security finding details",
    description="Returns detailed record for a specific security finding.",
    tags=["Findings"],
)
def get_finding(finding_id: str) -> JSONResponse:
    """Return finding detail by ID."""
    svc = _get_finding_service()
    item = svc.get_finding(finding_id)
    if not item:
        return JSONResponse(status_code=404, content={"detail": f"Finding '{finding_id}' not found."})
    return JSONResponse(content=item)


@router.post(
    "/api/v1/findings/{finding_id}/acknowledge",
    summary="Acknowledge security finding",
    description="Mark a security finding as ACKNOWLEDGED by an operator.",
    tags=["Findings"],
)
def acknowledge_finding(finding_id: str) -> JSONResponse:
    """Acknowledge finding."""
    svc = _get_finding_service()
    try:
        item = svc.acknowledge_finding(finding_id)
        return JSONResponse(content=item)
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})


@router.post(
    "/api/v1/findings/{finding_id}/resolve",
    summary="Resolve security finding",
    description="Mark a security finding as RESOLVED.",
    tags=["Findings"],
)
def resolve_finding(finding_id: str) -> JSONResponse:
    """Resolve finding."""
    svc = _get_finding_service()
    try:
        item = svc.resolve_finding(finding_id)
        return JSONResponse(content=item)
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})


@router.post(
    "/api/v1/findings/{finding_id}/reopen",
    summary="Reopen security finding",
    description="Reopen a previously resolved security finding.",
    tags=["Findings"],
)
def reopen_finding(finding_id: str) -> JSONResponse:
    """Reopen finding."""
    svc = _get_finding_service()
    try:
        item = svc.reopen_finding(finding_id)
        return JSONResponse(content=item)
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})






# ---------------------------------------------------------------------------
# PDF / HTML Executive Reports
# ---------------------------------------------------------------------------


from fastapi import APIRouter, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse
from src.reporting.pdf_generator import generate_pdf_report


@router.get(
    "/api/v1/reports/{audit_id}",
    summary="Generate executive PDF report for an audit",
    description="Returns a native binary PDF executive summary report.",
    tags=["Reports"],
)
def get_audit_report(audit_id: str) -> Response:
    """Return binary PDF report for an audit result."""
    store = _get_audit_store()
    result = store.get_audit(audit_id)
    if result is None:
        return JSONResponse(status_code=404, content={"detail": f"Audit '{audit_id}' not found."})
    pdf_bytes = generate_pdf_report(result, audit_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="audit-report-{audit_id}.pdf"'},
    )


@router.get(
    "/api/v1/reports/{audit_id}/html",
    summary="Generate HTML executive report for an audit",
    description="Returns a formatted HTML executive summary report.",
    tags=["Reports"],
    response_class=HTMLResponse,
)
def get_audit_report_html(audit_id: str) -> HTMLResponse:
    """Return HTML report for browser viewing."""
    store = _get_audit_store()
    result = store.get_audit(audit_id)
    if result is None:
        return HTMLResponse(status_code=404, content=f"<h1>404 Not Found</h1><p>Audit '{audit_id}' not found.</p>")
    html_content = generate_html_report(result, audit_id)
    return HTMLResponse(content=html_content)


