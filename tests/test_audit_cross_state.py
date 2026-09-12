"""
test_audit_cross_state.py — Cross-State Multi-District Validation Suite.

Document 3, Gates 17, 18, 26.
Validates the full Village Intelligence & Opportunity Engine across 4 distinct Indian states
and business sectors:
    1. Telangana (Medak / Balanagar) — Dairy
    2. Maharashtra (Satara / Patan) — Kirana / Grocery
    3. Karnataka (Mandya / Maddur) — Tailoring / Apparel
    4. Uttar Pradesh (Varanasi / Kashi) — Metal Fabrication
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "app" / "core"))

import pytest
from app.core.intelligence.engine import MarketOpportunityEngine
from app.core.intelligence.models import RecommendationClass
from app.core.adapters.population import PopulationAdapter
from app.core.adapters.amenities import AmenitiesAdapter
from app.core.adapters.odop import ODOPAdapter


CROSS_STATE_TARGETS = [
    {
        "state": "TELANGANA",
        "district": "MEDAK",
        "village": "Balanagar",
        "intent": "dairy",
        "expected_cagr_min": 0.005,
    },
    {
        "state": "MAHARASHTRA",
        "district": "SATARA",
        "village": "Patan",
        "intent": "kirana",
        "expected_cagr_min": 0.005,
    },
    {
        "state": "KARNATAKA",
        "district": "MANDYA",
        "village": "Maddur",
        "intent": "tailoring",
        "expected_cagr_min": 0.005,
    },
    {
        "state": "UTTAR PRADESH",
        "district": "VARANASI",
        "village": "Rohania",
        "intent": "fabrication",
        "expected_cagr_min": 0.005,
    },
]


def test_cross_state_demographics():
    """Verify Census population projection baseline and CAGR across states."""
    pop_adapter = PopulationAdapter()
    for target in CROSS_STATE_TARGETS:
        state = target["state"]
        district = target["district"]
        village = target["village"]

        pop_data = pop_adapter.fetch_features(state=state, district=district, village=village)
        assert pop_data["projected_population"] > 0, f"Population must be > 0 for {village}, {district}"
        assert pop_data["projected_households"] > 0, f"Households must be > 0 for {village}, {district}"
        assert pop_data["projection_status"] == "Projected population baseline", "Projection status wording mismatch"
        assert pop_data["annual_cagr"] >= target["expected_cagr_min"], f"CAGR suspiciously low for {state}"
        print(f"[PASS] Demographics for {village}, {district}, {state}: Pop={pop_data['projected_population']:,} (CAGR: {pop_data['annual_cagr']*100:.2f}%)")


def test_cross_state_amenities():
    """Verify Mission Antyodaya amenities baseline retrieval across states."""
    amenities_adapter = AmenitiesAdapter()
    for target in CROSS_STATE_TARGETS:
        state = target["state"]
        district = target["district"]
        village = target["village"]

        amenities = amenities_adapter.fetch_features(state=state, district=district, village=village)
        assert amenities["infrastructure_score"] >= 0.0
        assert amenities["join_level"] in ("village", "district_baseline", "regional_baseline")
        assert "power_supply_hours" in amenities
        assert "all_weather_road" in amenities
        print(f"[PASS] Amenities for {village}, {district}: Score={amenities['infrastructure_score']:.1f}/10 ({amenities['join_level']})")


def test_cross_state_opportunity_pipeline():
    """Execute end-to-end Opportunity Engine across multiple states and business sectors."""
    engine = MarketOpportunityEngine()

    for target in CROSS_STATE_TARGETS:
        state = target["state"]
        district = target["district"]
        village = target["village"]
        intent = target["intent"]

        report = engine.analyze_opportunity(
            state=state,
            district=district,
            village=village,
            business_intent=intent,
            radius_km=10.0,
            core_radius_km=5.0,
            max_records=500,
        )

        assert 5.0 <= report.composite_score <= 95.0, f"Score out of bounds: {report.composite_score}"
        assert report.recommendation in [rc.value for rc in RecommendationClass]
        assert report.confidence in ("HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA")

        # Verify explainability object integrity
        ev = report.evidence
        assert "confidence_reasons" in ev, "confidence_reasons missing from evidence"
        assert len(ev["confidence_reasons"]) > 0, "confidence_reasons must not be empty"
        assert "plain_language_summary" in ev
        all_narrative = " ".join(
            ev.get("top_positive_drivers", [])
            + ev.get("confidence_reasons", [])
            + ev.get("data_quality_limitations", [])
            + [ev.get("plain_language_summary", "")]
        )
        assert "projected population baseline" in all_narrative.lower()

        # Verify sensitivity analysis is present
        assert len(report.sensitivity_analysis) >= 4, "Must have at least 4 sensitivity scenarios"

        # Verify data lineage has government sources
        assert len(report.data_lineage) >= 2, "Must reference official government sources"

        print(
            f"[PASS] Cross-State Opportunity Run: {intent.upper()} in {village} ({district}, {state}) -> "
            f"Score: {report.composite_score:.1f} | Verdict: {report.recommendation} | Conf: {report.confidence}"
        )


if __name__ == "__main__":
    print("=" * 80)
    print("STARTING CROSS-STATE MULTI-DISTRICT AUDIT VALIDATION")
    print("=" * 80)
    test_cross_state_demographics()
    print("-" * 80)
    test_cross_state_amenities()
    print("-" * 80)
    test_cross_state_opportunity_pipeline()
    print("\n" + "=" * 80)
    print("ALL CROSS-STATE TESTS COMPLETED WITH 100% SUCCESS")
    print("=" * 80)
