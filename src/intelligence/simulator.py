"""
intelligence.simulator
~~~~~~~~~~~~~~~~~~~~~~

Deterministic What-If Compliance Simulator.

Design & Safety Rules:
- Evaluates virtual compliance posture when proposed security intents are fixed.
- Every simulation is explicitly marked ``is_simulated: True``.
- NEVER mutates original configuration text.
- NEVER overwrites persistent audit history or findings in SQLite.
- Uses existing deterministic compliance engine rules without LLM dependency.
"""

from __future__ import annotations

import copy
from src.api.schemas import AuditResponse
from src.compliance.model import ComplianceResult, ComplianceStatus
from src.intelligence.model import SimulationResult
from src.risk.engine import compute_risk


class WhatIfSimulator:
    """Deterministic simulation engine for predicting security posture deltas."""

    def simulate_intent_fixes(
        self,
        audit_response: AuditResponse,
        intents_to_fix: list[str],
    ) -> SimulationResult:
        """Simulate fixing specified security intents on an existing audit result."""
        from src.intelligence.service import SECURITY_INTENTS

        # Identify all control IDs mapped to the requested security intents
        controls_to_resolve: set[str] = set()
        for intent_id in intents_to_fix:
            intent = next((i for i in SECURITY_INTENTS if i.id == intent_id or i.name == intent_id), None)
            if intent:
                controls_to_resolve.update(intent.related_control_ids)
            else:
                # Direct control_id passed
                controls_to_resolve.add(intent_id)

        # Deep copy results to guarantee strict isolation
        simulated_results: list[ComplianceResult] = []
        resolved_controls: list[str] = []

        for r_schema in audit_response.results:
            c_status = r_schema.status.value.lower() if hasattr(r_schema.status, "value") else str(r_schema.status).lower()
            c_sev = r_schema.severity.value.upper() if hasattr(r_schema.severity, "value") else str(r_schema.severity).upper()

            if c_status == "fail" and r_schema.control_id in controls_to_resolve:
                # Virtual fix: transition from FAIL to PASS
                new_status = ComplianceStatus.PASS
                resolved_controls.append(r_schema.control_id)
            else:
                new_status = ComplianceStatus(c_status) if c_status in ("pass", "fail", "not_applicable", "needs_review") else ComplianceStatus.FAIL

            simulated_results.append(
                ComplianceResult(
                    control_id=r_schema.control_id,
                    control_name=r_schema.control_name,
                    description=r_schema.description,
                    severity=c_sev,
                    status=new_status,
                    vendor=r_schema.vendor,
                    hostname=r_schema.hostname,
                )
            )

        # Calculate original vs projected metrics
        orig_fails = sum(1 for r in audit_response.results if (r.status.value if hasattr(r.status, "value") else r.status).lower() == "fail")
        orig_passes = sum(1 for r in audit_response.results if (r.status.value if hasattr(r.status, "value") else r.status).lower() == "pass")

        proj_fails = sum(1 for r in simulated_results if r.status == ComplianceStatus.FAIL)
        proj_passes = sum(1 for r in simulated_results if r.status == ComplianceStatus.PASS)

        # Calculate original vs projected risk metrics
        orig_risk = 0.0
        for r_schema in audit_response.results:
            st = r_schema.status.value.lower() if hasattr(r_schema.status, "value") else str(r_schema.status).lower()
            if st == "fail":
                sev = r_schema.severity.value.upper() if hasattr(r_schema.severity, "value") else str(r_schema.severity).upper()
                dummy_res = ComplianceResult(
                    control_id=r_schema.control_id,
                    control_name=r_schema.control_name,
                    description=r_schema.description,
                    severity=sev,
                    status=ComplianceStatus.FAIL,
                    vendor=r_schema.vendor,
                    hostname=r_schema.hostname,
                )
                s, _ = compute_risk(dummy_res)
                orig_risk += s
        orig_risk = round(orig_risk, 2)

        proj_risk = round(sum(compute_risk(r)[0] for r in simulated_results if r.status == ComplianceStatus.FAIL), 2)

        remaining_fails = [r.control_id for r in simulated_results if r.status == ComplianceStatus.FAIL]

        if proj_fails < orig_fails:
            impact = "SECURITY_IMPROVEMENT"
        elif proj_fails > orig_fails:
            impact = "SECURITY_DEGRADATION"
        else:
            impact = "NEUTRAL"

        return SimulationResult(
            is_simulated=True,
            original_fail_count=orig_fails,
            projected_fail_count=proj_fails,
            original_pass_count=orig_passes,
            projected_pass_count=proj_passes,
            original_risk_score=orig_risk,
            projected_risk_score=proj_risk,
            resolved_control_ids=sorted(resolved_controls),
            remaining_fail_control_ids=sorted(remaining_fails),
            applied_intent_ids=sorted(list(intents_to_fix)),
            security_impact=impact,
        )

