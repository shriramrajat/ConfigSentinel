"""
api.phase3_routes
~~~~~~~~~~~~~~~~~

FastAPI API endpoints for Phase 3: Security Operations, Remediation & Fleet Intelligence.
"""

from __future__ import annotations

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from src.baselines.service import BaselineService
from src.export.service import OperationalExportService, WebhookService
from src.fleet.service import FleetPostureService
from src.inventory.service import DeviceInventoryService
from src.prioritization.service import FindingPrioritizationService
from src.query.engine import NaturalLanguageQueryEngine
from src.remediation.service import RemediationService
from src.scheduling.model import ScheduleInterval
from src.scheduling.service import AuditScheduleService
from src.security.audit_trail import AuditTrailService

router = APIRouter(tags=["Security Operations"])


def _get_db_path() -> str:
    return os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))


class DeviceCreateApiRequest(BaseModel):
    hostname: str = Field(..., description="Device hostname")
    vendor: str = Field(..., description="Device vendor (cisco, juniper, arista, fortinet, panos)")
    platform: str = Field(default="Unknown", description="Device platform")
    version: str = Field(default="Unknown", description="OS Version")
    environment: str = Field(default="PRODUCTION", description="Environment tag")
    location: str | None = Field(default=None, description="Location/Zone")
    owner: str | None = Field(default=None, description="Owner")
    tags: list[str] = Field(default_factory=list, description="Metadata tags")


class RemediationVerifyApiRequest(BaseModel):
    control_id: str = Field(..., description="Control ID")
    remediated_config_text: str = Field(..., description="Updated configuration text after remediation")
    vendor: str | None = Field(default=None, description="Optional vendor filter")


class BaselineCreateApiRequest(BaseModel):
    config_text: str = Field(..., description="Configuration text for the baseline")
    created_by: str = Field(default="secops_admin", description="Operator identity")
    vendor: str | None = Field(default=None, description="Optional vendor")


class ScheduleCreateApiRequest(BaseModel):
    device_id: str = Field(..., description="Target device ID")
    interval: str = Field(default="DAILY", description="HOURLY, DAILY, WEEKLY")


class QueryApiRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")


# --- 3.1 Device Inventory Endpoints ---

