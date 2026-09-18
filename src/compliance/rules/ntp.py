"""NTP-001: NTP server must be configured for time synchronization."""

from __future__ import annotations

from src.compliance.model import ComplianceResult, ComplianceStatus, Evidence, Remediation, Severity
from src.compliance.rules.base import ComplianceRule, SecurityControl
from src.normalization.model import NormalizedConfig

_CONTROL = SecurityControl(
    control_id="NTP-001",
    control_name="NTP Server Must Be Configured",
    description=(
        "Network devices must synchronize their clocks with a reliable NTP server. "
        "Accurate time is required for log correlation, certificate validation, and "
        "forensic investigation."
    ),
    severity=Severity.MEDIUM,
    framework_refs=(
        "CIS-IOS-L1-3.3.1",
        "NIST-AU-8",
        "DISA-STIG-NET-001",
    ),
    applicable_vendors=frozenset({"cisco", "juniper"}),
)

_CISCO_REMEDIATION = Remediation(
    vendor="cisco",
    guidance="Configure at least one NTP server. Prefer authenticated NTP.",
    config_hint="ntp server <ip-address>\nntp authenticate",
)

_JUNIPER_REMEDIATION = Remediation(
    vendor="juniper",
    guidance="Configure at least one NTP server under system ntp.",
    config_hint="set system ntp server <ip-address>",
)


class NtpRule(ComplianceRule):
    """Evaluate NTP-001 for Cisco IOS/IOS-XE and Juniper JunOS."""

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
        ntp_items = [
            item for item in config.global_items
            if item.key.lower() == "ntp"
            and item.value is not None
            and item.value.lower().startswith("server")
        ]
        if ntp_items:
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, None,
                    tuple(i.raw_line for i in ntp_items),
                    f"{len(ntp_items)} NTP server(s) configured",
                    "At least one NTP server",
                    f"Found {len(ntp_items)} NTP server directive(s).",
                    line_number=ntp_items[0].line_number,
                )],
            )
        return self._build_result(
            config,
            ComplianceStatus.FAIL,
            [Evidence(
                self.control.control_id, None, (), None,
                "ntp server <ip-address>",
                "No NTP server directive was found in the global configuration.",
            )],
            _CISCO_REMEDIATION,
        )

    def _evaluate_juniper(self, config: NormalizedConfig) -> ComplianceResult:
        system = config.get_section("system")
        if system is None:
            return self._build_result(
                config,
                ComplianceStatus.FAIL,
                [Evidence(
                    self.control.control_id, None, (), None,
                    "system ntp server <ip>",
                    "No system section found; NTP configuration cannot be verified.",
                )],
                _JUNIPER_REMEDIATION,
            )
        ntp_items = [
            item for item in system.items
            if item.key.lower() == "server"
            and "ntp" in item.path
        ]
        if not ntp_items:
            # Broaden: look for any 'ntp' subsection item
            ntp_items = [
                item for item in system.items
                if "ntp" in item.path
            ]
        if ntp_items:
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, "system",
                    tuple(i.raw_line for i in ntp_items),
                    f"{len(ntp_items)} NTP server(s) configured",
                    "At least one NTP server",
                    f"Found {len(ntp_items)} NTP directive(s) under system ntp.",
                    line_number=ntp_items[0].line_number,
                )],
            )
        return self._build_result(
            config,
            ComplianceStatus.NEEDS_REVIEW,
            [Evidence(
                self.control.control_id, "system", (), None,
                "system ntp server <ip>",
                "No NTP server entries found under system section; path tracking may be incomplete.",
            )],
            _JUNIPER_REMEDIATION,
        )
