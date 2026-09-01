"""
Tests for the AI Semantic Mapping structural phase with SQLite persistence.
"""

import pytest
from fastapi.testclient import TestClient
import sqlite3

from src.api.main import app
from src.mapping.model import HumanApprovalState, PatternStatus, UnknownPattern
from src.mapping.service import SemanticMappingService
from src.mapping.ai_provider import AIMapper

client = TestClient(app)


def test_ai_provider_not_implemented():
    """Verify that AIMapper raises NotImplementedError natively."""
    mapper = AIMapper()
    pattern = UnknownPattern(vendor="fortinet", raw_directive="config system global")
    with pytest.raises(NotImplementedError):
        mapper.propose_mapping(pattern)


class StubAIMapper(AIMapper):
    """Stub AI Mapper for testing the service flow without LLMs."""
    def __init__(self, call_count=0):
        self.call_count = call_count

    def propose_mapping(self, pattern):
        self.call_count += 1
        from src.mapping.model import SemanticMapping, HumanApprovalState
        # Intentionally setting state to APPROVED to test that the service overrides it to PENDING.
        return SemanticMapping(
            pattern_id=pattern.id,
            original_syntax=pattern.raw_directive,
            proposed_key="test_key",
            proposed_value="test_value",
            confidence=0.9,
            explanation="Test explanation",
            approval_state=HumanApprovalState.APPROVED  # Service should override this
        )


def test_mapping_service_lifecycle(tmp_path):
    """Verify the structural service flow and strict security boundaries."""
    db_file = str(tmp_path / "test.db")
    service = SemanticMappingService(db_path=db_file, ai_mapper=StubAIMapper())

    # 1. Unknown Pattern registered
    pattern = UnknownPattern(vendor="fortinet", raw_directive="set admin-scp enable")
    service.add_unknown_pattern(pattern)
    assert pattern.status == PatternStatus.PENDING

    # 2. AI Proposal
    mapping = service.propose_mapping(pattern.id)

    # CRITICAL: AI provider tried to set APPROVED, but service MUST force PENDING
    assert mapping.approval_state == HumanApprovalState.PENDING

    # 3. Pending mappings list
    pending = service.get_pending_mappings()
    assert len(pending) == 1
    assert pending[0].id == mapping.id

    # 4. Human Approval
    approved_mapping = service.approve_mapping(mapping.id)
    assert approved_mapping.approval_state == HumanApprovalState.APPROVED

    updated_pattern = service.get_unknown_pattern(pattern.id)
    assert updated_pattern.status == PatternStatus.MAPPED


def test_mapping_service_rejection(tmp_path):
    """Verify mapping rejection."""
    db_file = str(tmp_path / "test.db")
    service = SemanticMappingService(db_path=db_file, ai_mapper=StubAIMapper())
    pattern = UnknownPattern(vendor="fortinet", raw_directive="set test")
    service.add_unknown_pattern(pattern)

    mapping = service.propose_mapping(pattern.id)
    assert mapping.approval_state == HumanApprovalState.PENDING

    rejected_mapping = service.reject_mapping(mapping.id)
    assert rejected_mapping.approval_state == HumanApprovalState.REJECTED

    updated_pattern = service.get_unknown_pattern(pattern.id)
    assert updated_pattern.status == PatternStatus.REJECTED


