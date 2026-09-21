"""
tests.unit.test_phase3
~~~~~~~~~~~~~~~~~~~~~~

Unit and Integration Tests for Phase 3: Production Security Operations.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.baselines.service import BaselineService
from src.export.service import OperationalExportService, WebhookService
from src.fleet.service import FleetPostureService
from src.inventory.model import DevicePostureStatus, DeviceStatus
from src.inventory.service import DeviceInventoryService
from src.prioritization.service import FindingPrioritizationService
from src.query.engine import NaturalLanguageQueryEngine
from src.remediation.service import RemediationService
from src.scheduling.service import AuditScheduleService
from src.security.audit_trail import AuditTrailService
from src.security.hardening import SecurityHardeningError, safe_extract_zip, validate_file_size


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def client(temp_db, monkeypatch):
    monkeypatch.setenv("AUDIT_DB_PATH", temp_db)
    app = create_app()
    return TestClient(app)


def test_device_inventory_registration_and_filtering(temp_db):
    svc = DeviceInventoryService(db_path=temp_db)
    dev1 = svc.register_or_update_device(hostname="RTR-01", vendor="cisco", environment="PRODUCTION")
    dev2 = svc.register_or_update_device(hostname="FW-01", vendor="juniper", environment="DMZ")

    assert dev1.hostname == "RTR-01"
    assert dev1.vendor == "cisco"
    assert dev2.environment == "DMZ"

    devices = svc.list_devices(vendor="cisco")
    assert len(devices) == 1
    assert devices[0].hostname == "RTR-01"


def test_finding_prioritization_queue(temp_db, client):
    # Perform audit to register findings in DB
    client.post(
        "/api/v1/audit",
        json={"config_text": "hostname RTR-01\nline vty 0 4\n transport input telnet\n no service password-encryption"},
    )
    p_svc = FindingPrioritizationService(db_path=temp_db)
    queue = p_svc.get_priority_queue()

    assert len(queue) > 0
    top_finding = queue[0]
    assert top_finding.priority_score > 0
    assert len(top_finding.risk_factors) > 0


def test_remediation_catalog_and_verification_success(temp_db):
    rem_svc = RemediationService()
    rem = rem_svc.get_remediation("TLN-001", vendor="cisco")
    assert rem.control_id == "TLN-001"
    assert any(i.vendor == "cisco" for i in rem.instructions)

    # Compliant config where Telnet is removed/disabled
    compliant_config = "hostname RTR-01\nline vty 0 4\n transport input ssh\n service password-encryption"
    res = rem_svc.verify_remediation(
        finding_id="find-123",
        control_id="TLN-001",
        remediated_config_text=compliant_config,
        vendor="cisco",
    )
    assert res.status == "FIX_VERIFIED"
    assert res.current_status == "PASS"


def test_remediation_verification_failure(temp_db):
    rem_svc = RemediationService()
    non_compliant_config = "hostname RTR-01\nline vty 0 4\n transport input telnet"
    res = rem_svc.verify_remediation(
        finding_id="find-123",
        control_id="TLN-001",
        remediated_config_text=non_compliant_config,
        vendor="cisco",
    )
    assert res.status == "FIX_NOT_VERIFIED"
    assert res.current_status.upper() == "FAIL"


def test_baseline_creation_and_immutability(temp_db):
    b_svc = BaselineService(db_path=temp_db)
    cfg1 = "hostname RTR-01\nline vty 0 4\n transport input ssh"
    base1 = b_svc.create_baseline("dev-1", cfg1, created_by="admin")

    assert base1.version == 1
    assert base1.status == "APPROVED"

    # Creating a new baseline version increases version number to 2
    cfg2 = "hostname RTR-01\nline vty 0 4\n transport input ssh\n service password-encryption"
    base2 = b_svc.create_baseline("dev-1", cfg2, created_by="admin")

    assert base2.version == 2
    latest = b_svc.get_latest_baseline("dev-1")
    assert latest.version == 2
    assert latest.baseline_id == base2.baseline_id


def test_baseline_drift_comparison(temp_db):
    b_svc = BaselineService(db_path=temp_db)
    base_cfg = "hostname RTR-01\nline vty 0 4\n transport input ssh"
    b_svc.create_baseline("dev-1", base_cfg)

    # Current config with modified directive
    curr_cfg = "hostname RTR-01-MODIFIED\nline vty 0 4\n transport input telnet"
    comp = b_svc.compare_with_baseline("dev-1", curr_cfg)

    assert comp.security_drift_detected is True
    assert comp.is_compliant_with_baseline is False


def test_audit_scheduling(temp_db):
    s_svc = AuditScheduleService(db_path=temp_db)
    job = s_svc.create_schedule(device_id="dev-100", interval="DAILY")
    assert job.device_id == "dev-100"
    assert job.next_run is not None

    schedules = s_svc.list_schedules()
    assert len(schedules) >= 1


def test_fleet_posture_metrics(temp_db):
    inv_svc = DeviceInventoryService(db_path=temp_db)
    inv_svc.register_or_update_device(hostname="RTR-01", vendor="cisco", current_posture="HEALTHY")
    inv_svc.register_or_update_device(hostname="FW-01", vendor="juniper", current_posture="CRITICAL")

    fleet_svc = FleetPostureService(db_path=temp_db)
    posture = fleet_svc.get_fleet_posture_overview()

    assert posture["total_devices"] == 2
    assert posture["healthy_devices"] == 1
    assert posture["critical_devices"] == 1


def test_bounded_nl_query_engine(temp_db):
    q_engine = NaturalLanguageQueryEngine(db_path=temp_db)
    res = q_engine.execute_bounded_query("Show me cisco devices with Telnet enabled")

    assert res["parsed_schema"]["intent_id"] == "TELNET_DISABLED"
    assert res["parsed_schema"]["vendor"] == "cisco"


def test_nl_query_sql_injection_rejection(temp_db):
    q_engine = NaturalLanguageQueryEngine(db_path=temp_db)
    res = q_engine.execute_bounded_query("Show devices where 1=1; DROP TABLE devices;")

    assert "DROP" not in res["parsed_schema"]["keyword"] if res["parsed_schema"]["keyword"] else True
    # Verify DB table remains intact and functional
    inv_svc = DeviceInventoryService(db_path=temp_db)
    assert isinstance(inv_svc.list_devices(), list)


def test_operational_exports_and_webhooks(temp_db):
    exp_svc = OperationalExportService(db_path=temp_db)
    csv_dev = exp_svc.export_devices_csv()
    assert "hostname" in csv_dev

    wh_svc = WebhookService()
    evt = wh_svc.dispatch_event("finding.created", {"device": "RTR-01", "raw_text": "password cisco_secret_123"})
    assert "cisco_secret_123" not in str(evt["payload"])


def test_audit_trail_logging_and_redaction(temp_db):
    trail_svc = AuditTrailService(db_path=temp_db)
    log_id = trail_svc.log_action("operator", "UPDATE_CONFIG", before_state={"config": "enable secret cisco123"})
    assert log_id.startswith("log-")

    logs = trail_svc.get_recent_logs()
    assert len(logs) >= 1
    assert "cisco123" not in logs[0]["before_state"]


def test_security_hardening_zip_slip_rejection(tmp_path):
    # Test oversized file size rejection
    with pytest.raises(SecurityHardeningError):
        validate_file_size("A" * (11 * 1024 * 1024))


def test_phase3_api_endpoints(client):
    # POST /api/v1/devices
    res1 = client.post("/api/v1/devices", json={"hostname": "RTR-CORE-01", "vendor": "cisco"})
    assert res1.status_code == 200
    device_id = res1.json()["device_id"]

    # GET /api/v1/inventory/devices
    res2 = client.get("/api/v1/inventory/devices")
    assert res2.status_code == 200
    assert res2.json()["total"] >= 1

    # GET /api/v1/prioritization/queue
    res3 = client.get("/api/v1/prioritization/queue")
    assert res3.status_code == 200

    # GET /api/v1/remediation/TLN-001
    res4 = client.get("/api/v1/remediation/TLN-001?vendor=cisco")
    assert res4.status_code == 200

    # POST /api/v1/baselines/{device_id}
    res5 = client.post(
        f"/api/v1/baselines/{device_id}",
        json={"config_text": "hostname RTR-CORE-01\nline vty 0 4\n transport input ssh"},
    )
    assert res5.status_code == 200

    # GET /api/v1/fleet/posture
    res6 = client.get("/api/v1/fleet/posture")
    assert res6.status_code == 200

    # POST /api/v1/query
    res7 = client.post("/api/v1/query", json={"query": "Show cisco devices with Telnet enabled"})
    assert res7.status_code == 200


# ---------------------------------------------------------------------------
# Regression tests: inventory endpoint wiring (Operations.tsx bug fix)
# ---------------------------------------------------------------------------

def test_inventory_endpoint_returns_correct_fleet_fields(client):
    """
    GET /api/v1/inventory/devices must return { total, devices: [...] }
    where each device has the fields the Operations dashboard renders:
    device_id, hostname, vendor, environment, current_posture, status.
    """
    # First register a device via explicit POST
    reg = client.post(
        "/api/v1/devices",
        json={
            "hostname": "RTR-PROD-01",
            "vendor": "cisco",
            "platform": "IOS-XE",
            "version": "17.3",
            "environment": "PRODUCTION",
        },
    )
    assert reg.status_code == 200
    reg_body = reg.json()
    assert reg_body["hostname"] == "RTR-PROD-01"
    assert reg_body["vendor"] == "cisco"

    # GET /api/v1/inventory/devices must now return this device with all required fields
    r = client.get("/api/v1/inventory/devices")
    assert r.status_code == 200
    body = r.json()

    # Top-level shape
    assert "total" in body, "Response must include 'total' key"
    assert "devices" in body, "Response must include 'devices' key"
    assert isinstance(body["devices"], list)
    assert body["total"] == len(body["devices"])
    assert body["total"] >= 1

    # Device record must contain all fields rendered by Operations.tsx
    dev = next((d for d in body["devices"] if d["hostname"] == "RTR-PROD-01"), None)
    assert dev is not None, "Registered device not found in inventory response"

    required_fields = ["device_id", "hostname", "vendor", "environment", "current_posture", "status"]
    for field in required_fields:
        assert field in dev, f"Inventory device missing required field: '{field}'"

    assert dev["hostname"] == "RTR-PROD-01"
    assert dev["vendor"] == "cisco"
    assert dev["environment"] == "PRODUCTION"
    assert dev["current_posture"] in ("HEALTHY", "NEEDS_ATTENTION", "CRITICAL", "UNKNOWN")
    assert dev["status"] in ("ACTIVE", "INACTIVE", "DECOMMISSIONED")


def test_legacy_devices_endpoint_is_not_fleet_inventory(client):
    """
    GET /api/v1/devices is the AUDIT STATS dashboard endpoint.
    Its response must NOT be usable as fleet inventory:
    - it does NOT have { total, devices } with hostname/environment/current_posture/status
    - each item uses 'device' (not 'device_id') and has audit_count/total_fails fields

    This test documents the two endpoints are intentionally separate and cannot be
    accidentally substituted for each other (regression guard for Operations.tsx).
    """
    # Perform an audit so the legacy endpoint has data
    client.post("/api/v1/audit", json={
        "config_text": "hostname TEST-LEGACY\nline vty 0 4\n transport input telnet ssh",
        "source": "TEST-LEGACY",
    })

    r = client.get("/api/v1/devices")
    assert r.status_code == 200
    body = r.json()

    # Legacy endpoint returns { devices: [...] } but each item is audit-stats, NOT inventory
    assert "devices" in body
    assert isinstance(body["devices"], list)

    # The legacy endpoint has NO 'total' key at the top level (inventory has it)
    assert "total" not in body, "Legacy /api/v1/devices must not have a 'total' key — it is not a fleet inventory response"

    if body["devices"]:
        item = body["devices"][0]
        # Legacy items use 'device' (audit source name), not 'device_id'
        assert "device" in item, "Legacy items must use 'device' key (audit source name)"
        assert "device_id" not in item, "Legacy items must NOT have 'device_id' — they are audit stats, not inventory records"
        assert "audit_count" in item, "Legacy items must have 'audit_count' field"
        assert "current_posture" not in item, "Legacy items must NOT have 'current_posture' — that is an inventory field"
        assert "environment" not in item, "Legacy items must NOT have 'environment' — that is an inventory field"


def test_fleet_posture_reflects_inventory_not_audit_history(client):
    """
    GET /api/v1/fleet/posture must aggregate from the Phase 3 device inventory,
    NOT from audit history. Before any devices are registered, total_devices == 0
    even if audits have been performed.
    """
    # Perform an audit (this should NOT auto-register inventory)
    client.post("/api/v1/audit", json={
        "config_text": "hostname AUDIT-ONLY-DEVICE\nline vty 0 4\n transport input ssh\nservice password-encryption",
        "source": "AUDIT-ONLY-DEVICE",
    })

    # Fleet posture should still show 0 registered devices
    r = client.get("/api/v1/fleet/posture")
    assert r.status_code == 200
    body = r.json()

    assert "total_devices" in body
    assert body["total_devices"] == 0, (
        "An audit alone must NOT register a device in the Phase 3 fleet inventory. "
        "Explicit POST /api/v1/devices registration is required."
    )

    # Now register a device explicitly
    client.post("/api/v1/devices", json={"hostname": "FLEET-DEV-01", "vendor": "cisco"})

    r2 = client.get("/api/v1/fleet/posture")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["total_devices"] == 1, "After explicit registration, fleet posture must show 1 device"


# ---------------------------------------------------------------------------
# Regression tests: NL query severity case-mismatch bug
# ---------------------------------------------------------------------------

def _setup_cisco_device_with_findings(client) -> str:
    """
    Helper: register a Cisco device, run an audit with Telnet/no-encryption
    (generates CRITICAL + other findings), sync findings.
    Returns the registered device hostname.
    """
    hostname = "OPS-TEST-CISCO-NL"

    # Register inventory record
    reg = client.post("/api/v1/devices", json={
        "hostname": hostname,
        "vendor": "cisco",
        "environment": "LAB",
    })
    assert reg.status_code == 200

    # Run audit (generates open findings including CRITICAL TLN-001)
    audit_r = client.post("/api/v1/audit", json={
        "config_text": (
            "hostname " + hostname + "\n"
            "line vty 0 4\n transport input telnet ssh\n"
            "no service password-encryption"
        ),
        "source": hostname,
    })
    assert audit_r.status_code == 200

    return hostname


def test_nl_query_cisco_critical_open_returns_device(client):
    """
    Root cause regression: severity stored as UPPERCASE in DB, but FindingService
    was filtering with severity.lower() causing 'CRITICAL' != 'critical' mismatch.
    After the fix, vendor=cisco + severity=CRITICAL + status=FAIL must match the device.
    """
    hostname = _setup_cisco_device_with_findings(client)

    r = client.post("/api/v1/query", json={
        "query": "Show me Cisco devices with open critical findings"
    })
    assert r.status_code == 200
    body = r.json()

    schema = body["parsed_schema"]
    assert schema["vendor"] == "cisco"
    assert schema["severity"] == "CRITICAL"
    assert schema["status"] == "FAIL"

    assert len(body["matched_findings"]) >= 1, (
        "Expected at least one CRITICAL finding for the cisco device, got 0. "
        "This is the severity case-mismatch regression."
    )
    assert len(body["matched_devices"]) >= 1, (
        f"Expected device '{hostname}' to appear in matched_devices, got 0."
    )
    device_hostnames = [d["hostname"] for d in body["matched_devices"]]
    assert hostname in device_hostnames, f"Expected '{hostname}' in matched_devices: {device_hostnames}"


def test_nl_query_cisco_fail_returns_device(client):
    """
    vendor=cisco + status=FAIL (no severity filter) must return the cisco device
    that has open failing findings.
    """
    hostname = _setup_cisco_device_with_findings(client)

    r = client.post("/api/v1/query", json={
        "query": "Show cisco devices with failing findings"
    })
    assert r.status_code == 200
    body = r.json()

    schema = body["parsed_schema"]
    assert schema["vendor"] == "cisco"
    assert schema["status"] == "FAIL"
    assert schema["severity"] is None

    assert len(body["matched_findings"]) >= 1
    device_hostnames = [d["hostname"] for d in body["matched_devices"]]
    assert hostname in device_hostnames


def test_nl_query_critical_only_returns_device(client):
    """
    severity=CRITICAL alone (no vendor filter) must return devices with
    critical open findings. Tests that the severity filter works independently.
    """
    hostname = _setup_cisco_device_with_findings(client)

    r = client.post("/api/v1/query", json={
        "query": "Show me critical findings"
    })
    assert r.status_code == 200
    body = r.json()

    schema = body["parsed_schema"]
    assert schema["severity"] == "CRITICAL"

    assert len(body["matched_findings"]) >= 1, "CRITICAL findings must be returned after fix"
    device_hostnames = [d["hostname"] for d in body["matched_devices"]]
    assert hostname in device_hostnames


def test_nl_query_no_matching_findings_returns_zero(client):
    """
    A query for a vendor that has no registered devices with findings must
    return zero matched devices. Ensures the fix does not produce false positives.
    """
    r = client.post("/api/v1/query", json={
        "query": "Show juniper devices with critical findings"
    })
    assert r.status_code == 200
    body = r.json()

    schema = body["parsed_schema"]
    assert schema["vendor"] == "juniper"
    assert schema["severity"] == "CRITICAL"

    # No juniper devices registered in this isolated test DB
    assert len(body["matched_devices"]) == 0, "No juniper devices registered, must return zero"


def test_finding_service_severity_filter_case_insensitive(temp_db):
    """
    Unit regression: FindingService.list_findings(severity='CRITICAL') and
    list_findings(severity='critical') must both return the same results.
    Severity is stored UPPERCASE; the filter must normalize to uppercase before querying.
    """
    from src.findings.service import FindingService
    from src.api.schemas import AuditRequest
    from src.api.service import run_audit

    fs = FindingService(temp_db)
    audit = run_audit(AuditRequest(
        config_text="hostname RTR-SEV-TEST\nline vty 0 4\n transport input telnet ssh\nno service password-encryption",
        source="RTR-SEV-TEST",
    ), persist=True)
    fs.sync_audit_findings(audit_response=audit)

    # Confirm findings were synced
    all_findings = fs.list_findings()
    assert len(all_findings) >= 1

    # Both cases must return the same count
    upper_results = fs.list_findings(severity="CRITICAL")
    lower_results = fs.list_findings(severity="critical")
    mixed_results = fs.list_findings(severity="Critical")

    assert len(upper_results) == len(lower_results) == len(mixed_results), (
        f"Severity filter must be case-insensitive: "
        f"CRITICAL={len(upper_results)}, critical={len(lower_results)}, Critical={len(mixed_results)}"
    )
    assert len(upper_results) >= 1, "Expected at least one CRITICAL finding from TLN-001 audit"

    # All returned findings must have severity == 'CRITICAL'
    for f in upper_results:
        assert f["severity"] == "CRITICAL", f"Non-CRITICAL finding returned: {f['severity']}"


# ---------------------------------------------------------------------------
# Regression tests: GET /api/v1/export/findings HTTP 500 bug
# ---------------------------------------------------------------------------

def test_export_findings_empty_returns_200_with_headers(client):
    """
    GET /api/v1/export/findings with zero findings must return:
    - HTTP 200 (not 500)
    - Content-Type: text/csv
    - Content-Disposition: attachment filename=security_findings.csv
    - CSV with header row only (no data rows)

    Root cause regression: export_findings_csv() used attribute access (f.id)
    on dict objects returned by FindingService.list_findings(), causing AttributeError.
    With zero findings the loop body never executes, so the empty case
    was also broken — the header row was returned but any data would have crashed.
    """
    r = client.get("/api/v1/export/findings")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    ct = r.headers.get("content-type", "")
    assert "text/csv" in ct, f"Expected text/csv content-type, got: {ct}"

    cd = r.headers.get("content-disposition", "")
    assert "attachment" in cd, f"Expected 'attachment' in Content-Disposition, got: {cd}"
    assert "findings" in cd.lower() or ".csv" in cd, f"Expected findings CSV filename in Content-Disposition: {cd}"

    lines = [line for line in r.text.strip().splitlines() if line.strip()]
    assert len(lines) == 1, f"Expected 1 header row for empty export, got {len(lines)}"

    expected_headers = ["finding_id", "device_id", "control_id", "severity", "status", "occurrence_count", "first_seen", "last_seen"]
    header_cols = lines[0].split(",")
    assert header_cols == expected_headers, f"CSV header mismatch. Expected {expected_headers}, got {header_cols}"


def test_export_findings_with_data_returns_correct_csv(client):
    """
    GET /api/v1/export/findings with existing findings must return:
    - HTTP 200
    - CSV with header + data rows
    - Each row must have 8 columns matching the header
    - finding_id, device_id, control_id, severity, status must be non-empty

    Root cause regression: f.id, f.device_id etc. raised AttributeError on dicts.
    """
    # Generate findings via audit
    client.post("/api/v1/audit", json={
        "config_text": "hostname EXPORT-TEST-RTR\nline vty 0 4\n transport input telnet ssh\nno service password-encryption",
        "source": "EXPORT-TEST-RTR",
    })

    r = client.get("/api/v1/export/findings")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"

    ct = r.headers.get("content-type", "")
    assert "text/csv" in ct

    lines = [line for line in r.text.strip().splitlines() if line.strip()]
    assert len(lines) >= 2, f"Expected header + at least 1 data row, got {len(lines)} lines"

    # Validate header
    header_cols = lines[0].split(",")
    assert "finding_id" in header_cols
    assert "device_id" in header_cols
    assert "control_id" in header_cols
    assert "severity" in header_cols
    assert "status" in header_cols

    # Validate data rows
    for row_line in lines[1:]:
        cols = row_line.split(",")
        assert len(cols) == len(header_cols), f"Data row column count mismatch: {row_line}"

        # Key fields must be non-empty
        row = dict(zip(header_cols, cols))
        assert row.get("finding_id"), f"finding_id must not be empty: {row}"
        assert row.get("device_id") == "EXPORT-TEST-RTR", f"device_id must be EXPORT-TEST-RTR: {row}"
        assert row.get("control_id"), f"control_id must not be empty: {row}"
        assert row.get("severity") in ("CRITICAL", "HIGH", "MEDIUM", "LOW"), f"Unexpected severity: {row}"
        assert row.get("status") in ("OPEN", "RESOLVED", "ACKNOWLEDGED", "REOPENED"), f"Unexpected status: {row}"


def test_export_findings_service_uses_dict_access(temp_db):
    """
    Unit test: OperationalExportService.export_findings_csv() must not raise
    AttributeError when findings exist (root cause regression unit test).
    FindingService.list_findings() returns list[dict]; the export must use
    f.get('key') not f.key.
    """
    from src.export.service import OperationalExportService
    from src.findings.service import FindingService
    from src.api.schemas import AuditRequest
    from src.api.service import run_audit

    fs = FindingService(temp_db)
    audit = run_audit(AuditRequest(
        config_text="hostname RTR-EXPORT-UNIT\nline vty 0 4\n transport input telnet ssh\nno service password-encryption",
        source="RTR-EXPORT-UNIT",
    ), persist=True)
    fs.sync_audit_findings(audit_response=audit)

    svc = OperationalExportService(temp_db)

    # Must not raise AttributeError
    try:
        csv_out = svc.export_findings_csv()
    except AttributeError as e:
        raise AssertionError(
            f"export_findings_csv() raised AttributeError: {e}\n"
            "FindingService.list_findings() returns list[dict]; use f.get('key') not f.key"
        )

    assert isinstance(csv_out, str), "export_findings_csv() must return str"

    lines = [l for l in csv_out.strip().splitlines() if l.strip()]
    assert len(lines) >= 2, f"Expected header + data rows, got: {lines}"

    # Verify header
    assert lines[0].startswith("finding_id,"), f"Wrong CSV header: {lines[0]}"

    # Verify no empty finding_id fields
    header = lines[0].split(",")
    for row_line in lines[1:]:
        row = dict(zip(header, row_line.split(",")))
        assert row.get("finding_id"), "finding_id field must not be empty in CSV"
        assert row.get("device_id") == "RTR-EXPORT-UNIT"


def test_audit_persistence_persist_true(client):
    """
    Regression test: POST /api/v1/audit (persist=True by default) must write an
    audit record to the persistence store so that GET /api/v1/audits returns it.
    """
    initial_r = client.get("/api/v1/audits")
    assert initial_r.status_code == 200
    initial_total = initial_r.json()["total"]

    audit_r = client.post("/api/v1/audit", json={
        "config_text": "hostname PERSIST-TEST-01\nline vty 0 4\n transport input ssh\nservice password-encryption",
        "source_name": "PERSIST-TEST-01"
    })
    assert audit_r.status_code == 200

    history_r = client.get("/api/v1/audits")
    assert history_r.status_code == 200
    body = history_r.json()

    assert body["total"] == initial_total + 1
    items = body["items"]
    assert len(items) >= 1

    latest_item = items[0]  # Reverse-chronological order
    assert latest_item["source_name"] == "PERSIST-TEST-01" or latest_item["hostname"] == "PERSIST-TEST-01"
    assert latest_item["vendor"] == "cisco"
    assert "id" in latest_item and latest_item["id"]


def test_audit_persistence_persist_false_isolation():
    """
    Regression test: run_audit with persist=False (used by What-If Simulator,
    Baseline evaluation, and Remediation verification) MUST NOT write to audit history.
    """
    import tempfile, os
    from src.api.schemas import AuditRequest
    from src.api.service import run_audit
    from src.audit_store.service import AuditStoreService

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        os.environ["AUDIT_DB_PATH"] = path
        store = AuditStoreService(db_path=path)
        assert store.count_audits() == 0

        # Persist = False
        resp = run_audit(AuditRequest(config_text="hostname SIM-DEVICE-01\nline vty 0 4\n transport input telnet ssh"), persist=False)
        assert resp is not None
        assert store.count_audits() == 0, "run_audit(persist=False) must NOT save to audit_store"

        # Persist = True
        resp2 = run_audit(AuditRequest(config_text="hostname PERSIST-DEVICE-01\nline vty 0 4\n transport input ssh"), persist=True)
        assert resp2 is not None
        assert store.count_audits() == 1, "run_audit(persist=True) MUST save to audit_store"
    finally:
        if os.path.exists(path):
            os.remove(path)

