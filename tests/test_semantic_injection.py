"""
tests.test_semantic_injection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests the Semantic Injection Layer that runs between Parsing and Auditing.
"""

import pytest
from datetime import datetime, timezone

from src.mapping.model import SemanticMapping, HumanApprovalState, UnknownPattern, PatternStatus
from src.normalization.model import NormalizedConfig, ConfigItem, ConfigSection
from src.api.service import _apply_semantic_mappings, run_audit
from src.api.schemas import AuditRequest
from src.mapping.service import SemanticMappingService
from unittest.mock import patch, MagicMock

@pytest.fixture
def base_config():
    return NormalizedConfig(
        vendor="cisco",
        hostname="router1",
        global_items=[
            ConfigItem(key="crypto", value="force-ssh-v2 enable", raw_line="crypto force-ssh-v2 enable"),
            ConfigItem(key="hostname", value="router1", raw_line="hostname router1")
        ],
        sections=[
            ConfigSection(
                name="interface GigabitEthernet0/0",
                items=[ConfigItem(key="ip", value="address 10.0.0.1 255.255.255.0", raw_line="ip address 10.0.0.1 255.255.255.0")]
            )
        ]
    )

def _make_mapping(original: str, proposed_key: str, proposed_value: str, state: HumanApprovalState) -> SemanticMapping:
    return SemanticMapping(
        pattern_id="dummy-id",
        original_syntax=original,
        proposed_key=proposed_key,
        proposed_value=proposed_value,
        explanation="Test mapping",
        confidence=0.9,
        approval_state=state
    )

def test_approved_mapping_applies(base_config):
    """Test 1 — Approved mapping applies correctly without altering raw_line."""
    approved_map = _make_mapping(
        original="crypto force-ssh-v2 enable",
        proposed_key="ip",
        proposed_value="ssh version 2",
        state=HumanApprovalState.APPROVED
    )
    
    # Pre-condition: key is "crypto"
    assert base_config.global_items[0].key == "crypto"
    assert base_config.global_items[0].raw_line == "crypto force-ssh-v2 enable"
    
    config = _apply_semantic_mappings(base_config, [approved_map])
    
    # Post-condition: key and value translated, raw_line untouched (Test 6)
    assert config.global_items[0].key == "ip"
    assert config.global_items[0].value == "ssh version 2"
    assert config.global_items[0].raw_line == "crypto force-ssh-v2 enable"

def test_pending_mapping_does_nothing(base_config):
    """Test 2 — Pending mapping does nothing (in real execution, it wouldn't even be passed, but the function handles safely)."""
    # Note: _apply_semantic_mappings isn't responsible for filtering PENDING,
    # the SemanticMappingService.get_approved_mappings() is. We test the DB retrieval integration in another test.
    pass # covered by DB integration tests below

def test_no_mapping_unchanged(base_config):
    """Test 4 — No mapping leaves parser output unchanged."""
    config = _apply_semantic_mappings(base_config, [])
    assert config.global_items[0].key == "crypto"
    assert config.global_items[0].raw_line == "crypto force-ssh-v2 enable"

def test_exact_matching_only(base_config):
    """Test 5 — Exact matching only."""
    approved_map = _make_mapping(
        original="crypto force-ssh-v2 enable-extra", # Mismatch
        proposed_key="ip",
        proposed_value="ssh version 2",
        state=HumanApprovalState.APPROVED
    )
    
    config = _apply_semantic_mappings(base_config, [approved_map])
    assert config.global_items[0].key == "crypto" # Remained unchanged

def test_conflicting_mappings(base_config):
    """Test 9 — Conflicting approved mappings."""
    map1 = _make_mapping(
        original="crypto force-ssh-v2 enable",
        proposed_key="ip",
        proposed_value="ssh version 2",
        state=HumanApprovalState.APPROVED
    )
    map2 = _make_mapping(
        original="crypto force-ssh-v2 enable",
        proposed_key="ip",
        proposed_value="ssh version 1", # Conflict!
        state=HumanApprovalState.APPROVED
    )
    
    # Injection layer should deterministically skip applying ambiguous mappings
    config = _apply_semantic_mappings(base_config, [map1, map2])
    assert config.global_items[0].key == "crypto" # Remained unchanged due to conflict!

def test_same_mapping_twice(base_config):
    """Test 9.1 — Exact duplicate mapping is fine."""
    map1 = _make_mapping(
        original="crypto force-ssh-v2 enable",
        proposed_key="ip",
        proposed_value="ssh version 2",
        state=HumanApprovalState.APPROVED
    )
    map2 = _make_mapping(
        original="crypto force-ssh-v2 enable",
        proposed_key="ip",
        proposed_value="ssh version 2",
        state=HumanApprovalState.APPROVED
    )
    
    config = _apply_semantic_mappings(base_config, [map1, map2])
    assert config.global_items[0].key == "ip" # Applied normally since they don't conflict semantically

