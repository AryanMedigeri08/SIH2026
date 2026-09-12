"""
test_opportunity_engine.py — Comprehensive Unit & Integration Tests for Document 2:
MSME Market Intelligence & Opportunity Engine.

Tests cover:
    1. Business Intent Catalog & Resolution (Canonical intents, keywords, aliases)
    2. Deterministic 5-Class Competitor Relevance Classification
    3. Supply Metrics, Distance & Concentration (5km, 10km, Nearest km, HHI)
    4. Government Dataset Adapters (Population CAGR, Antyodaya Amenities, ODOP)
    5. DemandFeatureStore Orchestration
    6. Opportunity Indicators & Guardrails (SATURATED, CONSTRAINED, INSUFFICIENT_DATA)
    7. Explainability Evidence Object & Limitations Disclosure
    8. Radius Sensitivity Scenarios & Stress Testing
    9. Master MarketOpportunityEngine Orchestration & Multi-Category Comparison
   10. FastAPI V2 Market Intelligence Endpoints via TestClient
"""

import sys
from pathlib import Path

# Add project paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "app" / "core"))

import pytest
from fastapi.testclient import TestClient

from app.core.intelligence.models import (
    RelevanceClass,
    RecommendationClass,
    BusinessIntent,
    CompetitorRecord,
    SupplyMetrics,
    DemandFeatures,
    OpportunityIndicators,
)
from app.core.intelligence.intents import (
    resolve_business_intent,
    list_all_intents,
    INTENT_CATALOG,
)
from app.core.intelligence.relevance import classify_competitor_relevance
from app.core.intelligence.supply import compute_supply_metrics
from app.core.intelligence.opportunity import (
    calculate_opportunity_indicators,
    compute_opportunity_score_and_verdict,
)
from app.core.intelligence.explainability import generate_evidence_object
from app.core.intelligence.scenarios import run_sensitivity_scenarios
from app.core.intelligence.demand import DemandFeatureStore
from app.core.intelligence.engine import MarketOpportunityEngine
from app.core.adapters.population import PopulationAdapter
from app.core.adapters.amenities import AmenitiesAdapter
from app.core.adapters.odop import ODOPAdapter
from app.core.adapters.registry import list_all_sources, DATA_SOURCES


# ============================================================================
# 1. Test Business Intent Catalog & Resolution
# ============================================================================

class TestBusinessIntentResolution:
    """Validates canonical business intents, keyword search, and resolution logic."""

    def test_canonical_intents_catalog(self):
        intents = list_all_intents()
        assert len(intents) >= 10
        codes = [i["intent_id"] for i in intents]
        assert "dairy" in codes
        assert "kirana" in codes
        assert "tailoring" in codes
        assert "poultry" in codes
        assert "agro_processing" in codes
        assert "fabrication" in codes
        assert "mobile_repair" in codes

    def test_resolve_exact_id(self):
        intent = resolve_business_intent("dairy")
        assert intent.intent_id == "dairy"
        assert intent.primary_category == "DAIRY"
        assert "DAIRY" in intent.direct_categories
        assert "FOOD_PROCESSING" in intent.related_categories

    def test_resolve_case_insensitive(self):
        intent = resolve_business_intent("KIRANA")
        assert intent.intent_id == "kirana"
        assert intent.primary_category == "FOOD_RETAIL"

    def test_resolve_by_keyword_milk(self):
        intent = resolve_business_intent("milk chilling center")
        assert intent.intent_id == "dairy"

    def test_resolve_by_keyword_boutique(self):
        intent = resolve_business_intent("boutique ladies dress")
        assert intent.intent_id == "tailoring"

    def test_resolve_by_keyword_welding(self):
        intent = resolve_business_intent("gate welding workshop")
        assert intent.intent_id == "fabrication"

    def test_resolve_fallback(self):
        intent = resolve_business_intent("drone software")
        assert intent.intent_id == "drone software"
        assert intent.primary_category == "DRONE_SOFTWARE"


# ============================================================================
# 2. Test 5-Class Relevance Classification
# ============================================================================

