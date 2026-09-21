"""
export.service
~~~~~~~~~~~~~~

Operational Data Exporters (JSON, CSV, PDF) & Sanitized Webhooks.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from src.findings.service import FindingService
from src.inventory.service import DeviceInventoryService
from src.mapping.redaction import redact_secrets


class OperationalExportService:
    """Export fleet posture, devices, findings, and remediation payloads."""

    def __init__(self, db_path: str) -> None:
        self.inventory_svc = DeviceInventoryService(db_path=db_path)
        self.finding_svc = FindingService(db_path=db_path)

    def export_devices_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["device_id", "hostname", "vendor", "platform", "version", "environment", "posture", "status", "last_seen"])

        for d in self.inventory_svc.list_devices():
            writer.writerow([d.device_id, d.hostname, d.vendor, d.platform, d.version, d.environment, d.current_posture, d.status, d.last_seen])

        return redact_secrets(output.getvalue())

    def export_findings_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["finding_id", "device_id", "control_id", "severity", "status", "occurrence_count", "first_seen", "last_seen"])

        # FindingService.list_findings() returns list[dict] — use dict key access
        for f in self.finding_svc.list_findings():
            writer.writerow([
                f.get("id"),
                f.get("device_id"),
                f.get("control_id"),
                f.get("severity"),
                f.get("status"),
                f.get("occurrence_count"),
                f.get("first_seen"),
                f.get("last_seen"),
            ])

        return redact_secrets(output.getvalue())

    def export_fleet_json(self) -> str:
        devices = [
            {
                "device_id": d.device_id,
                "hostname": d.hostname,
                "vendor": d.vendor,
                "environment": d.environment,
                "posture": d.current_posture,
            }
            for d in self.inventory_svc.list_devices()
        ]
        # FindingService.list_findings() returns list[dict] — use dict key access
        findings = [
            {
                "id": f.get("id"),
                "device_id": f.get("device_id"),
                "control_id": f.get("control_id"),
                "severity": f.get("severity"),
                "status": f.get("status"),
            }
            for f in self.finding_svc.list_findings()
        ]
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "devices": devices,
            "findings": findings,
        }
        return redact_secrets(json.dumps(data, indent=2))


class WebhookService:
    """Sanitized event dispatcher for SIEM/ticketing webhooks."""

    def dispatch_event(self, event_type: str, payload: dict) -> dict:
        """Sanitize payload and format event for webhook transmission."""
        sanitized_json = redact_secrets(json.dumps(payload))
        sanitized_payload = json.loads(sanitized_json)

        return {
            "event_id": f"evt-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": sanitized_payload,
        }
