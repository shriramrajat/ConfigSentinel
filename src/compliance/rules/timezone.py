"""TIME-001: System timezone must be configured."""

from __future__ import annotations

from src.compliance.model import ComplianceResult, ComplianceStatus, Evidence, Remediation, Severity
from src.compliance.rules.base import ComplianceRule, SecurityControl
from src.normalization.model import NormalizedConfig

_CONTROL = SecurityControl(
    control_id="TIME-001",
    control_name="System Timezone Must Be Configured",
    description=(
        "Devices must have an explicit timezone configured for accurate log "
        "timestamps. Devices without a timezone may produce inconsistent "
        "log entries, complicating incident response and forensic analysis."
    ),
    severity=Severity.LOW,
    framework_refs=(
        "CIS-IOS-L1-3.3.2",
        "NIST-AU-8",
    ),
    applicable_vendors=frozenset({"cisco", "juniper"}),
)

_CISCO_REMEDIATION = Remediation(
    vendor="cisco",
    guidance="Configure an explicit timezone. UTC is recommended for consistency.",
    config_hint="clock timezone UTC 0",
)

_JUNIPER_REMEDIATION = Remediation(
    vendor="juniper",
    guidance="Configure a timezone under system. UTC is recommended.",
    config_hint="set system time-zone UTC",
)


class TimezoneRule(ComplianceRule):
    """Evaluate TIME-001 for Cisco IOS/IOS-XE and Juniper JunOS."""

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
        clock_items = [
            item for item in config.global_items
            if item.key.lower() == "clock"
            and item.value is not None
            and item.value.lower().startswith("timezone")
        ]
        if clock_items:
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, None,
                    tuple(i.raw_line for i in clock_items),
                    clock_items[0].value,
                    "Timezone configured",
                    f"Timezone is configured: '{clock_items[0].value}'.",
                    line_number=clock_items[0].line_number,
                )],
            )
        return self._build_result(
            config,
            ComplianceStatus.FAIL,
            [Evidence(
                self.control.control_id, None, (), None,
                "clock timezone <ZONE> <offset>",
                "No clock timezone directive was found.",
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
                    "system time-zone",
                    "No system section found; timezone cannot be verified.",
                )],
                _JUNIPER_REMEDIATION,
            )
        tz_items = [
            item for item in system.items
            if item.key.lower() == "time-zone"
        ]
        if tz_items:
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, "system",
                    tuple(i.raw_line for i in tz_items),
                    tz_items[0].value,
                    "Timezone configured",
                    f"Timezone configured: '{tz_items[0].value}'.",
                    line_number=tz_items[0].line_number,
                )],
            )
        return self._build_result(
            config,
            ComplianceStatus.FAIL,
            [Evidence(
                self.control.control_id, "system", (), None,
                "time-zone UTC",
                "No time-zone directive found under system.",
            )],
            _JUNIPER_REMEDIATION,
        )
