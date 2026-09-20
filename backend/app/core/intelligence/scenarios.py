"""
scenarios.py — Sensitivity Analysis & Uncertainty Propagation.

Document 2, Sections 34-36.

Tests the stability of the opportunity recommendation under alternative
catchment radii (5km, 10km, 15km) and propagates unmapped enterprise uncertainty
(worst-case simulation if unmapped businesses turn out to be local competitors).
"""

from __future__ import annotations
import logging
from typing import Optional

from .models import (
    CompetitorRecord,
    SupplyMetrics,
    DemandFeatures,
    SensitivityScenario,
    RelevanceClass,
    RecommendationClass,
)
from .supply import compute_supply_metrics
from .opportunity import (
    calculate_opportunity_indicators,
    compute_opportunity_score_and_verdict,
)

logger = logging.getLogger("udyam_saathi.intelligence.scenarios")


def run_sensitivity_scenarios(
    all_classified_records: list[CompetitorRecord],
    demand: DemandFeatures,
    target_category: str = "",
    target_locality: str = "",
) -> list[SensitivityScenario]:
    """
    Run multi-radius sensitivity analysis (5 km, 10 km, 15 km, 20 km)
    and an unmapped uncertainty stress test.
    """
    scenarios = []

    # 1. Radius Scenarios: 5km, 10km, 15km, 20km
    for radius in [5.0, 10.0, 15.0, 20.0]:
        # Filter records within this distance or unmapped
        sub_records = [
            r for r in all_classified_records
            if r.distance_km is None or r.distance_km <= radius
        ]

        sub_supply = compute_supply_metrics(
            records=sub_records,
            target_locality=target_locality,
            population=demand.population,
        )

        indicators = calculate_opportunity_indicators(
            supply=sub_supply,
            demand=demand,
            category=target_category,
        )

        score, verdict, _ = compute_opportunity_score_and_verdict(
            indicators=indicators,
            supply=sub_supply,
            demand=demand,
        )

        scenarios.append(SensitivityScenario(
            scenario_name=f"Catchment Radius {radius:.0f} km",
            radius_km=radius,
            competitors_count=sub_supply.direct_competitors_count,
            nearest_km=sub_supply.nearest_direct_competitor_km,
            opportunity_score=score,
            recommendation=verdict,
        ))

    # 2. Multi-Tier Uncertainty Stress Testing (Gate 16)
    # Evaluates 4 tiers: 0% (baseline), 15% (mild), 50% (moderate), 100% (worst-case bound)
    unmapped_records = [
        r for r in all_classified_records
        if r.market_zone == "UNMAPPED"
    ]
    unmapped_count = len(unmapped_records)

    base_supply = compute_supply_metrics(
        records=all_classified_records,
        target_locality=target_locality,
        population=demand.population,
    )

    stress_tiers = [
        ("Uncertainty Tier 0 (0% unmapped baseline)", 0.0),
        ("Uncertainty Tier 1 (15% unmapped allocated)", 0.15),
        ("Uncertainty Tier 2 (50% unmapped allocated)", 0.50),
        ("Uncertainty Tier 3 (100% unmapped worst-case)", 1.00),
    ]

    for tier_name, ratio in stress_tiers:
        assumed_extra = int(unmapped_count * ratio)
        stressed_supply = SupplyMetrics(
            total_nearby_enterprises=base_supply.total_nearby_enterprises,
            direct_competitors_count=base_supply.direct_competitors_count + assumed_extra,
            related_businesses_count=base_supply.related_businesses_count,
            indirect_competitors_count=base_supply.indirect_competitors_count,
            non_relevant_count=base_supply.non_relevant_count,
            unknown_relevance_count=base_supply.unknown_relevance_count,
            nearest_direct_competitor_km=base_supply.nearest_direct_competitor_km,
            nearest_related_business_km=base_supply.nearest_related_business_km,
            median_direct_competitor_distance_km=base_supply.median_direct_competitor_distance_km,
            direct_in_core_5km=base_supply.direct_in_core_5km + (assumed_extra // 2),
            direct_in_nearby_10km=base_supply.direct_in_nearby_10km + (assumed_extra - (assumed_extra // 2)),
            direct_outside_10km=base_supply.direct_outside_10km,
            direct_unmapped=base_supply.direct_unmapped,
            direct_in_target_locality=base_supply.direct_in_target_locality + (assumed_extra // 2),
            share_in_target_locality_pct=base_supply.share_in_target_locality_pct,
            category_share_pct=base_supply.category_share_pct,
            hhi_concentration_index=base_supply.hhi_concentration_index,
            businesses_per_1000_people=base_supply.businesses_per_1000_people,
        )

        stress_indicators = calculate_opportunity_indicators(
            supply=stressed_supply,
            demand=demand,
            category=target_category,
        )
        stress_score, stress_verdict, _ = compute_opportunity_score_and_verdict(
            indicators=stress_indicators,
            supply=stressed_supply,
            demand=demand,
        )

        scenarios.append(SensitivityScenario(
            scenario_name=f"{tier_name} (+{assumed_extra})",
            radius_km=10.0,
            competitors_count=stressed_supply.direct_competitors_count,
            nearest_km=stressed_supply.nearest_direct_competitor_km,
            opportunity_score=stress_score,
            recommendation=stress_verdict,
        ))

    return scenarios