class TestRelevanceClassification:
    """Validates deterministic 5-class competitor relevance with traceability."""

    @pytest.fixture
    def dairy_intent(self) -> BusinessIntent:
        return resolve_business_intent("dairy")

    def test_direct_competitor_by_category(self, dairy_intent):
        business = {
            "enterprise_name": "Krishna Dairy Farm",
            "record_fingerprint": "fp001",
            "primary_category": "DAIRY",
            "primary_category_label": "Dairy Farming",
            "distance_km": 2.5,
            "market_zone": "CORE_5KM",
            "activities_parsed": [
                {"nic_code": "0141", "activity_description": "Raising of dairy cattle"}
            ],
        }
        record = classify_competitor_relevance(business, dairy_intent)
        assert record.relevance_class == RelevanceClass.DIRECT_COMPETITOR.value
        assert record.relevance_confidence in ("HIGH", "MEDIUM")
        assert "direct" in record.relevance_reason.lower()

    def test_related_business_by_category(self, dairy_intent):
        business = {
            "enterprise_name": "Green Agro Feeds",
            "record_fingerprint": "fp002",
            "primary_category": "AGRICULTURE_SUPPORT",
            "primary_category_label": "Agriculture Support",
            "distance_km": 3.0,
            "market_zone": "CORE_5KM",
            "activities_parsed": [
                {"nic_code": "0161", "activity_description": "Support activities for crop production"}
            ],
        }
        record = classify_competitor_relevance(business, dairy_intent)
        assert record.relevance_class == RelevanceClass.RELATED_BUSINESS.value
        assert "related" in record.relevance_reason.lower() or "ecosystem" in record.relevance_reason.lower()

    def test_indirect_competitor_by_keyword(self, dairy_intent):
        business = {
            "enterprise_name": "Sai Cold Drinks & Milk Parlour",
            "record_fingerprint": "fp003",
            "primary_category": "GENERAL_RETAIL",
            "primary_category_label": "Retail",
            "distance_km": 1.5,
            "market_zone": "CORE_5KM",
            "activities_parsed": [
                {"nic_code": "4711", "activity_description": "General store selling milk and cold drinks"}
            ],
        }
        record = classify_competitor_relevance(business, dairy_intent)
        assert record.relevance_class in (
            RelevanceClass.INDIRECT_COMPETITOR.value,
            RelevanceClass.DIRECT_COMPETITOR.value,
        )

    def test_non_relevant_business(self, dairy_intent):
        business = {
            "enterprise_name": "Tech Soft IT Services",
            "record_fingerprint": "fp004",
            "primary_category": "MANUFACTURING",
            "primary_category_label": "Hardware Manufacturing",
            "distance_km": 5.0,
            "market_zone": "NEARBY_10KM",
            "activities_parsed": [
                {"nic_code": "2620", "activity_description": "Manufacture of computers"}
            ],
        }
        record = classify_competitor_relevance(business, dairy_intent)
        assert record.relevance_class == RelevanceClass.NON_RELEVANT.value

    def test_unknown_when_category_missing(self, dairy_intent):
        business = {
            "enterprise_name": "Enterprise X",
            "record_fingerprint": "fp005",
            "primary_category": "UNKNOWN",
            "primary_category_label": "Unclassified",
            "distance_km": 1.0,
            "market_zone": "CORE_5KM",
            "activities_parsed": [],
        }
        record = classify_competitor_relevance(business, dairy_intent)
        assert record.relevance_class == RelevanceClass.UNKNOWN.value


# ============================================================================
# 3. Test Supply Metrics, Distance & Concentration
# ============================================================================

