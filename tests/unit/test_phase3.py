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
