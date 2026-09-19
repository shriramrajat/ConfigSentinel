"""
tests.unit.test_drift_engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for configuration fingerprinting, drift detection, and posture change delta.
"""

from src.drift.engine import (
    SecurityImpact,
    compute_config_fingerprint,
    compute_posture_delta,
    detect_config_drift,
)
from src.parsers.cisco import parse_cisco
from src.compliance.engine import audit
from src.compliance.registry import RULE_REGISTRY


def test_fingerprint_identical_configs() -> None:
    cfg1 = parse_cisco("hostname ROUTER-01\nip ssh version 2\n")
    cfg2 = parse_cisco("hostname ROUTER-01\nip ssh version 2\n")
    assert compute_config_fingerprint(cfg1) == compute_config_fingerprint(cfg2)


def test_fingerprint_changes_on_directive_modification() -> None:
    cfg1 = parse_cisco("hostname ROUTER-01\nip ssh version 2\n")
    cfg2 = parse_cisco("hostname ROUTER-01\nip ssh version 1\n")
    assert compute_config_fingerprint(cfg1) != compute_config_fingerprint(cfg2)


def test_drift_detection_added_and_removed() -> None:
    cfg1 = parse_cisco("hostname ROUTER-01\nip ssh version 2\n")
    cfg2 = parse_cisco("hostname ROUTER-01\nip ssh version 1\nntp server 10.0.0.1\n")

    drift = detect_config_drift(cfg1, cfg2)
    assert len(drift) >= 1
    # ntp server added
    assert any(d.change_type == "ADDED" and "ntp" in d.key for d in drift)


def test_posture_delta_degradation() -> None:
    cfg_pass = parse_cisco("hostname PASS-RTR\nip ssh version 2\nline vty 0 4\n exec-timeout 10 0\n transport input ssh\n")
    cfg_fail = parse_cisco("hostname FAIL-RTR\nip ssh version 1\nline vty 0 4\n exec-timeout 0 0\n transport input telnet\n")

    res_pass = audit(cfg_pass, RULE_REGISTRY)
    res_fail = audit(cfg_fail, RULE_REGISTRY)

    delta = compute_posture_delta(res_pass, res_fail)
    assert delta.security_impact == SecurityImpact.SECURITY_DEGRADATION
    assert len(delta.new_failures) > 0


def test_posture_delta_improvement() -> None:
    cfg_fail = parse_cisco("hostname FAIL-RTR\nip ssh version 1\n")
    cfg_pass = parse_cisco("hostname PASS-RTR\nip ssh version 2\n")

    res_fail = audit(cfg_fail, RULE_REGISTRY)
    res_pass = audit(cfg_pass, RULE_REGISTRY)

    delta = compute_posture_delta(res_fail, res_pass)
    assert delta.security_impact == SecurityImpact.SECURITY_IMPROVEMENT
    assert "SSH-001" in delta.resolved_failures
