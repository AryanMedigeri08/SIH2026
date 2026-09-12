"""
engine.py — Master MSME Market Intelligence & Opportunity Engine.

Document 2, Sections 68, 75, 78.

Consumes Document 1's geographic market pool and combines:
    1. Business intent modeling
    2. 5-level competitor relevance classification
    3. Supply-side distance and concentration metrics
    4. Independent government demand/amenities features
    5. Transparent opportunity indicators & guardrails
    6. Explainability evidence object
    7. Radius sensitivity & uncertainty stress testing
"""

from __future__ import annotations
import logging
from typing import Optional, Any

from .models import (
    BusinessIntent,
    CompetitorRecord,
    SupplyMetrics,
    DemandFeatures,
    OpportunityIndicators,
    EvidenceObject,
    MarketOpportunityReport,
    RelevanceClass,
    RecommendationClass,
)
from .intents import resolve_business_intent
from .relevance import classify_records_batch
from .supply import compute_supply_metrics
from .demand import DemandFeatureStore
from .opportunity import (
    calculate_opportunity_indicators,
    compute_opportunity_score_and_verdict,
)
from .explainability import generate_evidence_object
from .scenarios import run_sensitivity_scenarios
from app.core.adapters.registry import list_all_sources
from app.core.udyam.pipeline import VillageIntelligencePipeline

logger = logging.getLogger("udyam_saathi.intelligence.engine")


