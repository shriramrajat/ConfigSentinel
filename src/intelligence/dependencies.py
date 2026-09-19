"""
intelligence.dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~

Deterministic Security Control Dependency & Threat Scenario Graph.

Design Intent:
- Models structural security relationships between security controls.
- Identifies risk amplification chains (e.g., Telnet Enabled -> Cleartext Credentials -> Unauthorized Access).
- Zero LLM dependency; relationship graph is deterministic and defensible.
"""

from __future__ import annotations

from src.intelligence.model import ControlDependencyNode


CONTROL_DEPENDENCIES: list[ControlDependencyNode] = [
    ControlDependencyNode(
        control_id="TLN-001",
        control_name="Telnet Must Be Disabled",
        depends_on=[],
        amplifies=["AAA-001", "PWD-001"],
        threat_scenario="Cleartext credential interception leading to administrative session takeover.",
    ),
    ControlDependencyNode(
        control_id="SSH-001",
        control_name="SSH Protocol Version 2 Enforced",
        depends_on=["TLN-001"],
        amplifies=["AAA-001"],
        threat_scenario="Cryptographic downgrade attack allowing session decryption and MITM packet insertion.",
    ),
    ControlDependencyNode(
        control_id="AAA-001",
        control_name="Remote AAA Authentication Enforced",
        depends_on=["SSH-001", "TLN-001"],
        amplifies=["EXEC-001", "PWD-001"],
        threat_scenario="Unauthenticated management access due to lack of centralized identity verification.",
    ),
    ControlDependencyNode(
        control_id="PWD-001",
        control_name="Privileged Password Hashing Enforced",
        depends_on=["AAA-001"],
        amplifies=["EXEC-001"],
        threat_scenario="Reversible or weak password hashes exposed in configuration backups.",
    ),
    ControlDependencyNode(
        control_id="EXEC-001",
        control_name="VTY Idle Session Timeout Configured",
        depends_on=["AAA-001"],
        amplifies=[],
        threat_scenario="Unattended open console sessions exploited for unauthorized physical or pivot access.",
    ),
]


class DependencyGraphService:
    """Service providing deterministic security control dependency graphs and attack path analysis."""

    def get_dependency_graph(self) -> list[dict]:
        """Return the complete control dependency and threat scenario graph."""
        return [
            {
                "control_id": node.control_id,
                "control_name": node.control_name,
                "depends_on": node.depends_on,
                "amplifies": node.amplifies,
                "threat_scenario": node.threat_scenario,
            }
            for node in CONTROL_DEPENDENCIES
        ]

    def analyze_attack_paths(self, failing_control_ids: list[str]) -> list[dict]:
        """Analyze active failing controls to construct risk amplification chains."""
        failing_set = set(failing_control_ids)
        chains: list[dict] = []

        for node in CONTROL_DEPENDENCIES:
            if node.control_id in failing_set:
                amplified_active = [c for c in node.amplifies if c in failing_set]
                chains.append({
                    "root_control_id": node.control_id,
                    "root_control_name": node.control_name,
                    "amplified_controls": amplified_active,
                    "threat_scenario": node.threat_scenario,
                    "severity_chain": "CRITICAL" if len(amplified_active) > 0 else "HIGH",
                })

        return chains
