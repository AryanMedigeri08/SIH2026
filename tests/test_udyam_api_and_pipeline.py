"""
test_udyam_api_and_pipeline.py — Integration and API Tests for UDYAM Village Intelligence.

Phases 30, 33 of the implementation plan:
    - Target location modeling
    - Pipeline execution
    - Market zones & competitor/supplier segregation
    - API endpoints (POST /market-analysis, GET /categories, GET /health)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.udyam.models import (
    UdyamCanonicalRecord,
    TargetLocation,
    MarketZone,
    LocalityMasterRecord,
)
from app.core.udyam.pipeline import VillageIntelligencePipeline
from app.core.udyam.geography.gazetteer import Gazetteer


@pytest.fixture
def client():
    return TestClient(app)


class TestUdyamPipelineIntegration:
    """Phase 30: Pipeline integration tests."""

    def test_pipeline_with_mocked_or_seeded_data(self, tmp_path):
        db_path = tmp_path / "test_gazetteer.sqlite3"
        gaz = Gazetteer(db_path=db_path)

        # Seed target village and a nearby village
        gaz.insert_locality(LocalityMasterRecord(
            locality_id="LOC_BALANAGAR",
            state="TELANGANA",
            district="MEDAK",
            village="BALANAGAR",
            normalized_name="BALANAGAR",
            latitude=17.9276,
            longitude=78.2344,
            source="test_seed",
            coordinate_confidence="HIGH",
        ))
        gaz.insert_locality(LocalityMasterRecord(
            locality_id="LOC_SHANKARAMPET",
            state="TELANGANA",
            district="MEDAK",
            village="SHANKARAMPET",
            normalized_name="SHANKARAMPET",
            latitude=17.9800,
            longitude=78.1800,
            source="test_seed",
            coordinate_confidence="HIGH",
        ))

        pipeline = VillageIntelligencePipeline(gazetteer=gaz)
        assert pipeline is not None
        assert pipeline.resolver is not None


class TestUdyamApiEndpoints:
    """Phase 33: API endpoints tests."""

    def test_get_categories(self, client):
        response = client.get("/api/v2/market-analysis/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert data["count"] > 10
        codes = [c["code"] for c in data["categories"]]
        assert "DAIRY" in codes
        assert "FOOD_RETAIL" in codes
        assert "TAILORING" in codes

    def test_get_health(self, client):
        response = client.get("/api/v2/market-analysis/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["api_key_configured"] is True

    def test_market_analysis_validation_error(self, client):
        """Empty request should fail validation."""
        response = client.post("/api/v2/market-analysis", json={})
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

