"""BANNER-001: A login warning banner must be configured."""

from __future__ import annotations

from src.compliance.model import ComplianceResult, ComplianceStatus, Evidence, Remediation, Severity
from src.compliance.rules.base import ComplianceRule, SecurityControl
from src.normalization.model import NormalizedConfig

_CONTROL = SecurityControl(
    control_id="BANNER-001",
    control_name="Login Warning Banner Must Be Configured",
    description=(
        "A legal warning banner must be displayed before authentication to inform "
        "users of authorized use policies and deter unauthorized access. "
        "The absence of a banner can weaken legal standing in prosecution."
    ),
    severity=Severity.LOW,
    framework_refs=(
        "CIS-IOS-L1-1.6.1",
        "NIST-AC-8",
        "DISA-STIG-NET-BANNER-001",
    ),
    applicable_vendors=frozenset({"cisco", "juniper"}),
)

_CISCO_REMEDIATION = Remediation(
    vendor="cisco",
    guidance="Configure a 'banner login' with an authorized use warning.",
    config_hint=(
        "banner login ^C\n"
        "AUTHORIZED USE ONLY. Unauthorized access is prohibited.\n"
        "^C"
    ),
)

_JUNIPER_REMEDIATION = Remediation(
    vendor="juniper",
    guidance="Configure a login message under system login.",
    config_hint='set system login message "AUTHORIZED USE ONLY. Unauthorized access is prohibited."',
)


class BannerRule(ComplianceRule):
    """Evaluate BANNER-001 for Cisco IOS/IOS-XE and Juniper JunOS."""

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
        # Cisco banner sections appear as ConfigSection with name starting with 'banner'
        banner_sections = [s for s in config.sections if s.name.lower().startswith("banner")]
        # Also check global_items for 'banner login ...' (single-line form)
        banner_items = [
            item for item in config.global_items
            if item.key.lower() == "banner"
        ]
        if banner_sections or banner_items:
            raw = tuple(s.name for s in banner_sections) or tuple(i.raw_line for i in banner_items)
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, None,
                    raw,
                    "Banner configured",
                    "Login banner present",
                    f"Found {len(banner_sections) + len(banner_items)} banner directive(s).",
                )],
            )
        return self._build_result(
            config,
            ComplianceStatus.FAIL,
            [Evidence(
                self.control.control_id, None, (), None,
                "banner login <text>",
                "No login banner is configured.",
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
                    "system login message",
                    "No system section found; banner configuration cannot be verified.",
                )],
                _JUNIPER_REMEDIATION,
            )
        msg_items = [
            item for item in system.items
            if item.key.lower() == "message" and "login" in item.path
        ]
        if msg_items:
            return self._build_result(
                config,
                ComplianceStatus.PASS,
                [Evidence(
                    self.control.control_id, "system",
                    tuple(i.raw_line for i in msg_items),
                    "Login message configured",
                    "Login message present",
                    "Login message found under system login.",
                    line_number=msg_items[0].line_number,
                )],
            )
        return self._build_result(
            config,
            ComplianceStatus.FAIL,
            [Evidence(
                self.control.control_id, "system", (), None,
                'system login message "<text>"',
                "No login message found under system login.",
            )],
            _JUNIPER_REMEDIATION,
        )
