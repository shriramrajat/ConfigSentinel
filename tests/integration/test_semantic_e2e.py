"""
tests/integration/test_semantic_e2e.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

End-to-end integration test proving the entire Phase 9 Semantic Mapping workflow.
Verifies that:
1. Unknown directives are discovered.
2. AI can propose mappings (mocked LLM).
3. PENDING mappings are NOT injected.
4. Human approval allows injection.
5. Injected mappings alter deterministic compliance results safely.
6. Original evidence is preserved.
"""

from __future__ import annotations

import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch

from src.api.service import run_audit
from src.api.schemas import AuditRequest
from src.mapping.service import SemanticMappingService
from src.mapping.ai_provider import AIMapper
from src.mapping.model import SemanticMapping, UnknownPattern
from src.compliance.model import ComplianceStatus


class MockAIMapper(AIMapper):
    def __init__(self, key: str, val: str):
        self.key = key
        self.val = val

    def propose_mapping(self, pattern: UnknownPattern) -> SemanticMapping:
        from src.mapping.model import HumanApprovalState
        from datetime import datetime, timezone
        import uuid
        return SemanticMapping(
            id=f"map_{pattern.id}",
            pattern_id=pattern.id,
            original_syntax=pattern.raw_directive,
            proposed_key=self.key,
            proposed_value=self.val,
            confidence=0.99,
            explanation="Mock E2E translation",
            approval_state=HumanApprovalState.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


def test_end_to_end_semantic_workflow(temp_db):
    """Prove the end-to-end semantic injection workflow."""
    # 1. Setup
    os.environ["MAPPINGS_DB_PATH"] = temp_db
    mock_ai = MockAIMapper(key="protocol-version", val="v2")
    mapping_svc = SemanticMappingService(db_path=temp_db, ai_mapper=mock_ai)

    # Cisco config that FAILS SSH version (missing 'ip ssh version 2')
    # but contains an unknown directive 'ssh-version 2'
    raw_config = """
hostname LAB-ROUTER-01
!
ssh-version 2
!
line vty 0 4
 transport input ssh
"""

    req = AuditRequest(config_text=raw_config, source_name="e2e-test.conf")

    # 2. First Audit - It should FAIL SSH-001 and DISCOVER 'ssh-version 2'
    resp1 = run_audit(req)
    
    ssh_result = next(r for r in resp1.results if r.control_id == "SSH-001")
    assert ssh_result.status == ComplianceStatus.FAIL.value, "Must initially fail without translation."

    # Verify discovery
    unknowns = mapping_svc.get_unknown_patterns("cisco")
    target_pattern = next((p for p in unknowns if p.raw_directive == "ssh-version 2"), None)
    assert target_pattern is not None, "Unknown directive must be discovered."

    # 3. AI Proposes Mapping
    # (In real life, triggered by API POST /mappings/propose)
    proposal = mapping_svc.propose_mapping(target_pattern.id)
    assert proposal.approval_state.value == "pending"
    
    # Wait, the rule for SSH-001 expects 'ip ssh version 2' for cisco, 
    # which we map to key='ip ssh version', value='2' for global items.
    # Cisco SSH rule looks for global_items key='ip ssh version', value='2'
    # My mock mapped it to key='protocol-version', value='v2', which is Juniper.
    # Let me re-propose with correct Cisco mapping.

def test_end_to_end_semantic_workflow_cisco(temp_db):
    """Prove the end-to-end semantic injection workflow for Cisco."""
    # 1. Setup
    os.environ["MAPPINGS_DB_PATH"] = temp_db
    # Cisco ssh rule checks: key="ip", value="ssh version 2"
    mock_ai = MockAIMapper(key="ip", val="ssh version 2")
    mapping_svc = SemanticMappingService(db_path=temp_db, ai_mapper=mock_ai)

    raw_config = """
hostname LAB-ROUTER-01
!
ssh-version 2
!
line vty 0 4
 transport input ssh
"""

    req = AuditRequest(config_text=raw_config, source_name="e2e-test.conf")

    # 2. First Audit - FAIL
    resp1 = run_audit(req)
    ssh_result = next(r for r in resp1.results if r.control_id == "SSH-001")
    assert ssh_result.status == ComplianceStatus.FAIL.value, "Must initially fail without translation."

    unknowns = mapping_svc.get_unknown_patterns("cisco")
    target_pattern = next((p for p in unknowns if p.raw_directive == "ssh-version 2"), None)
    assert target_pattern is not None, "Unknown directive must be discovered."

    # 3. Propose PENDING
    proposal = mapping_svc.propose_mapping(target_pattern.id)
    assert proposal.approval_state.value == "pending"

    # 4. Second Audit - STILL FAILS
    resp2 = run_audit(req)
    ssh_result2 = next(r for r in resp2.results if r.control_id == "SSH-001")
    assert ssh_result2.status == ComplianceStatus.FAIL.value, "PENDING mappings must not affect audit."

    # 5. Approve Mapping
    approved = mapping_svc.approve_mapping(proposal.id)
    assert approved.approval_state.value == "approved"

    # 6. Third Audit - MUST PASS
    resp3 = run_audit(req)
    ssh_result3 = next(r for r in resp3.results if r.control_id == "SSH-001")
    assert ssh_result3.status == ComplianceStatus.PASS.value, "APPROVED mapping must translate and PASS."

    # 7. Evidence Verification
    evidence_lines = ssh_result3.evidence[0].raw_lines
    assert any("ssh-version 2" in line for line in evidence_lines), "Original raw config line must be preserved in evidence!"

    # 8. Re-instantiate / Simulated Persistent Disk Restart
    del mapping_svc
    mapping_svc_restarted = SemanticMappingService(db_path=temp_db, ai_mapper=mock_ai)
    
    # Verify the approved mapping still exists
    approved_mappings = mapping_svc_restarted.get_approved_mappings("cisco")
    assert any(m.original_syntax == "ssh-version 2" for m in approved_mappings), "Approved mapping MUST survive restart."

    # 9. Fourth Audit - MUST PASS
    resp4 = run_audit(req)
    ssh_result4 = next(r for r in resp4.results if r.control_id == "SSH-001")
    assert ssh_result4.status == ComplianceStatus.PASS.value, "APPROVED mapping must still apply after restart."

def test_ai_not_called_during_audit(temp_db):
    """Prove explicitly that the LLM is never called during run_audit()."""
    os.environ["MAPPINGS_DB_PATH"] = temp_db
    
    raw_config = """
hostname LAB-ROUTER-01
!
some completely unknown directive
"""
    req = AuditRequest(config_text=raw_config, source_name="e2e-test2.conf")
    
    with patch("src.mapping.service.SemanticMappingService.propose_mapping") as mock_propose:
        run_audit(req)
        mock_propose.assert_not_called()