@router.get("/api/v1/inventory/devices", summary="List fleet device inventory")
def list_fleet_devices(
    vendor: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    posture: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> JSONResponse:
    svc = DeviceInventoryService(_get_db_path())
    devices = svc.list_devices(vendor=vendor, environment=environment, posture=posture, search=search)
    return JSONResponse(
        content={
            "total": len(devices),
            "devices": [
                {
                    "device_id": d.device_id,
                    "hostname": d.hostname,
                    "vendor": d.vendor,
                    "platform": d.platform,
                    "version": d.version,
                    "environment": d.environment,
                    "location": d.location,
                    "owner": d.owner,
                    "tags": d.tags,
                    "first_seen": d.first_seen,
                    "last_seen": d.last_seen,
                    "last_audit_id": d.last_audit_id,
                    "current_posture": d.current_posture,
                    "status": d.status,
                }
                for d in devices
            ],
        }
    )


@router.post("/api/v1/devices", summary="Register or update device record")
def register_device(req: DeviceCreateApiRequest) -> JSONResponse:
    svc = DeviceInventoryService(_get_db_path())
    dev = svc.register_or_update_device(
        hostname=req.hostname,
        vendor=req.vendor,
        platform=req.platform,
        version=req.version,
        environment=req.environment,
        location=req.location,
        owner=req.owner,
        tags=req.tags,
    )
    AuditTrailService(_get_db_path()).log_action("operator", "REGISTER_DEVICE", device_id=dev.device_id)
    return JSONResponse(
        content={
            "device_id": dev.device_id,
            "hostname": dev.hostname,
            "vendor": dev.vendor,
            "environment": dev.environment,
            "current_posture": dev.current_posture,
        }
    )


@router.get("/api/v1/devices/{device_id}", summary="Get device details")
def get_device_details(device_id: str) -> JSONResponse:
    svc = DeviceInventoryService(_get_db_path())
    dev = svc.get_device(device_id)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return JSONResponse(
        content={
            "device_id": dev.device_id,
            "hostname": dev.hostname,
            "vendor": dev.vendor,
            "platform": dev.platform,
            "version": dev.version,
            "environment": dev.environment,
            "location": dev.location,
            "owner": dev.owner,
            "tags": dev.tags,
            "first_seen": dev.first_seen,
            "last_seen": dev.last_seen,
            "last_audit_id": dev.last_audit_id,
            "current_posture": dev.current_posture,
            "status": dev.status,
        }
    )


# --- 3.2 Finding Prioritization Queue ---

@router.get("/api/v1/prioritization/queue", summary="Operator Risk Priority Queue")
def get_prioritized_finding_queue(device_id: str | None = Query(default=None)) -> JSONResponse:
    svc = FindingPrioritizationService(_get_db_path())
    queue = svc.get_priority_queue(device_id=device_id)
    return JSONResponse(
        content={
            "total": len(queue),
            "queue": [
                {
                    "finding_id": q.finding_id,
                    "fingerprint": q.fingerprint,
                    "device_id": q.device_id,
                    "control_id": q.control_id,
                    "severity": q.severity,
                    "priority_tier": q.priority_tier,
                    "priority_score": q.priority_score,
                    "occurrence_count": q.occurrence_count,
                    "risk_factors": q.risk_factors,
                    "evidence_snippet": q.evidence_snippet,
                }
                for q in queue
            ],
        }
    )


# --- 3.3 Remediation Intelligence & 3.4 Verification ---

@router.get("/api/v1/remediation/{control_id}", summary="Get structured remediation guidance")
def get_remediation_guidance(control_id: str, vendor: str | None = Query(default=None)) -> JSONResponse:
    svc = RemediationService()
    rem = svc.get_remediation(control_id=control_id, vendor=vendor)
    return JSONResponse(
        content={
            "intent_id": rem.intent_id,
            "control_id": rem.control_id,
            "title": rem.title,
            "goal": rem.goal,
            "risk_notes": rem.risk_notes,
            "instructions": [
                {
                    "vendor": i.vendor,
                    "platform": i.platform,
                    "syntax": i.syntax,
                    "verification_command": i.verification_command,
                    "preconditions": i.preconditions,
                }
                for i in rem.instructions
            ],
        }
    )


@router.post("/api/v1/remediation/{finding_id}/verify", summary="Verify remediation results post-fix")
def verify_remediation(finding_id: str, req: RemediationVerifyApiRequest) -> JSONResponse:
    svc = RemediationService()
    res = svc.verify_remediation(
        finding_id=finding_id,
        control_id=req.control_id,
        remediated_config_text=req.remediated_config_text,
        vendor=req.vendor,
    )
    AuditTrailService(_get_db_path()).log_action(
        actor="operator",
        operation="VERIFY_REMEDIATION",
        finding_id=finding_id,
        after_state=res.status,
    )
    return JSONResponse(
        content={
            "finding_id": res.finding_id,
            "control_id": res.control_id,
            "status": res.status,
            "previous_status": res.previous_status,
            "current_status": res.current_status,
            "evidence_note": res.evidence_note,
            "verification_timestamp": res.verification_timestamp,
        }
    )


# --- 3.5 Configuration Baselines ---

@router.get("/api/v1/baselines/{device_id}", summary="Get active baseline for device")
def get_device_baseline(device_id: str) -> JSONResponse:
    svc = BaselineService(_get_db_path())
    base = svc.get_latest_baseline(device_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"No approved baseline found for device '{device_id}'")
    return JSONResponse(
        content={
            "baseline_id": base.baseline_id,
            "device_id": base.device_id,
            "version": base.version,
            "created_at": base.created_at,
            "created_by": base.created_by,
            "fingerprint": base.fingerprint,
            "status": base.status,
            "pass_count": base.pass_count,
            "fail_count": base.fail_count,
        }
    )


@router.post("/api/v1/baselines/{device_id}", summary="Create approved immutable baseline")
def create_device_baseline(device_id: str, req: BaselineCreateApiRequest) -> JSONResponse:
    svc = BaselineService(_get_db_path())
    base = svc.create_baseline(
        device_id=device_id,
        config_text=req.config_text,
        created_by=req.created_by,
        vendor=req.vendor,
    )
    AuditTrailService(_get_db_path()).log_action("operator", "CREATE_BASELINE", device_id=device_id)
    return JSONResponse(
        content={
            "baseline_id": base.baseline_id,
            "device_id": base.device_id,
            "version": base.version,
            "status": base.status,
            "fingerprint": base.fingerprint,
        }
    )


@router.post("/api/v1/baselines/{device_id}/compare", summary="Compare config against baseline")
def compare_with_baseline(device_id: str, req: BaselineCreateApiRequest) -> JSONResponse:
    svc = BaselineService(_get_db_path())
    res = svc.compare_with_baseline(
        device_id=device_id,
        current_config_text=req.config_text,
        vendor=req.vendor,
    )
    return JSONResponse(
        content={
            "baseline_id": res.baseline_id,
            "device_id": res.device_id,
            "baseline_version": res.baseline_version,
            "is_compliant_with_baseline": res.is_compliant_with_baseline,
            "added_directives": res.added_directives,
            "removed_directives": res.removed_directives,
            "modified_directives": res.modified_directives,
            "security_drift_detected": res.security_drift_detected,
        }
    )


# --- 3.6 Scheduling & 3.7 Fleet Posture ---

@router.get("/api/v1/schedules", summary="List audit schedules")
def list_schedules() -> JSONResponse:
    svc = AuditScheduleService(_get_db_path())
    jobs = svc.list_schedules()
    return JSONResponse(
        content={
            "jobs": [
                {
                    "job_id": j.job_id,
                    "device_id": j.device_id,
                    "interval": j.interval,
                    "last_run": j.last_run,
                    "next_run": j.next_run,
                    "status": j.status,
                }
                for j in jobs
            ]
        }
    )


@router.post("/api/v1/schedules", summary="Create audit schedule")
def create_schedule(req: ScheduleCreateApiRequest) -> JSONResponse:
    svc = AuditScheduleService(_get_db_path())
    job = svc.create_schedule(device_id=req.device_id, interval=req.interval)
    return JSONResponse(
        content={
            "job_id": job.job_id,
            "device_id": job.device_id,
            "interval": job.interval,
            "next_run": job.next_run,
            "status": job.status,
        }
    )


@router.get("/api/v1/fleet/posture", summary="Fleet-wide security posture dashboard")
def get_fleet_posture() -> JSONResponse:
    svc = FleetPostureService(_get_db_path())
    return JSONResponse(content=svc.get_fleet_posture_overview())


# --- 3.8 Bounded Natural-Language Query Layer ---

@router.post("/api/v1/query", summary="Bounded natural-language security query")
def execute_natural_language_query(req: QueryApiRequest) -> JSONResponse:
    engine = NaturalLanguageQueryEngine(_get_db_path())
    res = engine.execute_bounded_query(req.query)
    AuditTrailService(_get_db_path()).log_action("operator", "NL_QUERY", after_state={"query": req.query})
    return JSONResponse(content=res)


# --- 3.10 Export & Webhooks ---

@router.get("/api/v1/export/devices", summary="Export devices CSV")
def export_devices_csv() -> Response:
    svc = OperationalExportService(_get_db_path())
    csv_data = svc.export_devices_csv()
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=fleet_devices.csv"})


@router.get("/api/v1/export/findings", summary="Export findings CSV")
def export_findings_csv() -> Response:
    svc = OperationalExportService(_get_db_path())
    csv_data = svc.export_findings_csv()
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=security_findings.csv"})


@router.post("/api/v1/webhooks/dispatch", summary="Dispatch test SIEM/ticketing webhook")
def dispatch_webhook(event_type: str = "finding.created", payload: dict | None = None) -> JSONResponse:
    svc = WebhookService()
    res = svc.dispatch_event(event_type, payload or {"sample": "security_finding_alert", "secret_key": "cisco123"})
    return JSONResponse(content=res)