class MarketOpportunityEngine:
    """
    Master intelligence engine delivering comprehensive market feasibility
    and credit appraisal intelligence.
    """

    def __init__(
        self,
        udyam_pipeline: Optional[VillageIntelligencePipeline] = None,
        api_key: Optional[str] = None,
    ):
        self.udyam_pipeline = udyam_pipeline or VillageIntelligencePipeline(api_key=api_key)
        self.demand_store = DemandFeatureStore(api_key=api_key)

    def analyze_opportunity(
        self,
        state: str,
        district: str,
        village: str = "",
        target_lat: Optional[float] = None,
        target_lon: Optional[float] = None,
        business_intent: str = "dairy",
        radius_km: float = 10.0,
        core_radius_km: float = 5.0,
        pincode: Optional[str] = None,
        max_records: Optional[int] = 1000,
        base_population_2011: Optional[float] = None,
        snapshot_id: Optional[str] = None,
    ) -> MarketOpportunityReport:
        """
        Execute full market intelligence and opportunity evaluation.
        Supports deterministic replay using snapshot_id.
        """
        state_clean = state.upper().strip()
        district_clean = district.upper().strip()
        village_clean = village.strip() if village else ""

        # Step 1: Resolve business intent
        intent = resolve_business_intent(business_intent)

        logger.info(
            f"[OPPORTUNITY ENGINE] Analyzing {intent.display_name} in "
            f"{village_clean or district_clean}, {district_clean}, {state_clean} (r={radius_km}km)"
        )

        # Step 2: Retrieve and resolve candidate nearby MSMEs via Document 1 pipeline
        udyam_result = self.udyam_pipeline.analyze(
            state=state_clean,
            district=district_clean,
            village=village_clean,
            target_lat=target_lat,
            target_lon=target_lon,
            radius_km=radius_km,
            core_radius_km=core_radius_km,
            business_category=intent.primary_category,
            pincode=pincode,
            max_records=max_records,
            snapshot_id=snapshot_id,
        )

        nearby_raw = udyam_result.nearby_businesses

        # Step 3: Classify competitor relevance (5 classes)
        classified_records = classify_records_batch(nearby_raw, intent)

        # Step 4: Ingest independent government demand and infrastructure features
        demand_features = self.demand_store.build_demand_features(
            state=state_clean,
            district=district_clean,
            village=village_clean,
            pincode=pincode,
            target_category=intent.primary_category,
            base_population_2011=base_population_2011,
        )

        # Step 5: Calculate supply-side metrics & concentration
        supply_metrics = compute_supply_metrics(
            records=classified_records,
            target_locality=village_clean,
            population=demand_features.population,
        )

        # Step 6: Compute transparent opportunity indicators
        indicators = calculate_opportunity_indicators(
            supply=supply_metrics,
            demand=demand_features,
            category=intent.primary_category,
        )

        # Step 7: Score composite opportunity & determine verdict
        score, verdict, confidence = compute_opportunity_score_and_verdict(
            indicators=indicators,
            supply=supply_metrics,
            demand=demand_features,
        )

        # Step 8: Generate explainability evidence object
        evidence = generate_evidence_object(
            score=score,
            verdict=verdict,
            confidence=confidence,
            supply=supply_metrics,
            demand=demand_features,
            indicators=indicators,
            intent_name=intent.display_name,
            target_village=village_clean,
            district=district_clean,
            state=state_clean,
        )

        # Step 9: Run sensitivity & uncertainty stress testing
        sensitivity = run_sensitivity_scenarios(
            all_classified_records=classified_records,
            demand=demand_features,
            target_category=intent.primary_category,
            target_locality=village_clean,
        )

        # Step 10: Assemble final report
        competitors_only = [
            r.to_dict() for r in classified_records
            if r.relevance_class in (RelevanceClass.DIRECT_COMPETITOR.value, RelevanceClass.RELATED_BUSINESS.value)
        ]

        target_info = {
            "state": state_clean,
            "district": district_clean,
            "village": village_clean,
            "latitude": target_lat,
            "longitude": target_lon,
            "analysis_radius_km": radius_km,
            "core_radius_km": core_radius_km,
            "snapshot_id": udyam_result.pipeline_metadata.get("snapshot_id", ""),
        }

        return MarketOpportunityReport(
            target_location=target_info,
            business_intent=intent.to_dict(),
            recommendation=verdict,
            composite_score=score,
            confidence=confidence,
            supply_metrics=supply_metrics.to_dict(),
            demand_features=demand_features.to_dict(),
            opportunity_indicators=indicators.to_dict(),
            classified_competitors=competitors_only,
            all_nearby_businesses=[r.to_dict() for r in classified_records],
            evidence=evidence.to_dict(),
            sensitivity_analysis=[s.to_dict() for s in sensitivity],
            data_lineage=list_all_sources(),
        )

    def compare_categories(
        self,
        state: str,
        district: str,
        village: str = "",
        target_lat: Optional[float] = None,
        target_lon: Optional[float] = None,
        categories: Optional[list[str]] = None,
        radius_km: float = 10.0,
        max_records: Optional[int] = 500,
    ) -> list[dict[str, Any]]:
        """
        Multi-category comparison for a single village per Section 50.
        Compares multiple business ideas side-by-side without re-fetching UDYAM.
        """
        candidates = categories or ["dairy", "kirana", "tailoring", "poultry", "fabrication"]
        results = []

        for cat in candidates:
            try:
                rep = self.analyze_opportunity(
                    state=state,
                    district=district,
                    village=village,
                    target_lat=target_lat,
                    target_lon=target_lon,
                    business_intent=cat,
                    radius_km=radius_km,
                    max_records=max_records,
                )
                results.append({
                    "intent_id": rep.business_intent.get("intent_id"),
                    "display_name": rep.business_intent.get("display_name"),
                    "primary_category": rep.business_intent.get("primary_category"),
                    "recommendation": rep.recommendation,
                    "composite_score": rep.composite_score,
                    "confidence": rep.confidence,
                    "direct_competitors": rep.supply_metrics.get("direct_competitors_count"),
                    "nearest_competitor_km": rep.supply_metrics.get("nearest_direct_competitor_km"),
                    "summary": rep.evidence.get("plain_language_summary"),
                })
            except Exception as e:
                logger.warning(f"Comparison error for category {cat}: {e}")

        # Rank by composite score descending
        results.sort(key=lambda x: x["composite_score"], reverse=True)
        return results
