"""
tests.unit.test_framework_filtering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for API AuditRequest framework filtering.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

CISCO_CONF = "hostname ROUTER-FW-TEST\nip ssh version 2\n"


def test_audit_without_framework_runs_all_rules() -> None:
    resp = client.post("/api/v1/audit", json={"config_text": CISCO_CONF})
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_controls"] == 13


def test_audit_with_cis_framework_filter() -> None:
    resp = client.post("/api/v1/audit", json={"config_text": CISCO_CONF, "framework": "CIS"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_controls"] >= 1
    # All returned findings must carry CIS in framework_refs
    for r in data["results"]:
        assert any("CIS" in ref for ref in r["framework_refs"])


def test_audit_with_nist_framework_filter() -> None:
    resp = client.post("/api/v1/audit", json={"config_text": CISCO_CONF, "framework": "NIST"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_controls"] >= 1
    for r in data["results"]:
        assert any("NIST" in ref for ref in r["framework_refs"])


def test_audit_with_stig_framework_filter() -> None:
    resp = client.post("/api/v1/audit", json={"config_text": CISCO_CONF, "framework": "DISA-STIG"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_controls"] >= 1
    for r in data["results"]:
        assert any("DISA" in ref or "STIG" in ref for ref in r["framework_refs"])
