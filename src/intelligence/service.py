"""
intelligence.service
~~~~~~~~~~~~~~~~~~~~

Cross-Vendor Security Intelligence Service.

Responsibilities:
- Maintain vendor-neutral security intent catalog.
- Build dynamic Cross-Vendor Control Coverage Matrix across vendors (Cisco, Juniper, Arista, FortiOS, PAN-OS).
- Translate vendor-neutral security policies into vendor-specific configuration requirements.
- Map audit compliance results to vendor-neutral security intents.
"""

from __future__ import annotations

from src.compliance.model import ComplianceResult, ComplianceStatus
from src.compliance.registry import RULE_REGISTRY
from src.intelligence.model import (
    ImplementationStatus,
    PolicyTranslationResult,
    SecurityIntent,
    SecurityPolicy,
    VendorImplementation,
    VendorPolicyTranslation,
)

# ---------------------------------------------------------------------------
# Canonical Security Intents Registry
# ---------------------------------------------------------------------------

SECURITY_INTENTS: list[SecurityIntent] = [
    SecurityIntent(
        id="SSH_VERSION_ENFORCED",
        name="SSH Protocol Version 2 Enforced",
        category="REMOTE_ACCESS",
        description="Enforce SSH Version 2 for administrative CLI connections; prohibit SSH Version 1.",
        security_domain="Management Plane Security",
        related_control_ids=["SSH-001", "SSH-002", "CIS-IOS-001", "CIS-JUNOS-001", "EOS-SSH-001", "FOS-SSH-001", "PAN-SSH-001"],
    ),
    SecurityIntent(
        id="TELNET_DISABLED",
        name="Telnet Management Disabled",
        category="TELNET_SECURITY",
        description="Disable plaintext Telnet service for VTY and management interfaces.",
        security_domain="Management Plane Security",
        related_control_ids=["TLN-001", "CIS-IOS-002", "CIS-JUNOS-002", "EOS-TLN-001", "FOS-TLN-001", "PAN-TLN-001"],
    ),
    SecurityIntent(
        id="EXEC_TIMEOUT_CONFIGURED",
        name="VTY Idle Session Timeout Configured",
        category="SESSION_TIMEOUT",
        description="Configure automatic logout timeout for inactive administrative sessions (<= 15 minutes).",
        security_domain="Session Management",
        related_control_ids=["TO-001", "CIS-IOS-003", "CIS-JUNOS-003", "EOS-EXEC-001"],
    ),
    SecurityIntent(
        id="PASSWORD_ENCRYPTION_ENABLED",
        name="Privileged Password Hashing Enforced",
        category="PASSWORD_SECURITY",
        description="Prohibit plaintext password storage; enforce strong secret hashing (Secret 5/8 or Argon2/SHA-512).",
        security_domain="Credential Security",
        related_control_ids=["PWD-001", "CIS-IOS-004", "CIS-JUNOS-004", "EOS-PWD-001"],
    ),
    SecurityIntent(
        id="AAA_AUTHENTICATION_ENABLED",
        name="Remote AAA Authentication Enforced",
        category="AAA_AUTHENTICATION",
        description="Require centralized TACACS+/RADIUS or local fallback AAA authentication for administrative login.",
        security_domain="Access Control",
        related_control_ids=["AAA-001", "CIS-IOS-005", "CIS-JUNOS-005", "EOS-AAA-001", "PAN-AAA-001"],
    ),
    SecurityIntent(
        id="HTTP_MANAGEMENT_DISABLED",
        name="Insecure HTTP Web Management Disabled",
        category="HTTP_MANAGEMENT",
        description="Disable unencrypted HTTP web management; require HTTPS or disable web server entirely.",
        security_domain="Management Plane Security",
        related_control_ids=["HTTP-001", "CIS-IOS-006", "CIS-JUNOS-006", "FOS-HTTP-001", "PAN-HTTP-001"],
    ),
    SecurityIntent(
        id="LOGGING_REMOTE_ENABLED",
        name="Centralized Remote Syslog Logging Enabled",
        category="LOGGING",
        description="Configure audit logging to forward events to remote syslog collectors.",
        security_domain="Audit Logging & Traceability",
        related_control_ids=["LOG-001", "CIS-IOS-007", "CIS-JUNOS-007", "FOS-LOG-001", "PAN-LOG-001"],
    ),
    SecurityIntent(
        id="NTP_AUTHENTICATION_ENABLED",
        name="NTP Time Synchronization Enabled",
        category="NTP_TIME_SYNC",
        description="Configure authoritative NTP time synchronization with authentication for audit timestamp accuracy.",
        security_domain="Network Services",
        related_control_ids=["NTP-001", "CIS-IOS-008", "CIS-JUNOS-008", "EOS-NTP-001"],
    ),
    SecurityIntent(
        id="SNMP_COMMUNITY_SECURED",
        name="SNMP v3 or Non-Default Community Enforced",
        category="SNMP_SECURITY",
        description="Disable default public/private SNMP community strings and enforce SNMPv3 encrypted auth.",
        security_domain="Network Management",
        related_control_ids=["SNMP-001", "CIS-IOS-009", "CIS-JUNOS-009"],
    ),
    SecurityIntent(
        id="UNNECESSARY_SERVICES_DISABLED",
        name="Unnecessary Network Services Disabled",
        category="SERVICE_HARDENING",
        description="Disable legacy insecure small servers (finger, echo, chargen, bootp, cdp, lldp).",
        security_domain="System Hardening",
        related_control_ids=["SVC-001", "BAN-001", "TZ-001", "CIS-IOS-010"],
    ),
    SecurityIntent(
        id="BANNER_SECURITY_CONFIGURED",
        name="Security Warning Banner Configured",
        category="BANNER_SECURITY",
        description="Display legal warning login banner informing users of authorized access only.",
        security_domain="Policy & Notice",
        related_control_ids=["CIS-IOS-010", "CIS-JUNOS-010", "EOS-BAN-001"],
    ),
]

