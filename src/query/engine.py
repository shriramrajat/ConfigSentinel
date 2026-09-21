"""
query.engine
~~~~~~~~~~~~

Bounded Natural Language Query Execution Engine.

Security Boundary:
- Translates natural language into a strict Pydantic StructuredQuerySchema.
- NEVER generates or executes raw dynamic SQL strings.
- Specifically detects and neutralizes SQL-like input (DDL, DML, SQL injection fragments).
- If no bounded filter or intent can be extracted, returns zero matched records
  rather than running an unfiltered query.
- Parameterized deterministic query execution only through predefined service methods.
"""

from __future__ import annotations

import os
import re
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
        """Parse natural language into a strict StructuredQuerySchema.

        Security Boundary:
        - Input is checked for SQL injection primitives. Any SQL DDL/DML pattern
          returns a clean, empty (all-None) StructuredQuerySchema.
        - Only predefined fields (intent_id, control_id, status, severity, vendor, environment, device_id, keyword)
          can be populated.
        """
        if not nl_query or not nl_query.strip():
            return StructuredQuerySchema()

        q_raw = nl_query.strip()
        q_lower = q_raw.lower()

        # 1. SQL Injection / SQL Fragment Detection Guard
        sql_patterns = [
            r"\bdrop\b",
            r"\bselect\b",
            r"\binsert\b",
            r"\bupdate\b",
            r"\bdelete\b",
            r"\bunion\b",
            r"\balter\b",
            r"\bcreate\b",
            r"\btruncate\b",
            r"\bexec\b",
            r"\bexecute\b",
            r"\bfrom\b",
            r"\bwhere\b",
            r"\bgroup\s+by\b",
            r"\border\s+by\b",
            r"\bhaving\b",
            r"--",
            r";",
            r"/\*",
            r"\*/",
            r"\b1\s*=\s*1\b",
            r"\bor\b\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, q_lower):
                # Malicious or SQL-like query detected -> return all-None schema safely
                return StructuredQuerySchema()

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

        # 2. Intent & Control ID detection
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

        # Direct Control ID regex matching (e.g. TLN-001, SSH-001, PWD-001, AAA-001)
        control_match = re.search(r"\b([a-zA-Z]{3}-\d{3})\b", q_raw)
        if control_match:
            schema_dict["control_id"] = control_match.group(1).upper()

        # 3. Severity detection
        if "critical" in q_lower:
            schema_dict["severity"] = "CRITICAL"
        elif "high" in q_lower:
            schema_dict["severity"] = "HIGH"
        elif "medium" in q_lower:
            schema_dict["severity"] = "MEDIUM"
        elif "low" in q_lower:
            schema_dict["severity"] = "LOW"

        # 4. Status detection
        if any(w in q_lower for w in ["open", "failing", "failed", "fail"]):
            schema_dict["status"] = "FAIL"
        elif any(w in q_lower for w in ["pass", "passing", "compliant"]):
            schema_dict["status"] = "PASS"

        # 5. Vendor detection
        for v in ["cisco", "juniper", "arista", "fortinet", "panos"]:
            if v in q_lower:
                schema_dict["vendor"] = v
                break

        # 6. Environment detection
        if "production" in q_lower or "prod" in q_lower:
            schema_dict["environment"] = "PRODUCTION"
        elif "dmz" in q_lower:
            schema_dict["environment"] = "DMZ"
        elif "lab" in q_lower:
            schema_dict["environment"] = "LAB"
        elif "staging" in q_lower:
            schema_dict["environment"] = "STAGING"

        # 7. Safe Keyword extraction (if no structural filter was matched)
        has_structural_filter = any(
            v is not None for k, v in schema_dict.items() if k != "keyword"
        )
        if not has_structural_filter:
            kw_match = re.search(r"\bkeyword\s+([a-zA-Z0-9_\-]+)\b", q_lower)
            if kw_match:
                schema_dict["keyword"] = kw_match.group(1)
            else:
                stop_words = {
                    "show", "me", "find", "list", "search", "get", "query", "all",
                    "devices", "device", "findings", "finding", "with", "the", "and",
                    "for", "has", "have", "that", "are", "is", "in", "of", "to", "on"
                }
                words = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]+\b", q_lower) if len(w) >= 3 and w not in stop_words]
                if len(words) == 1:
                    schema_dict["keyword"] = words[0]

        return StructuredQuerySchema(**schema_dict)

    def execute_bounded_query(self, nl_query: str) -> dict:
        """Process natural language query safely and return matching device and finding records.

        Security Invariant:
        - If query has no recognized bounded filters (or contains SQL patterns),
          return zero matched records (0 devices, 0 findings) to prevent data leaks.
        - Database access is strictly parameterized via existing service methods.
        """
        parsed_schema = self.parse_natural_language_query(nl_query)

        schema_dict = parsed_schema.model_dump()
        has_active_filters = any(v is not None for v in schema_dict.values())

        if not has_active_filters:
            # Unrecognized, empty, or malicious query -> return 0 matched devices & 0 matched findings
            return {
                "query": nl_query,
                "parsed_schema": schema_dict,
                "matched_devices": [],
                "matched_findings": [],
            }

        # Safe parameterized execution via existing deterministic services
        devices = self.inventory_svc.list_devices(
            vendor=parsed_schema.vendor,
            environment=parsed_schema.environment,
            search=parsed_schema.keyword,
        )

        findings = self.finding_svc.list_findings(
            severity=parsed_schema.severity,
            status="OPEN" if parsed_schema.status in ("FAIL", "OPEN") else None,
        )

        if parsed_schema.vendor:
            findings = [f for f in findings if self._finding_matches_vendor(f, parsed_schema.vendor, devices)]

        if parsed_schema.control_id:
            findings = [f for f in findings if f.get("control_id") == parsed_schema.control_id]

        matched_device_ids = {f.get("device_id") for f in findings}

        # Filter devices to those matching findings if specific control/severity/status was requested
        if parsed_schema.control_id or parsed_schema.severity or parsed_schema.status:
            devices = [d for d in devices if d.device_id in matched_device_ids or d.hostname in matched_device_ids]

        return {
            "query": nl_query,
            "parsed_schema": schema_dict,
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

    def _finding_matches_vendor(self, finding: dict, vendor: str, devices: list) -> bool:
        dev_id = finding.get("device_id")
        if not dev_id:
            return False
        for d in devices:
            if (d.device_id == dev_id or d.hostname == dev_id) and d.vendor.lower() == vendor.lower():
                return True
        return False