def test_state_machine_enforcement(tmp_path):
    """Verify invalid state transitions are blocked."""
    db_file = str(tmp_path / "test.db")
    service = SemanticMappingService(db_path=db_file, ai_mapper=StubAIMapper())

    # Setup two patterns to test both approve and reject flows
    pattern1 = UnknownPattern(vendor="fortinet", raw_directive="set test1")
    pattern2 = UnknownPattern(vendor="fortinet", raw_directive="set test2")
    service.add_unknown_pattern(pattern1)
    service.add_unknown_pattern(pattern2)

    map1 = service.propose_mapping(pattern1.id)
    map2 = service.propose_mapping(pattern2.id)

    # PENDING -> APPROVED (valid)
    service.approve_mapping(map1.id)

    # APPROVED -> APPROVED (invalid)
    with pytest.raises(ValueError, match="Cannot approve mapping in state: APPROVED"):
        service.approve_mapping(map1.id)

    # APPROVED -> REJECTED (invalid)
    with pytest.raises(ValueError, match="Cannot reject mapping in state: APPROVED"):
        service.reject_mapping(map1.id)

    # PENDING -> REJECTED (valid)
    service.reject_mapping(map2.id)

    # REJECTED -> REJECTED (invalid)
    with pytest.raises(ValueError, match="Cannot reject mapping in state: REJECTED"):
        service.reject_mapping(map2.id)

    # REJECTED -> APPROVED (invalid)
    with pytest.raises(ValueError, match="Cannot approve mapping in state: REJECTED"):
        service.approve_mapping(map2.id)


def test_duplicate_pending_proposals_prevented(tmp_path):
    """Verify that a pending mapping prevents duplicate proposals."""
    mapper = StubAIMapper()
    db_file = str(tmp_path / "test.db")
    service = SemanticMappingService(db_path=db_file, ai_mapper=mapper)
    pattern = UnknownPattern(vendor="fortinet", raw_directive="set unique")
    service.add_unknown_pattern(pattern)

    # First proposal
    map1 = service.propose_mapping(pattern.id)
    assert mapper.call_count == 1

    # Second proposal (should return existing pending)
    map2 = service.propose_mapping(pattern.id)
    assert mapper.call_count == 1
    assert map1.id == map2.id

    # Reject it
    service.reject_mapping(map1.id)

    # Third proposal (should create new proposal since the old one is rejected)
    map3 = service.propose_mapping(pattern.id)
    assert mapper.call_count == 2
    assert map3.id != map1.id

    # Approve the new one
    service.approve_mapping(map3.id)

    # Fourth proposal (should create new proposal since the old one is approved)
    map4 = service.propose_mapping(pattern.id)
    assert mapper.call_count == 3
    assert map4.id != map3.id


def test_persistence_reinstantiation(tmp_path):
    """Verify that data persists across service instances."""
    db_file = str(tmp_path / "test.db")
    service1 = SemanticMappingService(db_path=db_file, ai_mapper=StubAIMapper())

    pattern = UnknownPattern(vendor="fortinet", raw_directive="set test persist")
    service1.add_unknown_pattern(pattern)
    map1 = service1.propose_mapping(pattern.id)

    # New instance, same DB file
    service2 = SemanticMappingService(db_path=db_file, ai_mapper=StubAIMapper())
    pending = service2.get_pending_mappings()

    assert len(pending) == 1
    assert pending[0].id == map1.id
    assert pending[0].pattern_id == pattern.id

    retrieved_pattern = service2.get_unknown_pattern(pattern.id)
    assert retrieved_pattern is not None
    assert retrieved_pattern.raw_directive == "set test persist"


def test_mapping_api_propose_not_configured():
    """Verify that the real API endpoint properly wraps the ProviderNotConfiguredError."""
    # Using the real router instance which has the unconfigured _ai_mapper
    pattern = UnknownPattern(vendor="fortinet", raw_directive="test")
    # Add it to the real service
    from src.api.mapping_routes import _service
    _service.add_unknown_pattern(pattern)

    response = client.post("/api/v1/mappings/propose", json={"pattern_id": pattern.id})
    assert response.status_code == 503
    assert "AI Integration is not configured" in response.json()["detail"]


def test_api_existing_health_endpoint():
    """Ensure backward compatibility of existing endpoints."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_production_db_path_startup_safety(tmp_path):
    """Verify that supplying an unreachable MAPPINGS_DB_PATH crashes safely."""
    # In production, /var/data/mappings.db is expected.
    # If /var/data doesn't exist, we must crash rather than fall back to root.
    bad_dir = tmp_path / "does_not_exist"
    db_file = str(bad_dir / "mappings.db")

    with pytest.raises(sqlite3.OperationalError):
        SemanticMappingService(db_path=db_file, ai_mapper=StubAIMapper())
