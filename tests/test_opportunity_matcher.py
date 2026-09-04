"""
test_opportunity_matcher.py — Comprehensive Unit & Integration Tests
for the Regional Alternative Enterprise Recommendation Engine.
"""

import sys
import os
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CORE_DIR = ROOT_DIR / "backend" / "app" / "core"
BACKEND_DIR = ROOT_DIR / "backend"

sys.path.insert(0, str(CORE_DIR))
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from opportunity_matcher import (
    get_alternative_recommendations,
    _deterministic_recommendations,
    _compute_deterministic_dscr,
    _compute_state_affinity,
    SECTOR_CATALOG,
    AlternativeRecommendation,
)


def test_sector_catalog_integrity():
    """Verify SECTOR_CATALOG has 16 valid archetypes with all required attributes."""
    print("\n--- Test: Sector Catalog Integrity ---")
    assert len(SECTOR_CATALOG) == 16, f"Expected 16 archetypes, got {len(SECTOR_CATALOG)}"
    
    required_keys = [
        "sector_id", "enterprise_name", "sector", "business_category",
        "typical_project_cost_range", "typical_turnover_multiplier",
        "opex_ratio", "ideal_infra_min", "weather_risk_max",
        "state_affinities", "description", "relevant_scheme",
    ]
    
    for item in SECTOR_CATALOG:
        for k in required_keys:
            assert k in item, f"Missing key '{k}' in sector {item.get('sector_id')}"
        assert item["typical_project_cost_range"][0] < item["typical_project_cost_range"][1]
        assert 0 < item["opex_ratio"] < 1.0
        assert item["typical_turnover_multiplier"] > 1.0
    
    print(f"✅ All {len(SECTOR_CATALOG)} sector archetypes are valid and well-formed.")


def test_deterministic_dscr_computation():
    """Verify mathematical soundness of deterministic DSCR calculator."""
    print("\n--- Test: Deterministic DSCR Computation ---")
    dscr = _compute_deterministic_dscr(
        project_cost=500000,
        turnover_multiplier=2.0,
        opex_ratio=0.50,
        subsidy_pct=0.25,
        promoter_pct=0.10,
        interest_rate=0.11,
        tenure_years=7,
    )
    assert dscr > 1.33, f"Expected DSCR > 1.33 for viable model, got {dscr}"
    print(f"✅ DSCR calculation verified: {dscr} (Clears RBI 1.33 threshold)")


def test_deterministic_fallback_ranking():
    """Test deterministic matching and sector exclusion."""
    print("\n--- Test: Deterministic Fallback Matching ---")
    recs = _deterministic_recommendations(
        rejected_sector="dairy",
        state_name="Maharashtra",
        district_name="Pune",
        project_cost=600000,
        margin_capital=60000,
        infrastructure_score=7.0,
        weather_risk_score=0.25,
        cpi_inflation_pct=5.2,
        promoter_category="obc",
        max_results=3,
    )
    
    assert len(recs) == 3, f"Expected 3 recommendations, got {len(recs)}"
    
    # Verify rejected sector was excluded
    sectors = [r.sector.lower() for r in recs]
    assert "dairy" not in sectors, "Rejected sector was not excluded!"
    
    # Verify all DSCRs are viable
    for r in recs:
        assert r.estimated_dscr >= 1.25, f"Recommendation {r.enterprise_name} has invalid DSCR {r.estimated_dscr}"
        assert r.estimated_project_cost > 0
        assert r.estimated_annual_turnover > 0
        assert r.suitability_score > 0
        assert r.source == "DETERMINISTIC_FALLBACK"
    
    print(f"✅ Generated 3 diverse recommendations:")
    for r in recs:
        print(f"   #{r.rank} [{r.relevant_scheme}] {r.enterprise_name} (Cost: ₹{r.estimated_project_cost:,.0f} | DSCR: {r.estimated_dscr})")


def test_public_api_end_to_end():
    """Test public async API get_alternative_recommendations()."""
    print("\n--- Test: Public API End-to-End ---")
    context = {
        "enterprise_name": "Stressed Brick Kiln",
        "sector": "construction_materials",
        "business_category": "manufacturing",
        "state_name": "Uttar Pradesh",
        "district_name": "Varanasi",
        "village_name": "Gram Shivpur",
        "is_rural": True,
        "project_cost": 800000,
        "margin_capital": 80000,
        "annual_turnover_estimate": 600000,
        "promoter_category": "sc",
        "infrastructure_score": 6.5,
        "cpi_inflation_pct": 5.4,
        "weather_risk_score": 0.30,
        "msme_density_per_10k": 12.0,
        "competition_intensity": 0.45,
        "dscr": 0.85,
        "ml_confidence_pct": 94.0,
        "top_risk_factor": "DSCR 0.85 below debt solvency line",
    }
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(get_alternative_recommendations(context))
    loop.close()
    
    assert "recommendations" in result
    assert "source" in result
    assert result["count"] >= 3
    assert result["rejected_enterprise"] == "Stressed Brick Kiln"
    
    print(f"✅ Engine responded with {result['count']} recommendations via [{result['source']}]")
    for r in result["recommendations"][:3]:
        print(f"   - {r['enterprise_name']} ({r['sector']}) -> Scheme: {r['relevant_scheme']}, DSCR: {r['estimated_dscr']}")


if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING ALTERNATIVE OPPORTUNITY MATCHER TESTS")
    print("=" * 70)
    
    test_sector_catalog_integrity()
    test_deterministic_dscr_computation()
    test_deterministic_fallback_ranking()
    test_public_api_end_to_end()
    
    print("\n" + "=" * 70)
    print("ALL OPPORTUNITY MATCHER TESTS PASSED!")
    print("=" * 70)