# ---------------------------------------------------------------------------
# Vendor Implementation Capabilities Matrix
# ---------------------------------------------------------------------------

VENDOR_IMPLEMENTATIONS: list[VendorImplementation] = [
    # Cisco IOS / IOS-XE
    VendorImplementation("cisco", "IOS-XE", "SSH_VERSION_ENFORCED", ImplementationStatus.SUPPORTED, "ip ssh version 2"),
    VendorImplementation("cisco", "IOS-XE", "TELNET_DISABLED", ImplementationStatus.SUPPORTED, "line vty 0 15\n transport input ssh"),
    VendorImplementation("cisco", "IOS-XE", "EXEC_TIMEOUT_CONFIGURED", ImplementationStatus.SUPPORTED, "exec-timeout 10 0"),
    VendorImplementation("cisco", "IOS-XE", "PASSWORD_ENCRYPTION_ENABLED", ImplementationStatus.SUPPORTED, "service password-encryption\n enable secret <hash>"),
    VendorImplementation("cisco", "IOS-XE", "AAA_AUTHENTICATION_ENABLED", ImplementationStatus.SUPPORTED, "aaa new-model\n aaa authentication login default group radius local"),
    VendorImplementation("cisco", "IOS-XE", "HTTP_MANAGEMENT_DISABLED", ImplementationStatus.SUPPORTED, "no ip http server"),
    VendorImplementation("cisco", "IOS-XE", "LOGGING_REMOTE_ENABLED", ImplementationStatus.SUPPORTED, "logging host 10.0.0.50"),
    VendorImplementation("cisco", "IOS-XE", "NTP_AUTHENTICATION_ENABLED", ImplementationStatus.SUPPORTED, "ntp server 10.0.0.1\n ntp authenticate"),
    VendorImplementation("cisco", "IOS-XE", "SNMP_COMMUNITY_SECURED", ImplementationStatus.SUPPORTED, "no snmp-server community public"),
    VendorImplementation("cisco", "IOS-XE", "BANNER_SECURITY_CONFIGURED", ImplementationStatus.SUPPORTED, "banner motd ^Authorized Access Only^"),

    # Juniper JunOS
    VendorImplementation("juniper", "JunOS", "SSH_VERSION_ENFORCED", ImplementationStatus.SUPPORTED, "set system services ssh protocol-version v2"),
    VendorImplementation("juniper", "JunOS", "TELNET_DISABLED", ImplementationStatus.SUPPORTED, "delete system services telnet"),
    VendorImplementation("juniper", "JunOS", "EXEC_TIMEOUT_CONFIGURED", ImplementationStatus.SUPPORTED, "set system login idle-timeout 15"),
    VendorImplementation("juniper", "JunOS", "PASSWORD_ENCRYPTION_ENABLED", ImplementationStatus.SUPPORTED, "set system root-authentication encrypted-password <hash>"),
    VendorImplementation("juniper", "JunOS", "AAA_AUTHENTICATION_ENABLED", ImplementationStatus.SUPPORTED, "set system authentication-order [ radius local ]"),
    VendorImplementation("juniper", "JunOS", "HTTP_MANAGEMENT_DISABLED", ImplementationStatus.SUPPORTED, "delete system services web-management http"),
    VendorImplementation("juniper", "JunOS", "LOGGING_REMOTE_ENABLED", ImplementationStatus.SUPPORTED, "set system syslog host 10.0.0.50 any notice"),
    VendorImplementation("juniper", "JunOS", "NTP_AUTHENTICATION_ENABLED", ImplementationStatus.SUPPORTED, "set system ntp server 10.0.0.1"),
    VendorImplementation("juniper", "JunOS", "SNMP_COMMUNITY_SECURED", ImplementationStatus.SUPPORTED, "delete snmp community public"),
    VendorImplementation("juniper", "JunOS", "BANNER_SECURITY_CONFIGURED", ImplementationStatus.SUPPORTED, "set system login message \"Authorized Access Only\""),

    # Arista EOS
    VendorImplementation("arista", "EOS", "SSH_VERSION_ENFORCED", ImplementationStatus.SUPPORTED, "management ssh\n  protocol version 2"),
    VendorImplementation("arista", "EOS", "TELNET_DISABLED", ImplementationStatus.SUPPORTED, "no management telnet"),
    VendorImplementation("arista", "EOS", "EXEC_TIMEOUT_CONFIGURED", ImplementationStatus.SUPPORTED, "line vty\n  timeout login 15"),
    VendorImplementation("arista", "EOS", "PASSWORD_ENCRYPTION_ENABLED", ImplementationStatus.SUPPORTED, "enable secret sha512 <hash>"),
    VendorImplementation("arista", "EOS", "AAA_AUTHENTICATION_ENABLED", ImplementationStatus.SUPPORTED, "aaa authentication login default group tacacs+ local"),
    VendorImplementation("arista", "EOS", "HTTP_MANAGEMENT_DISABLED", ImplementationStatus.SUPPORTED, "no management api http-commands\n  no protocol http"),

    # Fortinet FortiOS
    VendorImplementation("fortinet", "FortiOS", "SSH_VERSION_ENFORCED", ImplementationStatus.SUPPORTED, "config system global\n  set admin-ssh-v1 disable\n end"),
    VendorImplementation("fortinet", "FortiOS", "TELNET_DISABLED", ImplementationStatus.SUPPORTED, "config system interface\n  edit port1\n    unset allowaccess telnet\n end"),
    VendorImplementation("fortinet", "FortiOS", "EXEC_TIMEOUT_CONFIGURED", ImplementationStatus.SUPPORTED, "config system global\n  set admintimeout 15\n end"),
    VendorImplementation("fortinet", "FortiOS", "HTTP_MANAGEMENT_DISABLED", ImplementationStatus.SUPPORTED, "config system interface\n  edit port1\n    unset allowaccess http\n end"),

    # Palo Alto PAN-OS
    VendorImplementation("panos", "PAN-OS", "SSH_VERSION_ENFORCED", ImplementationStatus.SUPPORTED, "set deviceconfig system ssh v2-only yes"),
    VendorImplementation("panos", "PAN-OS", "TELNET_DISABLED", ImplementationStatus.SUPPORTED, "set deviceconfig system service disable-telnet yes"),
    VendorImplementation("panos", "PAN-OS", "HTTP_MANAGEMENT_DISABLED", ImplementationStatus.SUPPORTED, "set deviceconfig system service disable-http yes"),
    VendorImplementation("panos", "PAN-OS", "AAA_AUTHENTICATION_ENABLED", ImplementationStatus.SUPPORTED, "set deviceconfig system authentication-profile RAD-PROFILE"),
]

