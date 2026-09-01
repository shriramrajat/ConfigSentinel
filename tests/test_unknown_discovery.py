"""
tests.test_unknown_discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests Phase 6.1: Passive Discovery of Unknown Configuration Directives.
"""

import pytest
import sqlite3
import os
from unittest.mock import patch

from src.api.service import run_audit
from src.api.schemas import AuditRequest
from src.mapping.service import SemanticMappingService
from src.mapping.model import UnknownPattern, HumanApprovalState, PatternStatus
from src.compliance.model import ComplianceStatus

@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "test_discovery.db")
    svc = SemanticMappingService(db_path=db_path)
    return db_path, svc

def _get_patterns(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM unknown_patterns").fetchall()


def test_1_recognized_compliant_not_discovered(test_db):
    """TEST 1: Recognized compliant directive -> no UnknownPattern created."""
    db_path, svc = test_db
    
    # exec-timeout 5 0 is compliant for Cisco EXEC-001
    config_text = "hostname router1\nline vty 0 4\n exec-timeout 5 0"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    with patch("os.getenv", return_value=db_path):
        response = run_audit(request)
        
    patterns = [p for p in _get_patterns(db_path) if "hostname" not in p["raw_directive"]]
    assert len(patterns) == 0


def test_2_recognized_non_compliant_not_discovered(test_db):
    """TEST 2: Recognized non-compliant directive -> no UnknownPattern created."""
    db_path, svc = test_db
    
    # exec-timeout 20 0 is NON-compliant for Cisco EXEC-001
    config_text = "hostname router1\nline vty 0 4\n exec-timeout 20 0"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    with patch("os.getenv", return_value=db_path):
        response = run_audit(request)
        
    patterns = [p for p in _get_patterns(db_path) if "hostname" not in p["raw_directive"]]
    # The rule failed it, so it should NOT be flagged as unknown
    assert len(patterns) == 0


def test_3_unmapped_directive_discovered(test_db):
    """TEST 3: Unmapped directive -> UnknownPattern created."""
    db_path, svc = test_db
    
    # 'custom-timeout 20' is not recognized by any rule
    config_text = "hostname router1\nline vty 0 4\n custom-timeout 20"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    with patch("os.getenv", return_value=db_path):
        response = run_audit(request)
        
    patterns = [p for p in _get_patterns(db_path) if "hostname" not in p["raw_directive"]]
    assert len(patterns) == 1
    assert patterns[0]["raw_directive"] == " custom-timeout 20"
    assert patterns[0]["section_context"] == "line vty 0 4"


def test_4_duplicate_audit_deduplication(test_db):
    """TEST 4: Duplicate audit -> exactly one UnknownPattern."""
    db_path, svc = test_db
    
    config_text = "hostname router1\nline vty 0 4\n custom-timeout 20"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    with patch("os.getenv", return_value=db_path):
        # Run 10 times
        for _ in range(10):
            run_audit(request)
            
    patterns = [p for p in _get_patterns(db_path) if "hostname" not in p["raw_directive"]]
    assert len(patterns) == 1


def test_5_vendor_isolation(test_db):
    """TEST 5: Vendor isolation -> same directive under two vendors creates two records."""
    db_path, svc = test_db
    
    cisco_text = "hostname router1\ncustom-global-command"
    juniper_text = "system {\n host-name router1;\n}\ncustom-global-command"
    
    with patch("os.getenv", return_value=db_path):
        run_audit(AuditRequest(config_text=cisco_text, source_name="test"))
        run_audit(AuditRequest(config_text=juniper_text, source_name="test"))
        
    patterns = [p for p in _get_patterns(db_path) if "host-name" not in p["raw_directive"] and "hostname" not in p["raw_directive"]]
    assert len(patterns) == 2
    vendors = {p["vendor"] for p in patterns}
    assert vendors == {"cisco", "juniper"}


def test_6_context_preservation(test_db):
    """TEST 6: Context preservation -> section/source metadata preserved."""
    db_path, svc = test_db
    
    config_text = "hostname r1\ninterface GigabitEthernet0/0\n speed 1000"
    request = AuditRequest(config_text=config_text, source_name="core-router.cfg")
    
    with patch("os.getenv", return_value=db_path):
        run_audit(request)
        
    patterns = [p for p in _get_patterns(db_path) if "hostname" not in p["raw_directive"]]
    speed_pattern = next(p for p in patterns if "speed" in p["raw_directive"])
    
    assert speed_pattern["section_context"] == "interface GigabitEthernet0/0"
    assert speed_pattern["source_name"] == "core-router.cfg"
    assert speed_pattern["raw_directive"] == " speed 1000"


def test_7_pending_mapping_deduplicates(test_db):
    """TEST 7: Pending mapping -> no duplicate discovery record."""
    db_path, svc = test_db
    
    # Pre-insert a pending mapping
    pattern = UnknownPattern(vendor="cisco", raw_directive=" custom-timeout 20")
    svc.add_unknown_pattern(pattern)
    
    config_text = "hostname router1\nline vty 0 4\n custom-timeout 20"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    with patch("os.getenv", return_value=db_path):
        run_audit(request)
        
    patterns = [p for p in _get_patterns(db_path) if "hostname" not in p["raw_directive"]]
    # Still only 1 record, the original one
    assert len(patterns) == 1


def test_8_approved_mapping_behavior(test_db):
    """TEST 8: Approved mapping -> semantic injection occurs, no duplicate created."""
    db_path, svc = test_db
    
    # Create the pattern and approve a mapping
    pattern = UnknownPattern(vendor="cisco", raw_directive=" custom-timeout 10 0")
    svc.add_unknown_pattern(pattern)
    
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO semantic_mappings 
            (id, pattern_id, original_syntax, proposed_key, proposed_value, confidence, explanation, approval_state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("m1", pattern.id, " custom-timeout 10 0", "exec-timeout", "10 0", 1.0, "Test", HumanApprovalState.APPROVED.value, "2020-01-01", "2020-01-01")
        )
        conn.commit()

    config_text = "hostname router1\nline vty 0 4\n custom-timeout 10 0"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    with patch("os.getenv", return_value=db_path):
        response = run_audit(request)
        
    # Semantic injection happened, so it's compliant now
    exec_result = next((r for r in response.results if r.control_id == "EXEC-001"), None)
    assert exec_result.status == "pass"
    
    patterns = [p for p in _get_patterns(db_path) if "hostname" not in p["raw_directive"]]
    # Still only the original pattern
    assert len(patterns) == 1


def test_9_ai_isolation(test_db):
    """TEST 9: AI isolation -> AI provider is NOT invoked."""
    db_path, svc = test_db
    config_text = "hostname router1\n custom-timeout 20"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    with patch("os.getenv", return_value=db_path):
        with patch("src.mapping.llm_provider.LLMMapper.propose_mapping") as mock_ai:
            run_audit(request)
            mock_ai.assert_not_called()


def test_10_compliance_immutability(test_db):
    """TEST 10: Compliance immutability -> Identical results before/after discovery."""
    db_path, svc = test_db
    config_text = "hostname router1\nline vty 0 4\n custom-timeout 20"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    # Run with discovery disabled by failing the DB
    with patch("os.getenv", return_value="/invalid/path"):
        response_without = run_audit(request)
        
    # Run with discovery enabled
    with patch("os.getenv", return_value=db_path):
        response_with = run_audit(request)
        
    assert response_with.summary == response_without.summary
    assert len(response_with.results) == len(response_without.results)
    for r_with, r_without in zip(response_with.results, response_without.results):
        assert r_with.status == r_without.status


def test_11_discovery_db_failure(test_db):
    """TEST 11: Discovery DB failure -> audit still returns normally."""
    db_path, svc = test_db
    config_text = "hostname router1\n custom-timeout 20"
    request = AuditRequest(config_text=config_text, source_name="test")
    
    with patch("src.mapping.service.SemanticMappingService.add_unknown_patterns_batch", side_effect=Exception("DB Error")):
        with patch("os.getenv", return_value=db_path):
            response = run_audit(request)
            
    # The error was caught, and response was returned normally
    assert response.summary.total_controls > 0


def test_12_empty_raw_line(test_db):
    """TEST 12: Empty raw line -> no meaningless UnknownPattern created."""
    db_path, svc = test_db
    # Parsers usually strip empty lines, but if they don't, discovery should ignore them
    from src.normalization.model import NormalizedConfig, ConfigItem
    
    # Manually inject an empty item to simulate parser bug
    config = NormalizedConfig(vendor="cisco", hostname="router1", global_items=[ConfigItem(key="", value="", raw_line="   ")])
    
    from src.api.service import _discover_unknown_patterns
    _discover_unknown_patterns(config, [], svc)
    
    patterns = [p for p in _get_patterns(db_path) if "hostname" not in p["raw_directive"]]
    assert len(patterns) == 0
