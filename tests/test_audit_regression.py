"""
test_audit_regression.py — End-to-End Regression & Reproducibility Test Suite.

Document 3, Gates 3, 4, 13, 14, 15, 16, 17, 18.
Verifies:
    1. Deterministic snapshot replay (byte-for-byte / score-for-score reproducibility).
    2. Boundary conditions: Zero competitor market & Extreme saturation.
    3. Multi-tier uncertainty stress tests (Tiers 0, 1, 2, 3 monotonic bounds).
    4. Confidence decoupling & explainability validation (no fabricated turnover).
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "app" / "core"))

import pytest
from app.core.intelligence.models import (
    SupplyMetrics,
    DemandFeatures,
    CompetitorRecord,
    RelevanceClass,
    RecommendationClass,
)
from app.core.intelligence.opportunity import (
    calculate_opportunity_indicators,
    compute_opportunity_score_and_verdict,
)
from app.core.intelligence.scenarios import run_sensitivity_scenarios
from app.core.intelligence.explainability import generate_evidence_object
from app.core.intelligence.engine import MarketOpportunityEngine
from app.core.udyam.snapshot import SnapshotStore


def test_snapshot_replay_reproducibility():
    """Gates 3 & 4: Snapshot replay must produce exact identical scores and verdicts."""
    store = SnapshotStore()
    snapshots = store.list_snapshots()
    if not snapshots:
        pytest.skip("No snapshots found to test replay")

    target_snap = snapshots[0]
    qp = target_snap.get("query_parameters", {})
    engine = MarketOpportunityEngine()

    # Replay twice from same snapshot
    rep1 = engine.analyze_opportunity(
        state=qp.get("state", "TELANGANA"),
        district=qp.get("district", "MEDAK"),
        village=qp.get("village", "Balanagar"),
        target_lat=qp.get("target_lat"),
        target_lon=qp.get("target_lon"),
        business_intent="dairy",
        snapshot_id=target_snap["snapshot_id"],
    )

    rep2 = engine.analyze_opportunity(
        state=qp.get("state", "TELANGANA"),
        district=qp.get("district", "MEDAK"),
        village=qp.get("village", "Balanagar"),
        target_lat=qp.get("target_lat"),
        target_lon=qp.get("target_lon"),
        business_intent="dairy",
        snapshot_id=target_snap["snapshot_id"],
    )

    assert rep1.composite_score == rep2.composite_score, "Replay score non-deterministic"
    assert rep1.recommendation == rep2.recommendation, "Replay recommendation non-deterministic"
    assert rep1.confidence == rep2.confidence, "Replay confidence non-deterministic"
    assert len(rep1.classified_competitors) == len(rep2.classified_competitors)
    print(f"\n[PASS] Snapshot {target_snap['snapshot_id']} replayed deterministically: Score {rep1.composite_score}")


def test_zero_competitor_boundary():
    """Ensure engine behaves correctly when zero competitors exist in trade radius."""
    supply = SupplyMetrics(
        total_nearby_enterprises=0,
        direct_competitors_count=0,
        related_businesses_count=0,
        indirect_competitors_count=0,
        non_relevant_count=0,
        unknown_relevance_count=0,
        nearest_direct_competitor_km=None,
        nearest_related_business_km=None,
        median_direct_competitor_distance_km=None,
        direct_in_core_5km=0,
        direct_in_nearby_10km=0,
        direct_outside_10km=0,
        direct_unmapped=0,
        direct_in_target_locality=0,
        share_in_target_locality_pct=0.0,
        category_share_pct=0.0,
        hhi_concentration_index=0.0,
        businesses_per_1000_people=0.0,
    )

    demand = DemandFeatures(
        population=4500,
        households=900,
        is_odop_aligned=True,
        all_weather_road=True,
        power_supply_hours=20.0,
        commercial_bank_access=True,
        storage_access=True,
        infrastructure_score=8.5,
        has_sufficient_demand_evidence=True,
    )

    indicators = calculate_opportunity_indicators(supply, demand, category="DAIRY")
    score, verdict, confidence = compute_opportunity_score_and_verdict(indicators, supply, demand)

    assert score >= 70.0, f"Expected high score for empty market, got {score}"
    assert verdict == RecommendationClass.HIGH_OPPORTUNITY.value
    assert confidence in ("HIGH", "MEDIUM")

    ev = generate_evidence_object(
        score=score,
        verdict=verdict,
        confidence=confidence,
        supply=supply,
        demand=demand,
        indicators=indicators,
        intent_name="Dairy Farm",
        target_village="TestVillage",
        district="TestDistrict",
        state="TestState",
    )
    assert len(ev.confidence_reasons) > 0
    assert "No nearby enterprises found" in ev.confidence_reasons[0]


def test_extreme_saturation_guardrail():
    """Ensure extreme saturation guardrail forces SATURATED_MARKET verdict."""
    supply = SupplyMetrics(
        total_nearby_enterprises=50,
        direct_competitors_count=28,
        related_businesses_count=5,
        indirect_competitors_count=10,
        non_relevant_count=5,
        unknown_relevance_count=2,
        nearest_direct_competitor_km=0.8,
        nearest_related_business_km=1.2,
        median_direct_competitor_distance_km=3.5,
        direct_in_core_5km=12,
        direct_in_nearby_10km=16,
        direct_outside_10km=0,
        direct_unmapped=0,
        direct_in_target_locality=4,
        share_in_target_locality_pct=14.3,
        category_share_pct=56.0,
        hhi_concentration_index=4200.0,
        businesses_per_1000_people=6.2,
    )

    demand = DemandFeatures(
        population=4500,
        households=900,
        is_odop_aligned=False,
        all_weather_road=True,
        power_supply_hours=20.0,
        commercial_bank_access=True,
        storage_access=True,
        infrastructure_score=8.5,
        has_sufficient_demand_evidence=True,
    )

    indicators = calculate_opportunity_indicators(supply, demand, category="DAIRY")
    score, verdict, confidence = compute_opportunity_score_and_verdict(indicators, supply, demand)

    assert verdict == RecommendationClass.SATURATED_MARKET.value, f"Expected SATURATED_MARKET, got {verdict}"
    print(f"\n[PASS] Severe saturation guardrail triggered correctly: {verdict} (Score: {score})")


def test_uncertainty_stress_testing_tiers():
    """Gate 16: Uncertainty stress testing must generate 4 tiers with monotonic competitor counts."""
    # Create sample classified records with 8 unmapped enterprises
    records = []
    # 5 direct competitors mapped
    for i in range(5):
        records.append(CompetitorRecord(
            record_fingerprint=f"REC-{i}",
            enterprise_name=f"Dairy Unit {i}",
            category="DAIRY",
            category_label="Dairy & Milk Processing",
            market_zone="CORE_5KM",
            distance_km=2.0 + i,
            relevance_class="DIRECT_COMPETITOR",
            relevance_confidence="HIGH",
            relevance_reason="Direct dairy match",
            geographic_confidence="HIGH",
        ))
    # 8 unmapped records
    for j in range(8):
        records.append(CompetitorRecord(
            record_fingerprint=f"UNMAPPED-{j}",
            enterprise_name=f"Enterprise {j}",
            category="UNKNOWN",
            category_label="Unknown",
            market_zone="UNMAPPED",
            distance_km=None,
            relevance_class="UNKNOWN",
            relevance_confidence="UNKNOWN",
            relevance_reason="Unmapped",
            geographic_confidence="UNKNOWN",
        ))

    demand = DemandFeatures(
        population=5000,
        households=1000,
        is_odop_aligned=True,
        all_weather_road=True,
        power_supply_hours=20.0,
        commercial_bank_access=True,
        storage_access=True,
        infrastructure_score=8.0,
        has_sufficient_demand_evidence=True,
    )

    scenarios = run_sensitivity_scenarios(
        all_classified_records=records,
        demand=demand,
        target_category="DAIRY",
        target_locality="TestVillage",
    )

    # Filter out radius scenarios and find the 4 uncertainty tiers
    stress_scenarios = [s for s in scenarios if "Uncertainty Tier" in s.scenario_name]
    assert len(stress_scenarios) == 4, f"Expected 4 stress tiers, found {len(stress_scenarios)}"

    counts = [s.competitors_count for s in stress_scenarios]
    print(f"\nStress Tier Competitor Counts: {counts}")
    # Verify monotonic non-decreasing order: Tier 0 <= Tier 1 <= Tier 2 <= Tier 3
    assert counts[0] <= counts[1] <= counts[2] <= counts[3], "Stress tier counts must be non-decreasing"
    assert counts[0] == 5, f"Tier 0 baseline should have 5 competitors, got {counts[0]}"
    assert counts[3] == 5 + 8, f"Tier 3 worst-case should have 13 competitors, got {counts[3]}"


def test_explainability_no_fabricated_metrics():
    """Gate 15: Explainability must never fabricate financial turnover or footfalls."""
    supply = SupplyMetrics(
        total_nearby_enterprises=10,
        direct_competitors_count=3,
        related_businesses_count=2,
        indirect_competitors_count=1,
        non_relevant_count=3,
        unknown_relevance_count=1,
        nearest_direct_competitor_km=3.5,
        nearest_related_business_km=2.0,
        median_direct_competitor_distance_km=4.0,
        direct_in_core_5km=2,
        direct_in_nearby_10km=1,
        direct_outside_10km=0,
        direct_unmapped=1,
        direct_in_target_locality=1,
        share_in_target_locality_pct=33.3,
        category_share_pct=30.0,
        hhi_concentration_index=1500.0,
        businesses_per_1000_people=2.0,
    )

    demand = DemandFeatures(
        population=6000,
        households=1200,
        is_odop_aligned=True,
        all_weather_road=True,
        power_supply_hours=18.0,
        commercial_bank_access=True,
        storage_access=True,
        infrastructure_score=8.2,
        has_sufficient_demand_evidence=True,
    )

    indicators = calculate_opportunity_indicators(supply, demand, category="DAIRY")
    score, verdict, confidence = compute_opportunity_score_and_verdict(indicators, supply, demand)

    ev = generate_evidence_object(
        score=score,
        verdict=verdict,
        confidence=confidence,
        supply=supply,
        demand=demand,
        indicators=indicators,
        intent_name="Dairy",
        target_village="Balanagar",
        district="Medak",
        state="Telangana",
    )

    # Check that confidence_reasons is populated
    assert len(ev.confidence_reasons) >= 2, "EvidenceObject must have confidence_reasons"
    # Check that no fabricated claims appear
    full_text = " ".join(ev.top_positive_drivers + ev.top_risk_factors + [ev.plain_language_summary])
    forbidden_terms = ["monthly revenue", "daily customers", "annual profit", "turnover estimate"]
    for term in forbidden_terms:
        assert term not in full_text.lower(), f"Found forbidden fabricated term '{term}' in narrative"

    # Verify population wording
    assert "projected population baseline" in full_text.lower()


if __name__ == "__main__":
    test_snapshot_replay_reproducibility()
    test_zero_competitor_boundary()
    test_extreme_saturation_guardrail()
    test_uncertainty_stress_testing_tiers()
    test_explainability_no_fabricated_metrics()
    print("\n" + "=" * 60)
    print("ALL AUDIT REGRESSION TESTS PASSED (100% SUCCESS)")
    print("=" * 60)
