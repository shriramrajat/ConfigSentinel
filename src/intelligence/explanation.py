"""
intelligence.explanation
~~~~~~~~~~~~~~~~~~~~~~~~

Bounded AI Security Explanation for Deterministic Findings.

Safety Boundaries:
- AI explains WHY a finding matters and HOW to remediate.
- AI MUST NOT change PASS/FAIL, severity, or risk score.
- Strict Pydantic schema validation with extra="forbid".
- Pre-LLM secret redaction enforced.
- Robust deterministic fallback when AI is unconfigured/unavailable.
"""

from __future__ import annotations

import json
import logging
from pydantic import BaseModel, ConfigDict, Field
from src.mapping.redaction import redact_secrets

logger = logging.getLogger(__name__)


class FindingExplanationSchema(BaseModel):
    """Strict Pydantic schema for bounded AI finding explanations."""

    model_config = ConfigDict(extra="forbid")

    control_id: str = Field(..., description="Deterministic control ID (e.g. 'TLN-001')")
    why_it_matters: str = Field(..., description="Actionable explanation of the security risk")
    potential_impact: str = Field(..., description="Consequences of unmitigated risk")
    recommended_remediation: str = Field(..., description="Step-by-step remediation guidance")


def get_deterministic_fallback_explanation(control_id: str, control_name: str, severity: str) -> dict[str, str]:
    """Provide static deterministic fallback when LLM is unconfigured or fails."""
    fallbacks: dict[str, dict[str, str]] = {
        "TLN-001": {
            "why_it_matters": "Telnet transmits administrative credentials and commands in unencrypted plaintext across the network.",
            "potential_impact": "Eavesdroppers on the network path can capture cleartext passwords and execute man-in-the-middle attacks.",
            "recommended_remediation": "Disable Telnet management service and enforce SSH Version 2 for administrative CLI access.",
        },
        "SSH-001": {
            "why_it_matters": "SSH Version 1 suffers from cryptographic vulnerabilities including vulnerability to packet insertion and weak key exchanges.",
            "potential_impact": "Attainable decryption of active SSH sessions and session hijacking by network adversaries.",
            "recommended_remediation": "Explicitly enforce 'ip ssh version 2' or equivalent vendor directive.",
        },
        "EXEC-001": {
            "why_it_matters": "Unbounded VTY idle sessions allow unattended management terminals to remain open indefinitely.",
            "potential_impact": "Unauthorized local or pivot access to open administrative consoles.",
            "recommended_remediation": "Configure 'exec-timeout 15 0' or equivalent idle timeout under 15 minutes.",
        },
        "PWD-001": {
            "why_it_matters": "Plaintext or Type 7 obfuscated passwords are trivial to reverse-engineer using standard tools.",
            "potential_impact": "Credential leaks from configuration backups or unauthorized file exposure.",
            "recommended_remediation": "Enable 'service password-encryption' and configure 'enable secret' using SHA-512/PBKDF2.",
        },
        "AAA-001": {
            "why_it_matters": "Local standalone user accounts lack centralized authentication logging and instant access revocation.",
            "potential_impact": "Orphaned local accounts and lack of centralized audit traceability.",
            "recommended_remediation": "Enable AAA new-model and configure TACACS+/RADIUS server groups for admin login.",
        },
    }

    base = fallbacks.get(control_id.upper(), {
        "why_it_matters": f"Control {control_id} ({control_name}) is non-compliant with security baseline standards.",
        "potential_impact": f"Exposure of system management plane to {severity} risk.",
        "recommended_remediation": "Review vendor documentation and apply recommended configuration hardening directives.",
    })

    return {
        "control_id": control_id,
        "why_it_matters": base["why_it_matters"],
        "potential_impact": base["potential_impact"],
        "recommended_remediation": base["recommended_remediation"],
    }


def generate_bounded_finding_explanation(
    control_id: str,
    control_name: str,
    severity: str,
    evidence_text: str | None = None,
    ai_provider: Any = None,
) -> dict[str, str]:
    """Generate bounded AI explanation with pre-LLM secret redaction and strict schema validation."""
    if not ai_provider:
        return get_deterministic_fallback_explanation(control_id, control_name, severity)

    sanitized_evidence = redact_secrets(evidence_text or "")
    prompt = f"""You are a network security compliance expert. Explain the following deterministic security finding:
Control ID: {control_id}
Control Name: {control_name}
Severity: {severity}
Evidence: {sanitized_evidence}

Respond ONLY with valid JSON matching this schema:
{{
  "control_id": "{control_id}",
  "why_it_matters": "<explanation>",
  "potential_impact": "<impact>",
  "recommended_remediation": "<remediation>"
}}"""

    try:
        raw_response = ai_provider.generate(prompt)
        parsed_json = json.loads(raw_response)
        validated = FindingExplanationSchema(**parsed_json)
        return validated.model_dump()
    except Exception as exc:
        logger.warning("AI explanation failed or returned invalid schema (%s); using deterministic fallback.", exc)
        return get_deterministic_fallback_explanation(control_id, control_name, severity)
