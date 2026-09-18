"""SVC-001: Unnecessary network services must be disabled."""

from __future__ import annotations

from src.compliance.model import ComplianceResult, ComplianceStatus, Evidence, Remediation, Severity
from src.compliance.rules.base import ComplianceRule, SecurityControl
from src.normalization.model import ConfigItem, NormalizedConfig

_CONTROL = SecurityControl(
    control_id="SVC-001",
    control_name="Unnecessary Network Services Must Be Disabled",
    description=(
        "Cisco IOS enables several unnecessary services by default (CDP, Finger, "
        "TCP small servers, UDP small servers, IP source routing, Proxy ARP). "
        "These services increase the attack surface and must be disabled unless "
        "explicitly required."
    ),
    severity=Severity.MEDIUM,
    framework_refs=(
        "CIS-IOS-L1-1.2",
        "NIST-CM-7",
        "DISA-STIG-NET-SVC-001",
    ),
    applicable_vendors=frozenset({"cisco"}),
)

_CISCO_REMEDIATION = Remediation(
    vendor="cisco",
    guidance="Disable unnecessary services that are not required for device operation.",
    config_hint=(
        "no service finger\n"
        "no service tcp-small-servers\n"
        "no service udp-small-servers\n"
        "no ip source-route\n"
        "no cdp run"
    ),
)

# Services whose explicit enabling is a FAIL
_ENABLED_FAIL_PATTERNS: list[tuple[str, str]] = [
    ("service", "finger"),
    ("service", "tcp-small-servers"),
    ("service", "udp-small-servers"),
    ("ip", "source-route"),
]


class UnnecessaryServicesRule(ComplianceRule):
    """Evaluate SVC-001 for Cisco IOS/IOS-XE."""

    control = _CONTROL

    def evaluate(self, config: NormalizedConfig) -> ComplianceResult:
        if not self.control.applies_to(config.vendor):
            return self._not_applicable(config)
        return self._evaluate_cisco(config)

    def _evaluate_cisco(self, config: NormalizedConfig) -> ComplianceResult:
        bad_items: list[ConfigItem] = []

        for item in config.global_items:
            key = item.key.lower()
            val = (item.value or "").lower().strip()
            for bad_key, bad_val in _ENABLED_FAIL_PATTERNS:
                if key == bad_key and val == bad_val:
                    bad_items.append(item)
                    break

        # Check for explicitly disabled (no ...) to subtract
        no_items: list[ConfigItem] = [
            item for item in config.global_items
            if item.key.lower() == "no"
        ]
        no_values = {(i.value or "").lower().strip() for i in no_items}

        # Filter bad_items: only report enabled services that are NOT explicitly disabled
        actual_bad = [
            item for item in bad_items
            if f"{item.key.lower()} {(item.value or '').lower().strip()}" not in no_values
        ]

        if actual_bad:
            return self._build_result(
                config,
                ComplianceStatus.FAIL,
                [Evidence(
                    self.control.control_id, None,
                    tuple(i.raw_line for i in actual_bad),
                    f"{len(actual_bad)} unnecessary service(s) enabled",
                    "All unnecessary services disabled",
                    f"Found {len(actual_bad)} unnecessary service directive(s) enabled.",
                    line_number=actual_bad[0].line_number,
                )],
                _CISCO_REMEDIATION,
            )
        return self._build_result(
            config,
            ComplianceStatus.PASS,
            [Evidence(
                self.control.control_id, None, (), None,
                "No unnecessary services enabled",
                "No known unnecessary service directives found in active configuration.",
            )],
        )
