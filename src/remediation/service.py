"""
remediation.service
~~~~~~~~~~~~~~~~~~~

Remediation Intelligence & Post-Fix Audit Verification Engine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from src.api.schemas import AuditRequest, AuditResponse
from src.api.service import run_audit
from src.compliance.model import ComplianceStatus
from src.remediation.model import (
    RemediationObject,
    RemediationVerificationResult,
    VendorRemediationInstruction,
)


REMEDIATION_CATALOG: dict[str, RemediationObject] = {
    "TLN-001": RemediationObject(
        intent_id="TELNET_DISABLED",
        control_id="TLN-001",
        title="Disable Insecure Telnet Service",
        goal="Eliminate plaintext Telnet protocol transmission for management access.",
        risk_notes="Telnet exposes administrative credentials and session data in cleartext.",
        instructions=[
            VendorRemediationInstruction(
                vendor="cisco",
                platform="IOS / IOS-XE",
                syntax="line vty 0 15\n transport input ssh\n no service telnet",
                verification_command="show running-config | section line vty",
            ),
            VendorRemediationInstruction(
                vendor="juniper",
                platform="JunOS",
                syntax="delete system services telnet",
                verification_command="show configuration system services",
            ),
            VendorRemediationInstruction(
                vendor="arista",
                platform="EOS",
                syntax="no management telnet",
                verification_command="show running-config section management",
            ),
            VendorRemediationInstruction(
                vendor="fortinet",
                platform="FortiOS",
                syntax="config system interface\n edit mgmt\n unset allowaccess telnet\n end",
                verification_command="show system interface mgmt",
            ),
            VendorRemediationInstruction(
                vendor="panos",
                platform="PAN-OS",
                syntax="set deviceconfig system service disable-telnet yes",
                verification_command="show deviceconfig system service",
            ),
        ],
    ),
    "SSH-001": RemediationObject(
        intent_id="SSH_VERSION_ENFORCED",
        control_id="SSH-001",
        title="Enforce SSH Protocol Version 2",
        goal="Ensure administrative CLI access requires SSHv2 encryption.",
        risk_notes="SSH Version 1 is vulnerable to man-in-the-middle insertion and weak cipher suites.",
        instructions=[
            VendorRemediationInstruction(
                vendor="cisco",
                platform="IOS / IOS-XE",
                syntax="ip ssh version 2",
                verification_command="show ip ssh",
            ),
            VendorRemediationInstruction(
                vendor="juniper",
                platform="JunOS",
                syntax="set system services ssh protocol-version v2",
                verification_command="show configuration system services ssh",
            ),
            VendorRemediationInstruction(
                vendor="arista",
                platform="EOS",
                syntax="management ssh\n protocol version 2",
                verification_command="show running-config section ssh",
            ),
        ],
    ),
    "PWD-001": RemediationObject(
        intent_id="PASSWORD_ENCRYPTION_ENABLED",
        control_id="PWD-001",
        title="Enforce Strong Secret Password Hashing",
        goal="Store all local passwords using strong non-reversible cryptographic hashes.",
        risk_notes="Plaintext or type 7 passwords in configurations can be reversed instantly.",
        instructions=[
            VendorRemediationInstruction(
                vendor="cisco",
                platform="IOS / IOS-XE",
                syntax="service password-encryption\nenable algorithm-type sha256 secret <SECRET>",
                verification_command="show running-config | include enable secret",
            ),
            VendorRemediationInstruction(
                vendor="juniper",
                platform="JunOS",
                syntax="set system root-authentication plain-text-password",
                verification_command="show configuration system root-authentication",
            ),
        ],
    ),
}


class RemediationService:
    """Service providing structured remediation guidance and deterministic verification."""

    def get_remediation(self, control_id: str, vendor: str | None = None) -> RemediationObject:
        """Fetch remediation instructions for a control_id."""
        rem = REMEDIATION_CATALOG.get(
            control_id,
            RemediationObject(
                intent_id="GENERIC_HARDENING",
                control_id=control_id,
                title=f"Hardening Guidance for {control_id}",
                goal=f"Remediate security vulnerability for {control_id}.",
                risk_notes="Non-compliant directive exposes network assets to security risks.",
                instructions=[
                    VendorRemediationInstruction(
                        vendor=vendor or "any",
                        platform="Generic",
                        syntax="Refer to vendor hardening guide.",
                        verification_command="Re-run compliance audit.",
                    )
                ],
            ),
        )
        if vendor:
            v_clean = vendor.lower()
            filtered_inst = [i for i in rem.instructions if i.vendor.lower() in (v_clean, "any")]
            if filtered_inst:
                return RemediationObject(
                    intent_id=rem.intent_id,
                    control_id=rem.control_id,
                    title=rem.title,
                    goal=rem.goal,
                    risk_notes=rem.risk_notes,
                    instructions=filtered_inst,
                )
        return rem

    def verify_remediation(
        self,
        finding_id: str,
        control_id: str,
        remediated_config_text: str,
        vendor: str | None = None,
    ) -> RemediationVerificationResult:
        """Run post-remediation audit and deterministically verify if fix succeeded."""
        now = datetime.now(timezone.utc).isoformat()
        audit_res: AuditResponse = run_audit(
            AuditRequest(config_text=remediated_config_text, vendor=vendor)
        )

        matched_res = next((r for r in audit_res.results if r.control_id == control_id), None)

        if matched_res and matched_res.status.lower() == "pass":
            status = "FIX_VERIFIED"
            note = f"Verification succeeded: Control {control_id} evaluated to PASS on updated config."
            cur_status = "PASS"
        else:
            status = "FIX_NOT_VERIFIED"
            note = f"Verification failed: Control {control_id} remains non-compliant (FAIL/NEEDS_REVIEW)."
            cur_status = matched_res.status if matched_res else "FAIL"

        return RemediationVerificationResult(
            finding_id=finding_id,
            control_id=control_id,
            status=status,
            previous_status="FAIL",
            current_status=cur_status,
            previous_risk_score=0.8,
            current_risk_score=0.0 if status == "FIX_VERIFIED" else 0.8,
            evidence_note=note,
            verification_timestamp=now,
        )
