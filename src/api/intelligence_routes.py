"""
api.intelligence_routes
~~~~~~~~~~~~~~~~~~~~~~~

FastAPI API endpoints for Phase 2: Cross-Vendor Security Intelligence.
"""

from __future__ import annotations

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.intelligence.dependencies import DependencyGraphService
from src.intelligence.explanation import generate_bounded_finding_explanation
from src.intelligence.service import CrossVendorIntelligenceService
from src.intelligence.simulator import WhatIfSimulator
from src.audit_store.service import AuditStoreService

router = APIRouter(tags=["Intelligence"])


class PolicyTranslateRequest(BaseModel):
    policy_id: str = Field(..., description="Policy ID or name (e.g. 'POL-HARDENED-MGMT')")
    vendor: str | None = Field(default=None, description="Optional vendor filter")


class SimulationApiRequest(BaseModel):
    audit_id: str | None = Field(default=None, description="Past audit ID to simulate against")
    config_text: str | None = Field(default=None, description="Raw configuration text to simulate")
    intents_to_fix: list[str] = Field(..., description="List of intent IDs or control IDs to simulate fixing")


class FindingExplanationApiRequest(BaseModel):
    control_id: str = Field(..., description="Control ID (e.g. 'TLN-001')")
    control_name: str = Field(..., description="Control name")
    severity: str = Field(..., description="Severity tier")
    evidence_text: str | None = Field(default=None, description="Optional configuration evidence snippet")


def _get_audit_store() -> AuditStoreService:
    db_path = os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))
    return AuditStoreService(db_path=db_path)


@router.get("/api/v1/intelligence/intents", summary="List vendor-neutral security intents")
def list_security_intents() -> JSONResponse:
    """Return catalog of vendor-neutral security intents."""
    svc = CrossVendorIntelligenceService()
    return JSONResponse(content={"intents": svc.list_intents()})


@router.get("/api/v1/intelligence/coverage", summary="Cross-vendor control coverage matrix")
def get_coverage_matrix(vendor: str | None = Query(default=None)) -> JSONResponse:
    """Return dynamic Cross-Vendor Control Coverage Matrix across Cisco, Juniper, Arista, FortiOS, PAN-OS."""
    svc = CrossVendorIntelligenceService()
    matrix = svc.get_coverage_matrix(vendor_filter=vendor)
    return JSONResponse(content={"coverage_matrix": matrix})


@router.post("/api/v1/intelligence/policies/translate", summary="Translate security policy to vendor syntax")
def translate_policy(req: PolicyTranslateRequest) -> JSONResponse:
    """Translate vendor-neutral security policy requirements across vendor platforms."""
    svc = CrossVendorIntelligenceService()
    res = svc.translate_policy(policy_id=req.policy_id, vendor_filter=req.vendor)
    return JSONResponse(content={
        "policy_id": res.policy_id,
        "policy_name": res.policy_name,
        "description": res.description,
        "translations": [
            {
                "vendor": t.vendor,
                "supported_intents": t.supported_intents,
                "unsupported_intents": t.unsupported_intents,
                "syntax_guidance": t.syntax_guidance,
            }
            for t in res.translations
        ],
    })


@router.post("/api/v1/simulations", summary="Run deterministic what-if compliance simulation")
def run_simulation(req: SimulationApiRequest) -> JSONResponse:
    """Simulate fixing specified security intents or controls without mutating original data."""
    store = _get_audit_store()
    audit_resp = None

    if req.audit_id:
        audit_resp = store.get_audit(req.audit_id)

    if not audit_resp and req.config_text:
        from src.api.service import run_audit
        from src.api.schemas import AuditRequest
        audit_resp = run_audit(AuditRequest(config_text=req.config_text))

    if not audit_resp:
        # Generate baseline sample audit response if neither ID nor config provided
        from src.api.service import run_audit
        from src.api.schemas import AuditRequest
        audit_resp = run_audit(AuditRequest(config_text="hostname RTR-CORE-01\nline vty 0 4\n transport input telnet ssh\n no service password-encryption"))

    simulator = WhatIfSimulator()
    sim_res = simulator.simulate_intent_fixes(audit_response=audit_resp, intents_to_fix=req.intents_to_fix)

    return JSONResponse(content={
        "is_simulated": sim_res.is_simulated,
        "original_fail_count": sim_res.original_fail_count,
        "projected_fail_count": sim_res.projected_fail_count,
        "original_pass_count": sim_res.original_pass_count,
        "projected_pass_count": sim_res.projected_pass_count,
        "original_risk_score": round(sim_res.original_risk_score, 2),
        "projected_risk_score": round(sim_res.projected_risk_score, 2),
        "resolved_control_ids": sim_res.resolved_control_ids,
        "remaining_fail_control_ids": sim_res.remaining_fail_control_ids,
        "applied_intent_ids": sim_res.applied_intent_ids,
        "security_impact": sim_res.security_impact,
    })


@router.post("/api/v1/findings/{finding_id}/explanation", summary="Bounded AI finding explanation")
def get_finding_explanation(finding_id: str, req: FindingExplanationApiRequest) -> JSONResponse:
    """Generate bounded AI explanation for a deterministic finding with fallback safety."""
    explanation = generate_bounded_finding_explanation(
        control_id=req.control_id,
        control_name=req.control_name,
        severity=req.severity,
        evidence_text=req.evidence_text,
    )
    return JSONResponse(content=explanation)


@router.get("/api/v1/intelligence/dependencies", summary="Control dependency & attack path graph")
def get_control_dependencies() -> JSONResponse:
    """Return control dependency graph and threat scenario amplification nodes."""
    svc = DependencyGraphService()
    return JSONResponse(content={"dependencies": svc.get_dependency_graph()})