# ---------------------------------------------------------
# Integration tests covering DB retrieval and Compliance
# ---------------------------------------------------------

@pytest.fixture
def integrated_service(tmp_path):
    db_path = str(tmp_path / "test.db")
    svc = SemanticMappingService(db_path=db_path)
    return svc, db_path

def test_db_filters_non_approved(integrated_service):
    """Test 2 & Test 3 — PENDING and REJECTED mappings do nothing because they aren't loaded."""
    svc, _ = integrated_service
    pattern1 = UnknownPattern(vendor="cisco", raw_directive="test1")
    pattern2 = UnknownPattern(vendor="cisco", raw_directive="test2")
    svc.add_unknown_pattern(pattern1)
    svc.add_unknown_pattern(pattern2)
    
    # Insert manually to simulate states
    with patch('src.mapping.service.get_db') as mock_db:
        # Actually just use real sqlite inserts for simplicity
        import sqlite3
        conn = sqlite3.connect(svc.db_path)
        conn.execute("INSERT INTO semantic_mappings (id, pattern_id, original_syntax, proposed_key, proposed_value, confidence, explanation, approval_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("m1", pattern1.id, "test1", "k", "v", 1.0, "e", HumanApprovalState.PENDING.value, "2020-01-01T00:00:00", "2020-01-01T00:00:00"))
        conn.execute("INSERT INTO semantic_mappings (id, pattern_id, original_syntax, proposed_key, proposed_value, confidence, explanation, approval_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("m2", pattern2.id, "test2", "k", "v", 1.0, "e", HumanApprovalState.REJECTED.value, "2020-01-01T00:00:00", "2020-01-01T00:00:00"))
        conn.commit()
        conn.close()

    # Query for approved mappings should return nothing
    approved = svc.get_approved_mappings(vendor="cisco")
    assert len(approved) == 0

def test_deterministic_compliance_authority(integrated_service):
    """Test 7 — AI translates to a non-compliant value, deterministic rule still fails it."""
    svc, db_path = integrated_service
    pattern = UnknownPattern(vendor="cisco", raw_directive="custom-ssh-v1")
    svc.add_unknown_pattern(pattern)
    
    # Create approved mapping that explicitly maps to ssh version 1 (which is non-compliant)
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO semantic_mappings (id, pattern_id, original_syntax, proposed_key, proposed_value, confidence, explanation, approval_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("m1", pattern.id, "custom-ssh-v1", "ip", "ssh version 1", 1.0, "e", HumanApprovalState.APPROVED.value, "2020-01-01T00:00:00", "2020-01-01T00:00:00"))
    conn.commit()
    conn.close()

    # Add 'hostname cisco-router' so detect_vendor correctly identifies it as cisco,
    # otherwise it falls back to 'unknown' and returns NOT_APPLICABLE.
    config_text = "hostname cisco-router\ncustom-ssh-v1"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    # Patch MAPPINGS_DB_PATH to use our test DB
    with patch("os.getenv", return_value=db_path):
        response = run_audit(request)
        
    # The rule SSH-001 must FAIL because the injected value is "ssh version 1"
    ssh_result = next((r for r in response.results if r.control_id == "SSH-001"), None)
    assert ssh_result is not None
    assert ssh_result.status == "fail"
    assert "cryptographically broken" in ssh_result.evidence[0].note
    
def test_ai_not_called_during_audit(integrated_service):
    """Test 8 — AI provider is never called during audit execution."""
    svc, db_path = integrated_service
    request = AuditRequest(config_text="hostname r1\ncrypto force-ssh-v2 enable", source_name="test")
    
    with patch("os.getenv", return_value=db_path):
        with patch("src.mapping.llm_provider.LLMMapper.propose_mapping") as mock_ai:
            run_audit(request)
            mock_ai.assert_not_called()

def test_malformed_mapping_safe_fallback(integrated_service):
    """Test 10 — Invalid mapping safely ignores or errors out without inventing compliance result."""
    svc, db_path = integrated_service
    pattern = UnknownPattern(vendor="cisco", raw_directive="crypto")
    svc.add_unknown_pattern(pattern)
    
    # Insert mapping with NULL proposed_key (violates our logic, but let's say DB got corrupted)
    import sqlite3
    conn = sqlite3.connect(db_path)
    # The schema requires NOT NULL, so let's bypass it slightly by injecting an empty string
    conn.execute("INSERT INTO semantic_mappings (id, pattern_id, original_syntax, proposed_key, proposed_value, confidence, explanation, approval_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("m1", pattern.id, "crypto", "", "val", 1.0, "e", HumanApprovalState.APPROVED.value, "2020-01-01T00:00:00", "2020-01-01T00:00:00"))
    conn.commit()
    conn.close()

    request = AuditRequest(config_text="crypto", source_name="test")
    
    with patch("os.getenv", return_value=db_path):
        response = run_audit(request)
    
    # Audit shouldn't crash, the empty key will just fail to match any deterministic rule
    assert response.summary.total_controls > 0
