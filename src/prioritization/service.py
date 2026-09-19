"""
prioritization.service
~~~~~~~~~~~~~~~~~~~~~~

Deterministic Finding Prioritization & Operator Risk Queue.
"""

from __future__ import annotations

from dataclasses import dataclass
from src.findings.service import FindingService
from src.intelligence.dependencies import DependencyGraphService


@dataclass
class PrioritizedFinding:
    finding_id: str
    fingerprint: str
    device_id: str
    control_id: str
    severity: str
    status: str
    occurrence_count: int
    first_seen: str
    last_seen: str
    priority_tier: str  # "P1_CRITICAL", "P2_HIGH", "P3_MEDIUM", "P4_LOW"
    priority_score: float  # Deterministic score in [0.0, 10.0]
    risk_factors: list[str]
    evidence_snippet: str | None


class FindingPrioritizationService:
    """Prioritizes open security findings into an explainable operator queue."""

    def __init__(self, db_path: str) -> None:
        self.finding_svc = FindingService(db_path=db_path)
        self.dep_svc = DependencyGraphService()

    def get_priority_queue(self, device_id: str | None = None) -> list[PrioritizedFinding]:
        """Fetch and deterministically rank all open findings."""
        open_findings = self.finding_svc.list_findings(device_id=device_id, status="OPEN")
        prioritized: list[PrioritizedFinding] = []

        dep_graph = self.dep_svc.get_dependency_graph()
        amplifiers = {node["control_id"]: node["amplifies"] for node in dep_graph if node.get("amplifies")}

        for f in open_findings:
            score, tier, factors = self._calculate_priority(f, amplifiers)
            prioritized.append(
                PrioritizedFinding(
                    finding_id=f["id"],
                    fingerprint=f["fingerprint"],
                    device_id=f["device_id"],
                    control_id=f["control_id"],
                    severity=f["severity"],
                    status=f["status"],
                    occurrence_count=f["occurrence_count"],
                    first_seen=f["first_seen"],
                    last_seen=f["last_seen"],
                    priority_tier=tier,
                    priority_score=round(score, 2),
                    risk_factors=factors,
                    evidence_snippet=f["evidence_json"][:200] if f.get("evidence_json") else None,
                )
            )

        # Sort descending by priority_score
        prioritized.sort(key=lambda x: x.priority_score, reverse=True)
        return prioritized

    def _calculate_priority(
        self,
        finding: dict,
        amplifiers: dict[str, list[str]],
    ) -> tuple[float, str, list[str]]:
        """Calculate deterministic priority score in [0.0, 10.0]."""
        factors: list[str] = []
        base_scores = {
            "CRITICAL": 8.0,
            "HIGH": 6.0,
            "MEDIUM": 4.0,
            "LOW": 2.0,
            "INFO": 1.0,
        }
        sev = finding.get("severity", "MEDIUM").upper()
        score = base_scores.get(sev, 3.0)
        factors.append(f"Severity Base ({sev})")

        occ = finding.get("occurrence_count", 1)
        # Recurrence amplification
        if occ > 3:
            score += 1.0
            factors.append(f"Recurring Finding ({occ} occurrences)")
        elif occ > 1:
            score += 0.5
            factors.append(f"Repeated Finding ({occ} occurrences)")

        # Control Dependency Chain Amplification
        c_id = finding.get("control_id", "")
        if c_id in amplifiers:
            score += 1.0
            chain = " -> ".join(amplifiers[c_id])
            factors.append(f"Control Chain Risk Amplification ({c_id} amplifies {chain})")

        score = min(score, 10.0)

        if score >= 8.0:
            tier = "P1_CRITICAL"
        elif score >= 6.0:
            tier = "P2_HIGH"
        elif score >= 4.0:
            tier = "P3_MEDIUM"
        else:
            tier = "P4_LOW"

        return score, tier, factors
