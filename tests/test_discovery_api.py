"""
tests.test_discovery_api
~~~~~~~~~~~~~~~~~~~~~~~~

Tests for Phase 6.2: Unknown Directive Discovery API.
"""

import pytest
from fastapi.testclient import TestClient
import sqlite3

from src.api.main import app
from src.mapping.model import UnknownPattern
from src.api.mapping_routes import _service

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    """Ensure the DB is clean before each test to prevent test pollution."""
    with sqlite3.connect(_service.db_path) as conn:
        conn.execute("DELETE FROM semantic_mappings")
        conn.execute("DELETE FROM unknown_patterns")
        conn.commit()


def test_discovery_queue_empty():
    """TEST 9: Empty discovery queue returns []"""
    response = client.get("/api/v1/mappings/discovered")
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_discovery_queue_returns_patterns():
    """TEST 1: GET /api/v1/mappings/discovered returns discovered patterns."""
    p1 = UnknownPattern(vendor="cisco", raw_directive="test1")
    p2 = UnknownPattern(vendor="juniper", raw_directive="test2")
    _service.add_unknown_patterns_batch([p1, p2])
    
    response = client.get("/api/v1/mappings/discovered")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    
    # TEST 10: Returned API schema matches the domain model.
    item = data["items"][0]
    assert "id" in item
    assert "vendor" in item
    assert "raw_directive" in item
    assert "status" in item


def test_discovery_queue_vendor_filtering():
    """TEST 2 & 3: Vendor filtering works and is isolated."""
    p1 = UnknownPattern(vendor="cisco", raw_directive="test1")
    p2 = UnknownPattern(vendor="juniper", raw_directive="test2")
    _service.add_unknown_patterns_batch([p1, p2])
    
    response = client.get("/api/v1/mappings/discovered?vendor=cisco")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["vendor"] == "cisco"
    assert data["items"][0]["raw_directive"] == "test1"


def test_discovery_queue_status_filtering():
    """Test status filtering works."""
    from src.mapping.model import PatternStatus
    p1 = UnknownPattern(vendor="cisco", raw_directive="test1", status=PatternStatus.PENDING)
    p2 = UnknownPattern(vendor="juniper", raw_directive="test2", status=PatternStatus.MAPPED)
    _service.add_unknown_patterns_batch([p1, p2])
    
    response = client.get(f"/api/v1/mappings/discovered?status={PatternStatus.MAPPED.value}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == PatternStatus.MAPPED.value


def test_discovery_queue_pagination():
    """Test limit and offset pagination."""
    patterns = [UnknownPattern(vendor="cisco", raw_directive=f"test{i}") for i in range(5)]
    _service.add_unknown_patterns_batch(patterns)
    
    response = client.get("/api/v1/mappings/discovered?limit=2&offset=1&sort_by=raw_directive&sort_dir=asc")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 1
    # Sort order is test0, test1, test2, test3, test4. Offset 1 means we start at test1.
    assert data["items"][0]["raw_directive"] == "test1"
    assert data["items"][1]["raw_directive"] == "test2"


def test_discovery_queue_invalid_pagination():
    """Test invalid pagination parameters."""
    response = client.get("/api/v1/mappings/discovered?limit=-1")
    assert response.status_code == 422
    
    response = client.get("/api/v1/mappings/discovered?limit=2000")
    assert response.status_code == 422
    
    response = client.get("/api/v1/mappings/discovered?offset=-5")
    assert response.status_code == 422


def test_discovery_queue_sorting():
    """Test deterministic sorting and whitelisting."""
    p1 = UnknownPattern(vendor="cisco", raw_directive="a")
    p2 = UnknownPattern(vendor="aruba", raw_directive="b")
    _service.add_unknown_patterns_batch([p1, p2])
    
    # Sort by vendor asc
    response = client.get("/api/v1/mappings/discovered?sort_by=vendor&sort_dir=asc")
    assert response.status_code == 200
    assert response.json()["items"][0]["vendor"] == "aruba"
    
    # Sort by vendor desc
    response = client.get("/api/v1/mappings/discovered?sort_by=vendor&sort_dir=desc")
    assert response.status_code == 200
    assert response.json()["items"][0]["vendor"] == "cisco"
    
    # Invalid sort fields fallback safely to first_seen desc
    response = client.get("/api/v1/mappings/discovered?sort_by=invalid_field; DROP TABLE users;&sort_dir=invalid")
    assert response.status_code == 200
    # Should not crash


def test_discovery_queue_sql_injection():
    """TEST 4: Malicious vendor input cannot perform SQL injection."""
    p1 = UnknownPattern(vendor="cisco", raw_directive="test1")
    p2 = UnknownPattern(vendor="juniper", raw_directive="test2")
    _service.add_unknown_patterns_batch([p1, p2])
    
    # Attempt SQL injection that would return true for all if string interpolated
    response = client.get("/api/v1/mappings/discovered?vendor=cisco' OR '1'='1")
    assert response.status_code == 200
    data = response.json()
    # It should treat it as a literal string and return 0 results (since we parameterize)
    assert data["total"] == 0


def test_pattern_detail_success():
    """TEST 5: GET /discovered/{id} returns the correct pattern."""
    p = UnknownPattern(vendor="fortinet", raw_directive="set global test")
    _service.add_unknown_patterns_batch([p])
    
    response = client.get(f"/api/v1/mappings/discovered/{p.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == p.id
    assert data["raw_directive"] == "set global test"


def test_pattern_detail_not_found():
    """TEST 6: Unknown pattern ID returns HTTP 404."""
    response = client.get("/api/v1/mappings/discovered/invalid-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


from unittest.mock import patch

def test_discovery_no_ai_invocation():
    """TEST 7: Discovery endpoint does not invoke AI."""
    p = UnknownPattern(vendor="cisco", raw_directive="test1")
    _service.add_unknown_patterns_batch([p])
    
    with patch("src.mapping.llm_provider.LLMMapper.propose_mapping") as mock_ai:
        client.get("/api/v1/mappings/discovered")
        client.get(f"/api/v1/mappings/discovered/{p.id}")
        
        mock_ai.assert_not_called()