class TestSupplyMetrics:
    """Validates distance distribution, nearest competitor, core/nearby counts, and HHI."""

    def test_supply_metrics_calculation(self):
        records = [
            CompetitorRecord(
                enterprise_name="D1", record_fingerprint="fp1", category="DAIRY",
                category_label="Dairy", relevance_class=RelevanceClass.DIRECT_COMPETITOR.value,
                distance_km=3.5, market_zone="CORE_5KM", resolved_locality="TEST_VILLAGE",
            ),
            CompetitorRecord(
                enterprise_name="D2", record_fingerprint="fp2", category="DAIRY",
                category_label="Dairy", relevance_class=RelevanceClass.DIRECT_COMPETITOR.value,
                distance_km=4.9, market_zone="CORE_5KM", resolved_locality="OTHER_VILLAGE",
            ),
            CompetitorRecord(
                enterprise_name="D3", record_fingerprint="fp3", category="DAIRY",
                category_label="Dairy", relevance_class=RelevanceClass.DIRECT_COMPETITOR.value,
                distance_km=8.2, market_zone="NEARBY_10KM", resolved_locality="OTHER_VILLAGE",
            ),
            CompetitorRecord(
                enterprise_name="R1", record_fingerprint="fp4", category="AGRICULTURE_SUPPORT",
                category_label="Agro Support", relevance_class=RelevanceClass.RELATED_BUSINESS.value,
                distance_km=2.1, market_zone="CORE_5KM", resolved_locality="TEST_VILLAGE",
            ),
            CompetitorRecord(
                enterprise_name="NR1", record_fingerprint="fp5", category="SERVICES",
                category_label="Services", relevance_class=RelevanceClass.NON_RELEVANT.value,
                distance_km=1.0, market_zone="CORE_5KM", resolved_locality="TEST_VILLAGE",
            ),
        ]

        metrics = compute_supply_metrics(
            records=records,
            target_locality="TEST_VILLAGE",
            population=5000,
        )

        assert metrics.total_nearby_enterprises == 5
        assert metrics.direct_competitors_count == 3
        assert metrics.related_businesses_count == 1
        assert metrics.indirect_competitors_count == 0
        assert metrics.non_relevant_count == 1
        assert metrics.direct_in_core_5km == 2
        assert metrics.direct_in_nearby_10km == 1
        assert metrics.nearest_direct_competitor_km == 3.5
        assert metrics.median_direct_competitor_distance_km == 4.9
        assert metrics.direct_in_target_locality == 1
        assert metrics.hhi_concentration_index > 0.0

    def test_supply_metrics_no_direct_competitors(self):
        records = [
            CompetitorRecord(
                enterprise_name="IT1", record_fingerprint="fp1", category="SERVICES",
                category_label="Services", relevance_class=RelevanceClass.NON_RELEVANT.value,
                distance_km=2.0, market_zone="CORE_5KM",
            ),
        ]
        metrics = compute_supply_metrics(records=records)
        assert metrics.direct_competitors_count == 0
        assert metrics.nearest_direct_competitor_km is None
        assert metrics.median_direct_competitor_distance_km is None
        assert metrics.direct_in_core_5km == 0


# ============================================================================
# 4. Test Government Dataset Adapters
# ============================================================================

class TestGovernmentAdapters:
    """Validates independent government dataset adapters."""

    def test_population_adapter_telangana_cagr(self):
        adapter = PopulationAdapter()
        meta = adapter.metadata()
        assert meta.source_id == "CENSUS_2011_POPULATION"
        assert "Office of the Registrar General" in meta.publisher

        features = adapter.fetch_features(state="Telangana", district="Medak")
        assert features["data_available"] is True
        assert features["projected_population"] > 4000
        assert features["projected_households"] > 800
        assert features["annual_cagr"] > 0.0

    def test_amenities_adapter_baseline(self):
        adapter = AmenitiesAdapter(api_key="")
        features = adapter.fetch_features(state="Telangana", district="Medak", village="Balanagar")
        assert features["data_available"] is True
        assert features["power_supply_hours"] >= 12.0
        assert features["all_weather_road"] is True
        assert features["commercial_bank_access"] is True
        assert features["infrastructure_score"] >= 5.0

    def test_odop_adapter_matching(self):
        adapter = ODOPAdapter()
        # Yadadri Bhuvanagiri handloom match
        features_yadadri = adapter.fetch_features(
            state="Telangana",
            district="Yadadri Bhuvanagiri",
            target_category="textile handloom"
        )
        assert features_yadadri["is_odop_aligned"] is True

    def test_dataset_registry(self):
        all_meta = list_all_sources()
        assert len(all_meta) == 4
        source_ids = [m["source_id"] for m in all_meta]
        assert "UDYAM_MSME" in source_ids
        assert "CENSUS_2011_POPULATION" in source_ids
        assert "MISSION_ANTYODAYA" in source_ids
        assert "ODOP_REGISTRY" in source_ids


# ============================================================================
# 5. Test Opportunity Indicators & Guardrails
# ============================================================================