# ---------------------------------------------------------------------------
# Security Policies
# ---------------------------------------------------------------------------

SECURITY_POLICIES: list[SecurityPolicy] = [
    SecurityPolicy(
        id="POL-HARDENED-MGMT",
        name="Disable Insecure Remote Management",
        description="Enforce SSH v2, disable Telnet, disable HTTP web management, and require idle session timeouts.",
        required_intent_ids=["TELNET_DISABLED", "HTTP_MANAGEMENT_DISABLED", "SSH_VERSION_ENFORCED", "EXEC_TIMEOUT_CONFIGURED"],
    ),
    SecurityPolicy(
        id="POL-AAA-IDENTITY",
        name="Centralized AAA & Strong Authentication",
        description="Require centralized TACACS+/RADIUS authentication and strong password hashing.",
        required_intent_ids=["AAA_AUTHENTICATION_ENABLED", "PASSWORD_ENCRYPTION_ENABLED"],
    ),
]


class CrossVendorIntelligenceService:
    """Service providing cross-vendor intent mapping, coverage matrix, and policy translation."""

    def list_intents(self) -> list[dict]:
        """Return vendor-neutral security intent catalog."""
        return [
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "description": i.description,
                "security_domain": i.security_domain,
                "related_control_ids": i.related_control_ids,
            }
            for i in SECURITY_INTENTS
        ]

    def get_coverage_matrix(self, vendor_filter: str | None = None) -> list[dict]:
        """Generate dynamic Cross-Vendor Control Coverage Matrix."""
        matrix: list[dict] = []
        vendors = ["cisco", "juniper", "arista", "fortinet", "panos"]

        if vendor_filter and vendor_filter.lower() in vendors:
            vendors = [vendor_filter.lower()]

        for intent in SECURITY_INTENTS:
            vendor_coverage: dict[str, dict] = {}
            for v in vendors:
                impl = next((i for i in VENDOR_IMPLEMENTATIONS if i.vendor == v and i.intent_id == intent.id), None)
                if impl:
                    vendor_coverage[v] = {
                        "status": impl.implementation_status.value,
                        "syntax": impl.syntax_example,
                        "platform": impl.platform,
                    }
                else:
                    vendor_coverage[v] = {
                        "status": ImplementationStatus.UNSUPPORTED.value,
                        "syntax": None,
                        "platform": "N/A",
                    }

            matrix.append({
                "intent_id": intent.id,
                "intent_name": intent.name,
                "category": intent.category,
                "security_domain": intent.security_domain,
                "related_controls": intent.related_control_ids,
                "vendor_coverage": vendor_coverage,
            })

        return matrix

    def translate_policy(self, policy_id: str, vendor_filter: str | None = None) -> PolicyTranslationResult:
        """Translate vendor-neutral security policy requirements across vendor platforms."""
        policy = next((p for p in SECURITY_POLICIES if p.id == policy_id or p.name.lower() == policy_id.lower()), None)
        if not policy:
            # Fallback policy for custom request
            policy = SecurityPolicy(
                id=policy_id,
                name="Custom Security Policy",
                description="User-requested security policy translation.",
                required_intent_ids=["TELNET_DISABLED", "HTTP_MANAGEMENT_DISABLED", "SSH_VERSION_ENFORCED"],
            )

        vendors = ["cisco", "juniper", "arista", "fortinet", "panos"]
        if vendor_filter and vendor_filter.lower() in vendors:
            vendors = [vendor_filter.lower()]

        translations: list[VendorPolicyTranslation] = []

        for v in vendors:
            supported: list[str] = []
            unsupported: list[str] = []
            guidance: list[dict[str, str]] = []

            for intent_id in policy.required_intent_ids:
                impl = next((i for i in VENDOR_IMPLEMENTATIONS if i.vendor == v and i.intent_id == intent_id), None)
                if impl and impl.implementation_status == ImplementationStatus.SUPPORTED:
                    supported.append(intent_id)
                    guidance.append({
                        "intent_id": intent_id,
                        "syntax": impl.syntax_example or "Vendor-specific directive",
                        "platform": impl.platform,
                    })
                else:
                    unsupported.append(intent_id)
                    guidance.append({
                        "intent_id": intent_id,
                        "syntax": "Vendor implementation unavailable.",
                        "platform": v,
                    })

            translations.append(VendorPolicyTranslation(
                vendor=v,
                supported_intents=supported,
                unsupported_intents=unsupported,
                syntax_guidance=guidance,
            ))

        return PolicyTranslationResult(
            policy_id=policy.id,
            policy_name=policy.name,
            description=policy.description,
            translations=translations,
        )

    def map_results_to_intents(self, compliance_results: list[ComplianceResult]) -> list[dict]:
        """Map vendor-specific compliance results to vendor-neutral security intents."""
        intent_results: list[dict] = []

        for intent in SECURITY_INTENTS:
            matching_results = [r for r in compliance_results if r.control_id in intent.related_control_ids]
            if not matching_results:
                continue

            # Determine aggregate intent status
            has_fail = any(r.status == ComplianceStatus.FAIL for r in matching_results)
            has_pass = any(r.status == ComplianceStatus.PASS for r in matching_results)

            if has_fail:
                aggregate_status = "FAIL"
            elif has_pass:
                aggregate_status = "PASS"
            else:
                aggregate_status = "NOT_APPLICABLE"

            # Aggregate evidence cleanly preserving vendor-specific raw lines
            aggregated_evidence: list[dict] = []
            for r in matching_results:
                for ev in r.evidence:
                    aggregated_evidence.append({
                        "control_id": r.control_id,
                        "section": ev.section_name,
                        "raw_lines": ev.raw_lines,
                        "observed": ev.observed,
                        "note": ev.note,
                    })

            intent_results.append({
                "intent_id": intent.id,
                "intent_name": intent.name,
                "category": intent.category,
                "status": aggregate_status,
                "matching_controls": [r.control_id for r in matching_results],
                "evidence": aggregated_evidence,
            })

        return intent_results
