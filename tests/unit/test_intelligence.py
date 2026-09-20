"""
tests/unit/test_intelligence.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit and integration tests for Phase 2: Cross-Vendor Security Intelligence.
Verifies cross-vendor intent mapping, control coverage matrix, policy translation,
deterministic What-If compliance simulation isolation, bounded AI explanations,
and control dependency graph endpoints.
"""

from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.compliance.model import ComplianceResult, ComplianceStatus, Severity
from src.intelligence.dependencies import DependencyGraphService
from src.intelligence.explanation import generate_bounded_finding_explanation
from src.intelligence.service import CrossVendorIntelligenceService
from src.intelligence.simulator import WhatIfSimulator


@pytest.fixture
def client():
    return TestClient(app)


def test_cross_vendor_intents():
    svc = CrossVendorIntelligenceService()
    intents = svc.list_intents()
    assert len(intents) >= 10
    intent_ids = [i["id"] for i in intents]
    assert "TELNET_DISABLED" in intent_ids
    assert "SSH_VERSION_ENFORCED" in intent_ids
    assert "AAA_AUTHENTICATION_ENABLED" in intent_ids


def test_coverage_matrix():
    svc = CrossVendorIntelligenceService()
    matrix = svc.get_coverage_matrix()
    assert len(matrix) >= 10
    tln_entry = next(item for item in matrix if item["intent_id"] == "TELNET_DISABLED")
    assert tln_entry["vendor_coverage"]["cisco"]["status"] == "SUPPORTED"
    assert tln_entry["vendor_coverage"]["juniper"]["status"] == "SUPPORTED"
    assert tln_entry["vendor_coverage"]["arista"]["status"] == "SUPPORTED"
    assert tln_entry["vendor_coverage"]["fortinet"]["status"] == "SUPPORTED"
    assert tln_entry["vendor_coverage"]["panos"]["status"] == "SUPPORTED"


def test_policy_translation():
    svc = CrossVendorIntelligenceService()
    res = svc.translate_policy("POL-HARDENED-MGMT")
    assert res.policy_id == "POL-HARDENED-MGMT"
    assert len(res.translations) == 5
    cisco_trans = next(t for t in res.translations if t.vendor == "cisco")
    assert "TELNET_DISABLED" in cisco_trans.supported_intents