class TestOpportunityIndicatorsAndGuardrails:
    """Validates 5 indicators and non-negotiable guardrails."""

    def test_saturated_market_guardrail_triggered(self):
        supply = SupplyMetrics(
            total_nearby_enterprises=500,
            direct_competitors_count=35,
            related_businesses_count=20,
            indirect_competitors_count=10,
            non_relevant_count=435,
            unknown_relevance_count=0,
            direct_in_core_5km=12,  # >= 10 triggers SATURATED_MARKET
            direct_in_nearby_10km=23,
            nearest_direct_competitor_km=1.2,
            median_direct_competitor_distance_km=3.4,
            hhi_concentration_index=1500.0,
        )
        demand = DemandFeatures(
            population=8000,
            households=1600,
            power_supply_hours=20.0,
            all_weather_road=True,
            commercial_bank_access=True,
            internet_access=True,
            storage_access=True,
            infrastructure_score=8.5,
            is_odop_aligned=False,
            sources=["CENSUS", "ANTYODAYA", "ODOP"],
        )

        indicators = calculate_opportunity_indicators(supply, demand, category="DAIRY")
        score, rec, conf = compute_opportunity_score_and_verdict(indicators, supply, demand)
        assert rec == RecommendationClass.SATURATED_MARKET.value
        assert score <= 50.0

    def test_constrained_market_guardrail_poor_power(self):
        supply = SupplyMetrics(
            total_nearby_enterprises=50,
            direct_competitors_count=0,
            related_businesses_count=5,
            indirect_competitors_count=2,
            non_relevant_count=43,
            unknown_relevance_count=0,
            direct_in_core_5km=0,
            direct_in_nearby_10km=0,
            nearest_direct_competitor_km=None,
            median_direct_competitor_distance_km=None,
            hhi_concentration_index=800.0,
        )
        demand = DemandFeatures(
            population=4000,
            households=800,
            power_supply_hours=6.0,  # < 8 hrs triggers CONSTRAINED_MARKET
            all_weather_road=True,
            commercial_bank_access=False,
            internet_access=False,
            storage_access=False,
            infrastructure_score=3.5,
            is_odop_aligned=False,
            sources=["CENSUS", "ANTYODAYA"],
        )

        indicators = calculate_opportunity_indicators(supply, demand, category="DAIRY")
        score, rec, conf = compute_opportunity_score_and_verdict(indicators, supply, demand)
        assert rec == RecommendationClass.CONSTRAINED_MARKET.value
        assert indicators.infrastructure_penalty >= 20.0

    def test_insufficient_data_guardrail(self):
        supply = SupplyMetrics(
            total_nearby_enterprises=0,
            direct_competitors_count=0,
            direct_unmapped=100,
        )
        demand = DemandFeatures(
            population=0,
            households=0,
            has_sufficient_demand_evidence=False,
            sources=[],
        )

        indicators = calculate_opportunity_indicators(supply, demand, category="DAIRY")
        score, rec, conf = compute_opportunity_score_and_verdict(indicators, supply, demand)
        assert rec == RecommendationClass.INSUFFICIENT_DATA.value


# ============================================================================
# 6. Test Explainability & Sensitivity Scenarios
# ============================================================================

class TestExplainabilityAndSensitivity:
    """Validates structured evidence objects and scenario sweeps."""

    def test_explainability_evidence_object(self):
        supply = SupplyMetrics(
            total_nearby_enterprises=50,
            direct_competitors_count=1,
            related_businesses_count=10,
            indirect_competitors_count=5,
            non_relevant_count=34,
            direct_in_core_5km=0,
            direct_in_nearby_10km=1,
            nearest_direct_competitor_km=7.5,
            median_direct_competitor_distance_km=7.5,
            hhi_concentration_index=1200.0,
        )
        demand = DemandFeatures(
            population=6000,
            households=1200,
            power_supply_hours=18.0,
            all_weather_road=True,
            commercial_bank_access=True,
            internet_access=True,
            storage_access=False,
            infrastructure_score=7.5,
            is_odop_aligned=True,
            odop_product_name="Buffalo Milk & Ghee",
            sources=["CENSUS_2011", "MISSION_ANTYODAYA", "ODOP_REGISTRY"],
        )
        indicators = calculate_opportunity_indicators(supply, demand, category="DAIRY")
        score, rec, conf = compute_opportunity_score_and_verdict(indicators, supply, demand)

        evidence = generate_evidence_object(
            score=score,
            verdict=rec,
            confidence=conf,
            supply=supply,
            demand=demand,
            indicators=indicators,
            intent_name="Dairy Farming & Milk Processing",
            target_village="BALANAGAR",
            district="MEDAK",
            state="TELANGANA",
        )

        assert evidence.composite_score == score
        assert evidence.recommendation == rec
        assert len(evidence.top_positive_drivers) > 0
        assert len(evidence.plain_language_summary) > 50
        assert "BALANAGAR" in evidence.plain_language_summary

    def test_radius_sensitivity_scenarios(self):
        demand = DemandFeatures(
            population=6000,
            households=1200,
            power_supply_hours=18.0,
            all_weather_road=True,
            commercial_bank_access=True,
            internet_access=True,
            storage_access=False,
            infrastructure_score=7.5,
            is_odop_aligned=False,
            sources=["CENSUS"],
        )
        records = [
            CompetitorRecord(
                enterprise_name="D1", record_fingerprint="fp1", category="DAIRY",
                category_label="Dairy", relevance_class=RelevanceClass.DIRECT_COMPETITOR.value,
                distance_km=4.0, market_zone="CORE_5KM",
            ),
            CompetitorRecord(
                enterprise_name="D2", record_fingerprint="fp2", category="DAIRY",
                category_label="Dairy", relevance_class=RelevanceClass.DIRECT_COMPETITOR.value,
                distance_km=9.0, market_zone="NEARBY_10KM",
            ),
            CompetitorRecord(
                enterprise_name="D3", record_fingerprint="fp3", category="DAIRY",
                category_label="Dairy", relevance_class=RelevanceClass.DIRECT_COMPETITOR.value,
                distance_km=14.0, market_zone="OUTSIDE_10KM",
            ),
        ]

        scenarios = run_sensitivity_scenarios(
            all_classified_records=records,
            demand=demand,
            target_category="DAIRY",
            target_locality="TEST_VILLAGE",
        )
        # Should contain 5km, 10km, 15km, 20km and uncertainty stress test
        assert len(scenarios) >= 4
        # 5km has 1 competitor
        assert scenarios[0].competitors_count == 1
        # 10km has 2 competitors
        assert scenarios[1].competitors_count == 2
        # 15km has 3 competitors
        assert scenarios[2].competitors_count == 3


