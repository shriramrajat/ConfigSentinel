"""SNMP-001: SNMP must use SNMPv3 or have no default communities."""

from __future__ import annotations

from src.compliance.model import ComplianceResult, ComplianceStatus, Evidence, Remediation, Severity
from src.compliance.rules.base import ComplianceRule, SecurityControl
from src.normalization.model import NormalizedConfig

_CONTROL = SecurityControl(
    control_id="SNMP-001",
    control_name="SNMP Default Communities Must Not Be Used",
    description=(
        "Default SNMP community strings ('public' and 'private') are well-known "
        "and provide unauthenticated read or read-write access to device MIBs. "
        "They must be removed or SNMPv3 with authentication must be required."
    ),
    severity=Severity.HIGH,
    framework_refs=(
        "CIS-IOS-L1-4.1",
        "NIST-CM-6",
        "NIST-IA-3",
        "DISA-STIG-NET-SNMP-001",
    ),
    applicable_vendors=frozenset({"cisco", "juniper"}),
)

_CISCO_REMEDIATION = Remediation(
    vendor="cisco",
    guidance=(
        "Remove default SNMP community strings 'public' and 'private'. "
        "Use SNMPv3 with authentication and privacy. "
        "If SNMPv2 is required, use strong non-default community strings."
    ),
    config_hint=(
        "no snmp-server community public\n"
        "no snmp-server community private\n"
        "snmp-server group <GROUP> v3 priv\n"
        "snmp-server user <USER> <GROUP> v3 auth sha <PASS> priv aes 128 <PASS>"
    ),
)

_JUNIPER_REMEDIATION = Remediation(
    vendor="juniper",
    guidance=(
        "Remove default SNMP community strings. Use SNMPv3 with authentication."
    ),
    config_hint=(
        "delete snmp community public\n"
        "delete snmp community private\n"
        "set snmp v3 usm local-engine user <USER> authentication-sha authentication-password <PASS>"
    ),
)

_DEFAULT_COMMUNITIES = frozenset({"public", "private"})


class SnmpRule(ComplianceRule):
    """Evaluate SNMP-001 for Cisco IOS/IOS-XE and Juniper JunOS."""

    control = _CONTROL

    def evaluate(self, config: NormalizedConfig) -> ComplianceResult:
        if not self.control.applies_to(config.vendor):
            return self._not_applicable(config)
        if config.vendor == "cisco":
            return self._evaluate_cisco(config)
        if config.vendor == "juniper":
            return self._evaluate_juniper(config)
        return self._not_applicable(config)

    def _evaluate_cisco(self, config: NormalizedConfig) -> ComplianceResult:
        snmp_items = [
            item for item in config.global_items
            if item.key.lower() == "snmp-server"
            and item.value is not None
            and item.value.lower().startswith("community")
        ]
        if not snmp_items:
            # No SNMP configured — SNMP disabled is acceptable
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, None, (), None,
                    "No default community strings",
                    "No SNMP community strings configured — SNMP appears to be disabled.",
                )],
            )
        bad_items = [
            item for item in snmp_items
            if any(
                f"community {c}" in item.value.lower()
                for c in _DEFAULT_COMMUNITIES
            )
        ]
        if bad_items:
            return self._build_result(
                config,
                ComplianceStatus.FAIL,
                [Evidence(
                    self.control.control_id, None,
                    tuple(i.raw_line for i in bad_items),
                    "Default community strings in use",
                    "No default community strings (public/private)",
                    f"Found {len(bad_items)} default SNMP community string(s).",
                    line_number=bad_items[0].line_number,
                )],
                _CISCO_REMEDIATION,
            )
        return self._build_result(
            config,
            ComplianceStatus.PASS,
            [Evidence(
                self.control.control_id, None,
                tuple(i.raw_line for i in snmp_items),
                "Custom community strings in use",
                "No default community strings",
                "SNMP community strings are configured and do not use default values.",
                line_number=snmp_items[0].line_number,
            )],
        )

    def _evaluate_juniper(self, config: NormalizedConfig) -> ComplianceResult:
        snmp_section = config.get_section("snmp")
        if snmp_section is None:
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, None, (), None,
                    "No SNMP section",
                    "No SNMP section found — SNMP appears to be disabled.",
                )],
            )
        community_items = [
            item for item in snmp_section.items
            if item.key.lower() in _DEFAULT_COMMUNITIES
        ]
        if community_items:
            return self._build_result(
                config,
                ComplianceStatus.FAIL,
                [Evidence(
                    self.control.control_id, "snmp",
                    tuple(i.raw_line for i in community_items),
                    "Default community strings in use",
                    "No default community strings",
                    f"Found {len(community_items)} default SNMP community string(s).",
                    line_number=community_items[0].line_number,
                )],
                _JUNIPER_REMEDIATION,
            )
        return self._build_result(
            config,
            ComplianceStatus.PASS,
            [Evidence(
                self.control.control_id, "snmp", (), None,
                "No default community strings",
                "SNMP section found without default community strings.",
            )],
        )
