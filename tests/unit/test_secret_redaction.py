"""
tests/unit/test_secret_redaction.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comprehensive Secret Redaction & Data Exposure Audit Regression Tests.
Verifies that sensitive credentials (passwords, enable secrets, SNMP community strings,
Bearer tokens, and API secret keys) NEVER appear in:
1. Webhook payloads
2. CSV exports
3. PDF/HTML reports
4. LLM provider inputs
5. Application log / audit trail entries
"""

import json
import os
import tempfile
import pytest

from src.mapping.redaction import redact_secrets
from src.export.service import OperationalExportService, WebhookService
from src.reporting.report_generator import generate_html_report
from src.reporting.pdf_generator import generate_pdf_report
from src.api.schemas import AuditRequest
from src.api.service import run_audit
from src.security.audit_trail import AuditTrailService
from src.mapping.llm_provider import sanitize_llm_prompt


@pytest.fixture
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_redact_secrets_comprehensive_patterns():
    """Verify all credential types are replaced with structural placeholders."""
    raw_config = (
        "username admin password SuperSecret123\n"
        "enable secret VerySecret456\n"
        "snmp-server community PublicSecret789 RO\n"
        "Authorization: Bearer fake-secret-token-12345\n"
        "api_key: sk-proj-super-secret-key-123\n"
        "secret_key: cisco123"
    )

    sanitized = redact_secrets(raw_config)

    assert "SuperSecret123" not in sanitized
    assert "VerySecret456" not in sanitized
    assert "PublicSecret789" not in sanitized
    assert "fake-secret-token-12345" not in sanitized
    assert "sk-proj-super-secret-key-123" not in sanitized
    assert "cisco123" not in sanitized

    assert "[REDACTED_SECRET]" in sanitized
    assert "[REDACTED_COMMUNITY]" in sanitized
    assert "[REDACTED_TOKEN]" in sanitized


def test_webhook_payload_redaction():
    """Verify webhook payloads scrub all secret fields including secret_key."""
    svc = WebhookService()
    payload = {
        "event": "finding.created",
        "secret_key": "cisco123",
        "api_token": "Bearer fake-secret-token-999",
        "detail": "username admin password SuperSecret123",
    }

    evt = svc.dispatch_event("finding.created", payload)
    json_str = json.dumps(evt)

    assert "cisco123" not in json_str
    assert "fake-secret-token-999" not in json_str
    assert "SuperSecret123" not in json_str

    assert evt["payload"]["secret_key"] == "[REDACTED_SECRET]"
    assert "[REDACTED_TOKEN]" in evt["payload"]["api_token"]
    assert "[REDACTED_SECRET]" in evt["payload"]["detail"]


def test_csv_export_redaction(temp_db_path):
    """Verify CSV export methods return redacted secret data."""
    export_svc = OperationalExportService(db_path=temp_db_path)

    # Populate an audit with config containing secrets
    audit_resp = run_audit(AuditRequest(
        config_text="hostname RTR-SECRET-TEST\nusername admin password SuperSecret123\nenable secret VerySecret456\nsnmp-server community PublicSecret789\nline vty 0 4\n transport input telnet ssh",
        source_name="RTR-SECRET-TEST",
    ), persist=True)

    from src.findings.service import FindingService
    fs = FindingService(temp_db_path)
    fs.sync_audit_findings(audit_response=audit_resp)

    csv_devices = export_svc.export_devices_csv()
    csv_findings = export_svc.export_findings_csv()

    assert "SuperSecret123" not in csv_devices
    assert "VerySecret456" not in csv_devices
    assert "PublicSecret789" not in csv_devices

    assert "SuperSecret123" not in csv_findings
    assert "VerySecret456" not in csv_findings
    assert "PublicSecret789" not in csv_findings


def test_html_and_pdf_report_redaction(temp_db_path):
    """Verify HTML and PDF executive reports sanitize evidence and remediation hints."""
    audit_resp = run_audit(AuditRequest(
        config_text="hostname RTR-REPORT-TEST\nusername admin password SuperSecret123\nline vty 0 4\n transport input telnet ssh\n no service password-encryption",
        source_name="RTR-REPORT-TEST",
    ), persist=True)

    html_out = generate_html_report(audit_resp, "audit-123")
    pdf_bytes = generate_pdf_report(audit_resp, "audit-123")

    assert "SuperSecret123" not in html_out
    assert b"SuperSecret123" not in pdf_bytes


def test_llm_provider_prompt_redaction():
    """Verify LLM prompt sanitizer strips raw secrets before inserting into LLM prompt."""
    raw_directive = "username admin password SuperSecret123 enable secret VerySecret456"
    sanitized_prompt = sanitize_llm_prompt(raw_directive)

    assert "SuperSecret123" not in sanitized_prompt
    assert "VerySecret456" not in sanitized_prompt
    assert "[REDACTED_SECRET]" in sanitized_prompt


def test_audit_trail_logging_redaction(temp_db_path):
    """Verify AuditTrailService redacts state changes before logging."""
    trail_svc = AuditTrailService(db_path=temp_db_path)
    trail_svc.log_action(
        actor="admin",
        operation="UPDATE_CONFIG",
        before_state={"config": "username admin password OldSecret123"},
        after_state={"config": "username admin password SuperSecret123"},
    )

    logs = trail_svc.get_recent_logs()
    assert len(logs) == 1
    log_entry = logs[0]

    json_str = json.dumps(log_entry)
    assert "OldSecret123" not in json_str
    assert "SuperSecret123" not in json_str
    assert "[REDACTED_SECRET]" in json_str