# ============================================================================
# 7. Test Master MarketOpportunityEngine Orchestration
# ============================================================================

class TestMarketOpportunityEngine:
    """Validates end-to-end opportunity report generation and comparison."""

    def test_engine_single_category_analysis(self):
        engine = MarketOpportunityEngine()
        report = engine.analyze_opportunity(
            state="TELANGANA",
            district="MEDAK",
            village="BALANAGAR",
            business_intent="dairy",
            radius_km=10.0,
        )
        assert report.target_location["village"] == "BALANAGAR"
        assert report.business_intent["intent_id"] == "dairy"
        assert report.composite_score >= 0.0
        assert report.recommendation in [r.value for r in RecommendationClass]
        assert report.supply_metrics["total_nearby_enterprises"] > 0
        assert report.evidence["plain_language_summary"] != ""
        assert len(report.sensitivity_analysis) >= 4

    def test_engine_multi_category_comparison(self):
        engine = MarketOpportunityEngine()
        comparison = engine.compare_categories(
            state="TELANGANA",
            district="MEDAK",
            village="BALANAGAR",
            categories=["dairy", "kirana", "tailoring"],
            radius_km=10.0,
        )
        assert len(comparison) == 3
        # Should be ranked descending by score
        scores = [c["composite_score"] for c in comparison]
        assert scores == sorted(scores, reverse=True)
        assert comparison[0]["intent_id"] in ["dairy", "kirana", "tailoring"]


# ============================================================================
# 8. Test FastAPI V2 Endpoints via TestClient
# ============================================================================

class TestMarketIntelligenceAPI:
    """Validates FastAPI V2 endpoints for opportunity intelligence."""

    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def test_get_canonical_intents(self, client):
        response = client.get("/api/v2/market-analysis/intents")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 10
        assert any(i["intent_id"] == "dairy" for i in data["intents"])

    def test_get_dataset_sources(self, client):
        response = client.get("/api/v2/market-analysis/sources")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 4
        source_ids = [s["source_id"] for s in data["sources"]]
        assert "UDYAM_MSME" in source_ids
        assert "CENSUS_2011_POPULATION" in source_ids
        assert "MISSION_ANTYODAYA" in source_ids
        assert "ODOP_REGISTRY" in source_ids

    def test_post_opportunity_analysis_endpoint(self, client):
        payload = {
            "state": "TELANGANA",
            "district": "MEDAK",
            "village": "BALANAGAR",
            "business_intent": "dairy",
            "radius_km": 10.0,
        }
        response = client.post("/api/v2/market-analysis/opportunity", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["business_intent"]["intent_id"] == "dairy"
        assert "composite_score" in data
        assert "recommendation" in data
        assert "evidence" in data
        assert "sensitivity_analysis" in data
        assert len(data["sensitivity_analysis"]) >= 4

    def test_post_compare_categories_endpoint(self, client):
        payload = {
            "state": "TELANGANA",
            "district": "MEDAK",
            "village": "BALANAGAR",
            "categories": ["dairy", "kirana"],
            "radius_km": 10.0,
        }
        response = client.post("/api/v2/market-analysis/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["village"] == "BALANAGAR"
        assert data["count"] == 2
        assert len(data["comparisons"]) == 2
