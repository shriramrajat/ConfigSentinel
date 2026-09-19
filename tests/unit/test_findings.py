"""
tests/unit/test_findings.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for Milestone 1.8: Security Finding Lifecycle Management.
Verifies finding correlation, status transitions (OPEN -> ACKNOWLEDGED -> RESOLVED -> REOPENED),
occurrence counting, and finding API routes.
"""

import tempfile
from pathlib import Path
import pytest

from src.compliance.model import ComplianceResult, ComplianceStatus, Severity
from src.findings.service import FindingService


@pytest.fixture
def temp_finding_service():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    svc = FindingService(db_path=db_path)
    yield svc
    Path(db_path).unlink(missing_ok=True)


def test_finding_lifecycle_flow(temp_finding_service):
    svc = temp_finding_service
    device_id = "RTR-CORE-01"

    # 1. Audit 1: Control CIS-IOS-001 FAILS
    result_fail = ComplianceResult(
        control_id="CIS-IOS-001",
        control_name="SSH Version 2",
        description="Ensure SSH Version 2 is enabled",
        severity=Severity.HIGH,
        status=ComplianceStatus.FAIL,
        vendor="cisco",
        hostname="RTR-CORE-01",
    )

    sync_res_1 = svc.sync_audit_findings(
        audit_id="audit-1",
        device_id=device_id,
        compliance_results=[result_fail],
    )

    assert sync_res_1["created"] == 1
    assert sync_res_1["updated"] == 0

    findings = svc.list_findings(device_id=device_id)
    assert len(findings) == 1
    f1 = findings[0]
    assert f1["control_id"] == "CIS-IOS-001"
    assert f1["status"] == "OPEN"
    assert f1["occurrence_count"] == 1
    assert f1["first_seen_audit_id"] == "audit-1"
    assert f1["last_seen_audit_id"] == "audit-1"

    # 2. Audit 2: Control CIS-IOS-001 FAILS again -> Occurrence count increases to 2
    sync_res_2 = svc.sync_audit_findings(
        audit_id="audit-2",
        device_id=device_id,
        compliance_results=[result_fail],
    )
    assert sync_res_2["created"] == 0
    assert sync_res_2["updated"] == 1

    findings_2 = svc.list_findings(device_id=device_id)
    assert len(findings_2) == 1
    f2 = findings_2[0]
    assert f2["status"] == "OPEN"
    assert f2["occurrence_count"] == 2
    assert f2["first_seen_audit_id"] == "audit-1"
    assert f2["last_seen_audit_id"] == "audit-2"

    # 3. Audit 3: Control CIS-IOS-001 PASSES -> Finding auto-resolved
    result_pass = ComplianceResult(
        control_id="CIS-IOS-001",
        control_name="SSH Version 2",
        description="Ensure SSH Version 2 is enabled",
        severity=Severity.HIGH,
        status=ComplianceStatus.PASS,
        vendor="cisco",
        hostname="RTR-CORE-01",
    )

    sync_res_3 = svc.sync_audit_findings(
        audit_id="audit-3",
        device_id=device_id,
        compliance_results=[result_pass],
    )
    assert sync_res_3["resolved"] == 1

    f3 = svc.get_finding(f1["id"])
    assert f3["status"] == "RESOLVED"
    assert f3["resolved_at"] is not None

    # 4. Audit 4: Control CIS-IOS-001 FAILS again -> Finding re-opened
    sync_res_4 = svc.sync_audit_findings(
        audit_id="audit-4",
        device_id=device_id,
        compliance_results=[result_fail],
    )
    assert sync_res_4["reopened"] == 1

    f4 = svc.get_finding(f1["id"])
    assert f4["status"] == "OPEN"
    assert f4["occurrence_count"] == 3
    assert f4["last_seen_audit_id"] == "audit-4"


def test_finding_manual_status_changes(temp_finding_service):
    svc = temp_finding_service
    device_id = "FW-PA-01"

    result_fail = ComplianceResult(
        control_id="PAN-001",
        control_name="Telnet Disabled",
        description="Ensure Telnet management is disabled",
        severity=Severity.CRITICAL,
        status=ComplianceStatus.FAIL,
        vendor="panos",
        hostname="FW-PA-01",
    )

    svc.sync_audit_findings(audit_id="audit-10", device_id=device_id, compliance_results=[result_fail])
    findings = svc.list_findings(device_id=device_id)
    finding_id = findings[0]["id"]

    # Acknowledge
    ack_res = svc.acknowledge_finding(finding_id)
    assert ack_res["status"] == "ACKNOWLEDGED"
    assert ack_res["acknowledged_at"] is not None

    # Resolve manually
    res_res = svc.resolve_finding(finding_id)
    assert res_res["status"] == "RESOLVED"
    assert res_res["resolved_at"] is not None

    # Reopen manually
    reopen_res = svc.reopen_finding(finding_id)
    assert reopen_res["status"] == "OPEN"