def test_what_if_simulator_isolation(client):
    # Perform audit
    audit_res = client.post(
        "/api/v1/audit",
        json={"config_text": "hostname RTR-01\nline vty 0 4\n transport input telnet ssh\n no service password-encryption"},
    )
    assert audit_res.status_code == 200
    orig_data = audit_res.json()
    orig_fail_count = orig_data["summary"]["fail_count"]

    # Simulate fixing TELNET_DISABLED
    sim_res = client.post(
        "/api/v1/simulations",
        json={
            "config_text": "hostname RTR-01\nline vty 0 4\n transport input telnet ssh\n no service password-encryption",
            "intents_to_fix": ["TELNET_DISABLED"],
        },
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()

    assert sim_data["is_simulated"] is True
    assert sim_data["original_fail_count"] == orig_fail_count
    assert sim_data["projected_fail_count"] < orig_fail_count
    assert "CIS-IOS-002" in sim_data["resolved_control_ids"] or "TLN-001" in sim_data["resolved_control_ids"] or len(sim_data["resolved_control_ids"]) >= 1

    # Verify original audit remains untouched (isolation)
    post_audit = client.post(
        "/api/v1/audit",
        json={"config_text": "hostname RTR-01\nline vty 0 4\n transport input telnet ssh\n no service password-encryption"},
    )
    assert post_audit.json()["summary"]["fail_count"] == orig_fail_count


def test_bounded_ai_explanation_fallback():
    explanation = generate_bounded_finding_explanation(
        control_id="TLN-001",
        control_name="Telnet Must Be Disabled",
        severity="CRITICAL",
        evidence_text="line vty 0 4\n transport input telnet",
        ai_provider=None,
    )

    assert explanation["control_id"] == "TLN-001"
    assert "Telnet" in explanation["why_it_matters"]
    assert len(explanation["recommended_remediation"]) > 10


def test_dependency_graph():
    svc = DependencyGraphService()
    graph = svc.get_dependency_graph()
    assert len(graph) >= 5
    tln_node = next(n for n in graph if n["control_id"] == "TLN-001")
    assert "AAA-001" in tln_node["amplifies"]

    attack_paths = svc.analyze_attack_paths(["TLN-001", "AAA-001"])
    assert len(attack_paths) >= 1


def test_intelligence_api_endpoints(client):
    # GET /api/v1/intelligence/intents
    res1 = client.get("/api/v1/intelligence/intents")
    assert res1.status_code == 200
    assert len(res1.json()["intents"]) >= 10

    # GET /api/v1/intelligence/coverage
    res2 = client.get("/api/v1/intelligence/coverage")
    assert res2.status_code == 200
    assert "coverage_matrix" in res2.json()

    # POST /api/v1/intelligence/policies/translate
    res3 = client.post("/api/v1/intelligence/policies/translate", json={"policy_id": "POL-HARDENED-MGMT"})
    assert res3.status_code == 200
    assert res3.json()["policy_id"] == "POL-HARDENED-MGMT"

    # POST /api/v1/findings/{id}/explanation
    res4 = client.post(
        "/api/v1/findings/TLN-001/explanation",
        json={"control_id": "TLN-001", "control_name": "Telnet Disabled", "severity": "CRITICAL"},
    )
    assert res4.status_code == 200
    assert res4.json()["control_id"] == "TLN-001"

    # GET /api/v1/intelligence/dependencies
    res5 = client.get("/api/v1/intelligence/dependencies")
    assert res5.status_code == 200
    assert "dependencies" in res5.json()

    # GET /api/v1/intelligence/posture-analytics
    res6 = client.get("/api/v1/intelligence/posture-analytics")
    assert res6.status_code == 200
    assert "vendor_coverage" in res6.json()
    assert "intent_support_ratio" in res6.json()


def test_simulation_does_not_mutate_audit_history_or_findings(client):
    # 1. Create and persist an explicit audit for test-cisco-day1
    audit_req = {
        "config_text": "hostname test-cisco-day1\nline vty 0 4\n transport input telnet ssh\n no service password-encryption",
        "source_name": "test-cisco-day1",
    }
    audit_res = client.post("/api/v1/audit", json=audit_req)
    assert audit_res.status_code == 200

    # 2. Record audit history state
    hist_res_before = client.get("/api/v1/audits?limit=50")
    assert hist_res_before.status_code == 200
    audits_before = hist_res_before.json()["items"]
    before_count = len(audits_before)
    target_audit_before = next(a for a in audits_before if a.get("source_name") == "test-cisco-day1" or a.get("hostname") == "test-cisco-day1")
    assert target_audit_before["source_name"] == "test-cisco-day1"
    orig_pass = target_audit_before["pass_count"]
    orig_fail = target_audit_before["fail_count"]
    orig_total = target_audit_before["total"]

    # 3. Run What-If simulation with a DIFFERENT hostname RTR-BORDER-01
    sim_res = client.post(
        "/api/v1/simulations",
        json={
            "config_text": "hostname RTR-BORDER-01\nline vty 0 4\n transport input telnet ssh\n no service password-encryption",
            "intents_to_fix": ["TELNET_DISABLED", "PASSWORD_ENCRYPTION_ENABLED"],
        },
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["is_simulated"] is True

    # 4. Query audit history again
    hist_res_after = client.get("/api/v1/audits?limit=50")
    assert hist_res_after.status_code == 200
    audits_after = hist_res_after.json()["items"]

    # 5. Verify total audit count did NOT increase
    assert len(audits_after) == before_count

    # 6. Verify RTR-BORDER-01 was NOT added to audit history
    rtr_audit = next((a for a in audits_after if a.get("hostname") == "RTR-BORDER-01" or a.get("source_name") == "RTR-BORDER-01"), None)
    assert rtr_audit is None, "Simulation configuration must NOT be persisted as an audit history entry!"

    # 7. Verify original test-cisco-day1 audit record remains unchanged
    target_audit_after = next(a for a in audits_after if a.get("source_name") == "test-cisco-day1" or a.get("hostname") == "test-cisco-day1")
    assert target_audit_after["pass_count"] == orig_pass
    assert target_audit_after["fail_count"] == orig_fail
    assert target_audit_after["total"] == orig_total


