"""
tests.unit.test_mapping_analytics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for learning analytics and mapping usage tracking.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_mapping_stats_endpoint() -> None:
    resp = client.get("/api/v1/mappings/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_patterns" in data
    assert "approved_mappings" in data
    assert "approval_rate" in data
    assert "total_mapping_reuse" in data


def test_get_mapping_usage_endpoint() -> None:
    resp = client.get("/api/v1/mappings/usage")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
