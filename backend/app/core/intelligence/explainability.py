"""
explainability.py — Evidence Object & Transparent Decision-Support Generator.

Document 2, Sections 27, 28, and 40.

Generates auditable, evidence-backed narratives explaining why an opportunity
is scored as high, moderate, saturated, or constrained. Never fabricates financial
figures or customer numbers.
"""

from __future__ import annotations
import logging
from typing import Optional

from .models import (
    SupplyMetrics,
    DemandFeatures,
    OpportunityIndicators,
    EvidenceObject,
    RecommendationClass,
)

logger = logging.getLogger("udyam_saathi.intelligence.explainability")


def generate_evidence_object(
    score: float,
    verdict: str,
    confidence: str,
    supply: SupplyMetrics,
    demand: DemandFeatures,
    indicators: OpportunityIndicators,
    intent_name: str,
    target_village: str,
    district: str,
    state: str,
) -> EvidenceObject:
    """
    Construct a structured EvidenceObject explaining the opportunity verdict.
    """
    positive_drivers = []
    risk_factors = []
    missing_evidence = []
    limitations = []

    # 1. Evaluate Positive Drivers
    if supply.direct_competitors_count <= 3:
        positive_drivers.append(
            f"Favorable supply gap: only {supply.direct_competitors_count} direct competitor(s) "
            f"identified across the 10 km catchment area."
        )
    elif supply.direct_competitors_count <= 8:
        positive_drivers.append(
            f"Moderate competitive density: {supply.direct_competitors_count} registered competitor(s) "
            f"observed within 10 km."
        )

    if supply.nearest_direct_competitor_km is not None:
        if supply.nearest_direct_competitor_km >= 8.0:
            positive_drivers.append(
                f"Accessibility buffer: nearest identified direct competitor is {supply.nearest_direct_competitor_km} km away."
            )
        elif supply.nearest_direct_competitor_km >= 4.0:
            positive_drivers.append(
                f"Reasonable separation: nearest competitor is located {supply.nearest_direct_competitor_km} km from the target village."
            )

    if supply.related_businesses_count > 0:
        positive_drivers.append(
            f"Complementary ecosystem: {supply.related_businesses_count} related enterprise(s) available "
            f"for local raw material supply and B2B partnerships."
        )

    if demand.population >= 3000:
        positive_drivers.append(
            f"Viable demographic base: projected population baseline of {demand.population:,} residents (~{demand.households:,} households) "
            f"in the primary trade territory (Census 2011 + State CAGR)."
        )

    if demand.is_odop_aligned:
        positive_drivers.append(
            f"Government priority alignment: {intent_name} is recognized under the One District One Product (ODOP) "
            f"cluster support program for {district}."
        )

    if demand.power_supply_hours >= 18.0 and demand.all_weather_road:
        positive_drivers.append(
            f"Sound rural infrastructure: reliable 3-phase electricity ({demand.power_supply_hours:.0f} hrs/day) "
            f"and paved all-weather road connectivity."
        )

    # 2. Evaluate Risk Factors
    if supply.direct_in_target_locality > 0:
        risk_factors.append(
            f"Immediate local competition: {supply.direct_in_target_locality} direct competitor(s) "
            f"are registered within the target locality of {target_village or 'the village'} itself."
        )

    if supply.nearest_direct_competitor_km is not None and supply.nearest_direct_competitor_km <= 2.5:
        risk_factors.append(
            f"Proximity pressure: nearest direct competitor is within {supply.nearest_direct_competitor_km} km, "
            f"contesting immediate neighborhood footfall."
        )

    if supply.direct_in_core_5km >= 5:
        risk_factors.append(
            f"Core zone cluster: {supply.direct_in_core_5km} direct competitors operate within a tight 5 km radius."
        )

    if demand.power_supply_hours < 16.0:
        risk_factors.append(
            f"Power constraint: local grid supplies approximately {demand.power_supply_hours:.0f} hours/day, "
            f"potentially requiring backup diesel generator capital."
        )

    if not demand.all_weather_road:
        risk_factors.append(
            "Logistical constraint: lack of paved all-weather road may increase transport and supply turnaround times."
        )

    if not demand.storage_access and intent_name.lower() in ("dairy", "food processing", "poultry"):
        risk_factors.append(
            "Cold chain deficit: absence of certified cold storage / warehousing in the immediate cluster "
            "increases inventory perishability risk."
        )

    # 3. Missing Evidence Disclosures (Sections 26 & 56)
    missing_evidence.append(
        "UDYAM reflects officially registered MSMEs; informal unregistered village micro-units are not captured."
    )
    missing_evidence.append(
        "Individual competitor revenues, daily customer footfalls, and operating profits are not publicly reported."
    )

    # 4. Data Quality Limitations (Section 37)
    limitations.append(
        f"Geographic coverage: {supply.direct_unmapped} enterprise(s) in this district could not be mapped to "
        f"exact geographic coordinates due to sparse address fields and remain unmapped."
    )
    limitations.append(
        "Demographic figures project Census 2011 baselines using state-level CAGR growth trends to 2026."
    )
    limitations.append(
        "Market analysis provides credit appraisal and decision support; it does not guarantee commercial outcomes."
    )

    # 5. Confidence Justification Reasons (Gates 13-15)
    confidence_reasons = []
    resolved_enterprises = max(0, supply.total_nearby_enterprises - supply.direct_unmapped)
    resolved_pct = (
        (resolved_enterprises / max(1, supply.total_nearby_enterprises)) * 100.0
        if supply.total_nearby_enterprises > 0
        else 100.0
    )
    if supply.total_nearby_enterprises > 0:
        confidence_reasons.append(
            f"Geographic resolution: {resolved_pct:.1f}% ({resolved_enterprises}/{supply.total_nearby_enterprises}) "
            f"of enterprises resolved to coordinate-level precision within 10 km."
        )
        if supply.direct_unmapped > 0:
            confidence_reasons.append(
                f"Unmapped enterprise boundary: {supply.direct_unmapped} district enterprise(s) lack geocoordinates "
                f"and are evaluated under uncertainty stress bounds."
            )
    else:
        confidence_reasons.append("No nearby enterprises found within 10 km trade area.")

    if demand.has_sufficient_demand_evidence:
        confidence_reasons.append(
            "Demographic baseline: Census 2011 population baseline with state CAGR projection to 2026."
        )
        confidence_reasons.append(
            f"Infrastructure indicators: Mission Antyodaya survey indicators ({demand.infrastructure_score:.1f}/10 infrastructure score)."
        )
    else:
        confidence_reasons.append(
            "Demographic or infrastructure evidence is incomplete or below appraisal threshold."
        )

    if demand.is_odop_aligned:
        confidence_reasons.append(
            f"ODOP verification: {intent_name} is recognized under the official One District One Product list for {district}."
        )

    # 6. Plain Language Summary
    loc_str = f"{target_village}, {district}, {state}" if target_village else f"{district}, {state}"
    if verdict == RecommendationClass.HIGH_OPPORTUNITY.value:
        summary = (
            f"The proposed {intent_name} in {loc_str} demonstrates HIGH OPPORTUNITY (Score: {score:.1f}/100, Confidence: {confidence}). "
            f"Observed registered supply is sparse ({supply.direct_competitors_count} direct competitors within 10 km) "
            f"backed by a demographic base of {demand.population:,} residents and supportive infrastructure."
        )
    elif verdict == RecommendationClass.MODERATE_OPPORTUNITY.value:
        summary = (
            f"The proposed {intent_name} in {loc_str} shows MODERATE OPPORTUNITY (Score: {score:.1f}/100, Confidence: {confidence}). "
            f"While demographic demand is viable, {supply.direct_competitors_count} competitor(s) exist within the 10 km trade radius, "
            f"requiring clear differentiation in product quality, pricing, or service delivery."
        )
    elif verdict == RecommendationClass.SATURATED_MARKET.value:
        summary = (
            f"The market for {intent_name} in {loc_str} shows signs of SATURATION (Score: {score:.1f}/100, Confidence: {confidence}). "
            f"A substantial cluster of {supply.direct_competitors_count} direct competitor(s) already operates nearby "
            f"({supply.direct_in_core_5km} within 5 km). Alternative regional enterprise archetypes should be considered."
        )
    elif verdict == RecommendationClass.CONSTRAINED_MARKET.value:
        summary = (
            f"The market for {intent_name} in {loc_str} is CONSTRAINED (Score: {score:.1f}/100, Confidence: {confidence}). "
            f"Local infrastructure limitations (power, road, or financial touchpoints) impose headwinds "
            f"that outweigh supply gap advantages."
        )
    else:
        summary = (
            f"INSUFFICIENT DATA to establish a definitive opportunity score for {intent_name} in {loc_str}. "
            f"Independent government demand datasets or geographic coordinates are incomplete."
        )

    return EvidenceObject(
        recommendation=verdict,
        composite_score=score,
        confidence=confidence,
        confidence_reasons=confidence_reasons,
        top_positive_drivers=positive_drivers,
        top_risk_factors=risk_factors,
        missing_evidence=missing_evidence,
        data_quality_limitations=limitations,
        plain_language_summary=summary,
    )
