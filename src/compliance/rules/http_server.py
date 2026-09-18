"""HTTP-001: HTTP management server must be disabled."""

from __future__ import annotations

from src.compliance.model import ComplianceResult, ComplianceStatus, Evidence, Remediation, Severity
from src.compliance.rules.base import ComplianceRule, SecurityControl
from src.normalization.model import NormalizedConfig

_CONTROL = SecurityControl(
    control_id="HTTP-001",
    control_name="HTTP Management Server Must Be Disabled",
    description=(
        "The HTTP management server (ip http server) transmits credentials and "
        "configuration data in plaintext. It must be disabled to prevent "
        "unencrypted administrative access. HTTPS may remain enabled if required."
    ),
    severity=Severity.HIGH,
    framework_refs=(
        "CIS-IOS-L1-1.5.1",
        "NIST-CM-7",
        "DISA-STIG-NET-HTTP-001",
    ),
    applicable_vendors=frozenset({"cisco"}),
)

_CISCO_REMEDIATION = Remediation(
    vendor="cisco",
    guidance=(
        "Disable the HTTP server. Use HTTPS (ip http secure-server) if "
        "web-based management is required."
    ),
    config_hint="no ip http server\nip http secure-server",
)


class HttpServerRule(ComplianceRule):
    """Evaluate HTTP-001 for Cisco IOS/IOS-XE."""

    control = _CONTROL

    def evaluate(self, config: NormalizedConfig) -> ComplianceResult:
        if not self.control.applies_to(config.vendor):
            return self._not_applicable(config)
        return self._evaluate_cisco(config)

    def _evaluate_cisco(self, config: NormalizedConfig) -> ComplianceResult:
        # Look for 'ip http server' (enabled) in global items
        http_enabled = [
            item for item in config.global_items
            if item.key.lower() == "ip"
            and item.value is not None
            and item.value.lower() == "http server"
        ]
        # Look for 'no ip http server' (explicitly disabled)
        http_disabled = [
            item for item in config.global_items
            if item.key.lower() == "no"
            and item.value is not None
            and item.value.lower() == "ip http server"
        ]
        if http_disabled:
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, None,
                    tuple(i.raw_line for i in http_disabled),
                    "HTTP server disabled",
                    "HTTP server disabled",
                    "HTTP server is explicitly disabled with 'no ip http server'.",
                    line_number=http_disabled[0].line_number,
                )],
            )
        if http_enabled:
            return self._build_result(
                config,
                ComplianceStatus.FAIL,
                [Evidence(
                    self.control.control_id, None,
                    tuple(i.raw_line for i in http_enabled),
                    "HTTP server enabled",
                    "HTTP server disabled",
                    "HTTP server is enabled — plaintext management access is possible.",
                    line_number=http_enabled[0].line_number,
                )],
                _CISCO_REMEDIATION,
            )
        # Neither explicitly enabled nor disabled: IOS default is disabled
        return self._build_result(
            config,
            ComplianceStatus.PASS,
            [Evidence(
                self.control.control_id, None, (), None,
                "HTTP server not found (default disabled)",
                "No 'ip http server' directive found. "
                "IOS/IOS-XE default is disabled — no action required.",
            )],
        )
