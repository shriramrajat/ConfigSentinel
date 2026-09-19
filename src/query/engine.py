"""
query.engine
~~~~~~~~~~~~

Bounded Natural Language Query Execution Engine.

Security Boundary:
- Translates natural language into a strict Pydantic StructuredQuerySchema.
- NEVER generates or executes raw dynamic SQL strings.
- Parameterized deterministic query execution only.
"""

from __future__ import annotations

import os
from pathlib import Path
from src.findings.service import FindingService
from src.inventory.service import DeviceInventoryService
from src.query.schema import StructuredQuerySchema


class NaturalLanguageQueryEngine:
    """Bounded query translation and deterministic result fetcher."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = os.getenv("AUDIT_DB_PATH", str(Path(__file__).parent.parent.parent / "audits.db"))
        self.inventory_svc = DeviceInventoryService(db_path=db_path)
        self.finding_svc = FindingService(db_path=db_path)

    def parse_natural_language_query(self, nl_query: str) -> StructuredQuerySchema:
        """Parse natural language into a strict StructuredQuerySchema."""
        q_lower = nl_query.lower().strip()

        # Reject obvious SQL injection primitives immediately
        sql_keywords = ["drop", "select ", "insert ", "update ", "delete ", "union", "--", ";", "where 1=1"]
        for kw in sql_keywords:
            if kw in q_lower:
                # Sanitize out malicious tokens
                q_lower = q_lower.replace(kw, "")

        schema_dict: dict[str, str | None] = {
            "intent_id": None,
            "control_id": None,
            "status": None,
            "severity": None,
            "vendor": None,
            "environment": None,
            "device_id": None,
            "keyword": None,
        }

        # Intent detection
        if "telnet" in q_lower:
            schema_dict["intent_id"] = "TELNET_DISABLED"
            schema_dict["control_id"] = "TLN-001"
        elif "ssh" in q_lower:
            schema_dict["intent_id"] = "SSH_VERSION_ENFORCED"
            schema_dict["control_id"] = "SSH-001"
        elif "password" in q_lower or "secret" in q_lower or "encryption" in q_lower:
            schema_dict["intent_id"] = "PASSWORD_ENCRYPTION_ENABLED"
            schema_dict["control_id"] = "PWD-001"
        elif "aaa" in q_lower or "authentication" in q_lower:
            schema_dict["intent_id"] = "AAA_AUTHENTICATION_ENABLED"
            schema_dict["control_id"] = "AAA-001"

        # Severity detection
        if "critical" in q_lower:
            schema_dict["severity"] = "CRITICAL"
        elif "high" in q_lower:
            schema_dict["severity"] = "HIGH"
        elif "medium" in q_lower:
            schema_dict["severity"] = "MEDIUM"

        # Status / Finding state detection
        if "open" in q_lower or "failing" in q_lower or "failed" in q_lower:
            schema_dict["status"] = "FAIL"
        elif "pass" in q_lower or "passing" in q_lower or "compliant" in q_lower:
            schema_dict["status"] = "PASS"

        # Vendor detection
        for v in ["cisco", "juniper", "arista", "fortinet", "panos"]:
            if v in q_lower:
                schema_dict["vendor"] = v
                break

        # Validate with Pydantic
        return StructuredQuerySchema(**schema_dict)

    def execute_bounded_query(self, nl_query: str) -> dict:
        """Process natural language query safely and return matching device and finding records."""
        parsed_schema = self.parse_natural_language_query(nl_query)

        # Execute parameterized deterministic query
        devices = self.inventory_svc.list_devices(
            vendor=parsed_schema.vendor,
            environment=parsed_schema.environment,
        )

        findings = self.finding_svc.list_findings(
            severity=parsed_schema.severity,
            status="OPEN" if parsed_schema.status in ("FAIL", "OPEN") else None,
        )

        if parsed_schema.control_id:
            findings = [f for f in findings if f.get("control_id") == parsed_schema.control_id]

        matched_device_ids = {f.get("device_id") for f in findings}

        # Filter devices to those matching findings if specific control/severity was requested
        if parsed_schema.control_id or parsed_schema.severity:
            devices = [d for d in devices if d.device_id in matched_device_ids or d.hostname in matched_device_ids]

        return {
            "query": nl_query,
            "parsed_schema": parsed_schema.model_dump(),
            "matched_devices": [
                {
                    "device_id": d.device_id,
                    "hostname": d.hostname,
                    "vendor": d.vendor,
                    "environment": d.environment,
                    "posture": d.current_posture,
                }
                for d in devices
            ],
            "matched_findings": [
                {
                    "id": f.get("id"),
                    "device_id": f.get("device_id"),
                    "control_id": f.get("control_id"),
                    "severity": f.get("severity"),
                    "status": f.get("status"),
                }
                for f in findings
            ],
        }
