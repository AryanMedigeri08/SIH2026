"""
intelligence — MSME Market Intelligence & Opportunity Engine Package.
Document 2 Implementation.
"""

from .models import (
    RelevanceClass,
    RecommendationClass,
    BusinessIntent,
    CompetitorRecord,
    SupplyMetrics,
    DemandFeatures,
    OpportunityIndicators,
    EvidenceObject,
    SensitivityScenario,
    MarketOpportunityReport,
)
from .intents import resolve_business_intent, list_all_intents, INTENT_CATALOG
from .relevance import classify_competitor_relevance, classify_records_batch
from .supply import compute_supply_metrics
from .demand import DemandFeatureStore
from .opportunity import calculate_opportunity_indicators, compute_opportunity_score_and_verdict
from .explainability import generate_evidence_object
from .scenarios import run_sensitivity_scenarios
from .engine import MarketOpportunityEngine

__all__ = [
    "RelevanceClass",
    "RecommendationClass",
    "BusinessIntent",
    "CompetitorRecord",
    "SupplyMetrics",
    "DemandFeatures",
    "OpportunityIndicators",
    "EvidenceObject",
    "SensitivityScenario",
    "MarketOpportunityReport",
    "resolve_business_intent",
    "list_all_intents",
    "INTENT_CATALOG",
    "classify_competitor_relevance",
    "classify_records_batch",
    "compute_supply_metrics",
    "DemandFeatureStore",
    "calculate_opportunity_indicators",
    "compute_opportunity_score_and_verdict",
    "generate_evidence_object",
    "run_sensitivity_scenarios",
    "MarketOpportunityEngine",
]
