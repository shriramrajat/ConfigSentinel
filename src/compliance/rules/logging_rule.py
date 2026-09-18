"""LOG-001: Logging must be enabled and directed to a syslog server."""

from __future__ import annotations

from src.compliance.model import ComplianceResult, ComplianceStatus, Evidence, Remediation, Severity
from src.compliance.rules.base import ComplianceRule, SecurityControl
from src.normalization.model import NormalizedConfig

_CONTROL = SecurityControl(
    control_id="LOG-001",
    control_name="Logging Must Be Enabled and Directed to a Syslog Server",
    description=(
        "Centralized logging is required for security monitoring, incident response, "
        "and audit trails. Devices must send logs to an external syslog server."
    ),
    severity=Severity.MEDIUM,
    framework_refs=(
        "CIS-IOS-L1-5.1",
        "NIST-AU-3",
        "NIST-AU-9",
        "DISA-STIG-NET-LOG-001",
    ),
    applicable_vendors=frozenset({"cisco", "juniper"}),
)

_CISCO_REMEDIATION = Remediation(
    vendor="cisco",
    guidance="Enable logging and direct it to an external syslog server.",
    config_hint="logging host <syslog-ip>\nlogging trap informational\nlogging on",
)

_JUNIPER_REMEDIATION = Remediation(
    vendor="juniper",
    guidance="Configure syslog under system syslog to direct logs to an external host.",
    config_hint="set system syslog host <syslog-ip> any any",
)


class LoggingRule(ComplianceRule):
    """Evaluate LOG-001 for Cisco IOS/IOS-XE and Juniper JunOS."""

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
        # Check for 'logging host' directive
        logging_hosts = [
            item for item in config.global_items
            if item.key.lower() == "logging"
            and item.value is not None
            and item.value.lower().startswith("host")
        ]
        # Check for 'no logging on'
        no_logging = [
            item for item in config.global_items
            if item.key.lower() == "no"
            and item.value is not None
            and item.value.lower() == "logging on"
        ]
        if no_logging:
            return self._build_result(
                config,
                ComplianceStatus.FAIL,
                [Evidence(
                    self.control.control_id, None,
                    tuple(i.raw_line for i in no_logging),
                    "logging disabled",
                    "logging on with external host",
                    "Logging is explicitly disabled via 'no logging on'.",
                    line_number=no_logging[0].line_number,
                )],
                _CISCO_REMEDIATION,
            )
        if logging_hosts:
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, None,
                    tuple(i.raw_line for i in logging_hosts),
                    f"{len(logging_hosts)} syslog host(s) configured",
                    "At least one logging host",
                    f"Logging directed to {len(logging_hosts)} external host(s).",
                    line_number=logging_hosts[0].line_number,
                )],
            )
        return self._build_result(
            config,
            ComplianceStatus.FAIL,
            [Evidence(
                self.control.control_id, None, (), None,
                "logging host <syslog-ip>",
                "No external syslog server is configured.",
            )],
            _CISCO_REMEDIATION,
        )

    def _evaluate_juniper(self, config: NormalizedConfig) -> ComplianceResult:
        system = config.get_section("system")
        if system is None:
            return self._build_result(
                config,
                ComplianceStatus.NEEDS_REVIEW,
                [Evidence(
                    self.control.control_id, None, (), None,
                    "system syslog host <ip>",
                    "No system section found; logging configuration cannot be verified.",
                )],
                _JUNIPER_REMEDIATION,
            )
        syslog_items = [
            item for item in system.items
            if "syslog" in item.path
        ]
        if syslog_items:
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, "system",
                    tuple(i.raw_line for i in syslog_items),
                    f"{len(syslog_items)} syslog directive(s)",
                    "Syslog configured",
                    f"Found {len(syslog_items)} syslog directive(s) under system.",
                    line_number=syslog_items[0].line_number,
                )],
            )
        return self._build_result(
            config,
            ComplianceStatus.FAIL,
            [Evidence(
                self.control.control_id, "system", (), None,
                "system syslog host <ip> any any",
                "No syslog configuration found under system section.",
            )],
            _JUNIPER_REMEDIATION,
        )
