"""
fleet.service
~~~~~~~~~~~~~

Fleet-Wide Security Posture Metrics Aggregation Service.
"""

from __future__ import annotations

import os
from pathlib import Path
from src.findings.service import FindingService
from src.inventory.model import DevicePostureStatus
from src.inventory.service import DeviceInventoryService


class FleetPostureService:
    """Aggregates metrics and posture analysis across the entire fleet."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))
        self.inventory_svc = DeviceInventoryService(db_path=db_path)
        self.finding_svc = FindingService(db_path=db_path)

    def get_fleet_posture_overview(self) -> dict:
        """Calculate aggregate fleet metrics."""
        devices = self.inventory_svc.list_devices()
        total_devices = len(devices)

        healthy_count = sum(1 for d in devices if d.current_posture == DevicePostureStatus.HEALTHY)
        attention_count = sum(1 for d in devices if d.current_posture == DevicePostureStatus.NEEDS_ATTENTION)
        critical_count = sum(1 for d in devices if d.current_posture == DevicePostureStatus.CRITICAL)
        unknown_count = sum(1 for d in devices if d.current_posture == DevicePostureStatus.UNKNOWN)

        all_open_findings = self.finding_svc.list_findings(status="OPEN")
        critical_findings_count = sum(1 for f in all_open_findings if f.get("severity", "").upper() == "CRITICAL")
        high_findings_count = sum(1 for f in all_open_findings if f.get("severity", "").upper() == "HIGH")

        vendor_breakdown: dict[str, int] = {}
        env_breakdown: dict[str, int] = {}

        for d in devices:
            v = d.vendor.lower()
            vendor_breakdown[v] = vendor_breakdown.get(v, 0) + 1
            e = d.environment.upper()
            env_breakdown[e] = env_breakdown.get(e, 0) + 1

        return {
            "total_devices": total_devices,
            "healthy_devices": healthy_count,
            "needs_attention_devices": attention_count,
            "critical_devices": critical_count,
            "unknown_posture_devices": unknown_count,
            "total_open_findings": len(all_open_findings),
            "open_critical_findings": critical_findings_count,
            "open_high_findings": high_findings_count,
            "vendor_distribution": vendor_breakdown,
            "environment_distribution": env_breakdown,
        }
