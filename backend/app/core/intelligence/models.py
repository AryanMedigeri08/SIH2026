"""
models.py — Data Structures for MSME Market Intelligence & Opportunity Engine.

Document 2, Sections 4-16, 23-28, 40.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import Optional, Any
from datetime import datetime, timezone


class RelevanceClass(str, Enum):
    """5-level competitor relevance classification per Section 9."""
    DIRECT_COMPETITOR = "DIRECT_COMPETITOR"
    RELATED_BUSINESS = "RELATED_BUSINESS"
    INDIRECT_COMPETITOR = "INDIRECT_COMPETITOR"
    NON_RELEVANT = "NON_RELEVANT"
    UNKNOWN = "UNKNOWN"


class RecommendationClass(str, Enum):
    """Opportunity recommendation classification per Section 33."""
    HIGH_OPPORTUNITY = "HIGH_OPPORTUNITY"
    MODERATE_OPPORTUNITY = "MODERATE_OPPORTUNITY"
    SATURATED_MARKET = "SATURATED_MARKET"
    CONSTRAINED_MARKET = "CONSTRAINED_MARKET"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class BusinessIntent:
    """User's entrepreneurial intent per Section 5."""
    intent_id: str
    display_name: str
    primary_category: str
    direct_categories: list[str] = field(default_factory=list)
    related_categories: list[str] = field(default_factory=list)
    search_keywords: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CompetitorRecord:
    """Classified enterprise record per Section 11."""
    enterprise_name: str
    record_fingerprint: str
    category: str
    category_label: str
    subcategory: str = ""
    relevance_class: str = RelevanceClass.UNKNOWN.value
    relevance_reason: str = ""
    relevance_confidence: str = "UNKNOWN"  # HIGH | MEDIUM | LOW | UNKNOWN
    distance_km: Optional[float] = None
    market_zone: str = "UNMAPPED"
    resolved_locality: str = ""
    geographic_confidence: str = "UNKNOWN"
    registration_date: Optional[str] = None
    nic_code: str = ""
    activity_description: str = ""
    data_sources: list[str] = field(default_factory=lambda: ["UDYAM_MSME"])
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coordinate_confidence: str = "UNKNOWN"
    coordinate_source: str = ""
    activities_parsed: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SupplyMetrics:
    """Supply-side concentration and competitor metrics per Sections 12-16."""
    total_nearby_enterprises: int = 0
    direct_competitors_count: int = 0
    related_businesses_count: int = 0
    indirect_competitors_count: int = 0
    non_relevant_count: int = 0
    unknown_relevance_count: int = 0

    # Distance metrics
    nearest_direct_competitor_km: Optional[float] = None
    nearest_related_business_km: Optional[float] = None
    median_direct_competitor_distance_km: Optional[float] = None

    # Zone distribution of direct competitors
    direct_in_core_5km: int = 0
    direct_in_nearby_10km: int = 0
    direct_outside_10km: int = 0
    direct_unmapped: int = 0

    # Geographic concentration
    direct_in_target_locality: int = 0
    share_in_target_locality_pct: float = 0.0

    # Category concentration & market density
    category_share_pct: float = 0.0
    hhi_concentration_index: float = 0.0  # 0 to 10,000 scale
    businesses_per_1000_people: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DemandFeatures:
    """Independent government demand-side indicators per Sections 17-21."""
    population: int = 0
    households: int = 0
    annual_population_growth_pct: float = 0.0
    infrastructure_score: float = 5.0
    power_supply_hours: float = 18.0
    all_weather_road: bool = True
    commercial_bank_access: bool = True
    internet_access: bool = True
    storage_access: bool = False
    is_odop_aligned: bool = False
    odop_product_name: Optional[str] = None
    data_years: dict[str, str] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
    has_sufficient_demand_evidence: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OpportunityIndicators:
    """Transparent independent opportunity sub-scores (0 to 100) per Section 23."""
    supply_gap_score: float = 50.0        # High score = few competitors relative to population
    accessibility_gap_score: float = 50.0  # High score = competitors are far away
    demand_support_score: float = 50.0    # High score = strong population & purchasing base
    growth_support_score: float = 50.0    # High score = expanding demographics & priority
    infrastructure_penalty: float = 0.0   # Negative penalty (0 to 40) for deficits

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvidenceObject:
    """Explainability and decision-support evidence per Sections 27-28 & 40."""
    recommendation: str
    composite_score: float
    confidence: str  # HIGH | MEDIUM | LOW | INSUFFICIENT_DATA
    confidence_reasons: list[str] = field(default_factory=list)
    top_positive_drivers: list[str] = field(default_factory=list)
    top_risk_factors: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    data_quality_limitations: list[str] = field(default_factory=list)
    plain_language_summary: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SensitivityScenario:
    """A single sensitivity scenario per Sections 34-36."""
    scenario_name: str
    radius_km: float
    competitors_count: int
    nearest_km: Optional[float]
    opportunity_score: float
    recommendation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MarketOpportunityReport:
    """Complete user-facing and API intelligence deliverable per Section 38."""
    target_location: dict[str, Any]
    business_intent: dict[str, Any]
    recommendation: str
    composite_score: float
    confidence: str

    supply_metrics: dict[str, Any]
    demand_features: dict[str, Any]
    opportunity_indicators: dict[str, Any]

    classified_competitors: list[dict[str, Any]]
    all_nearby_businesses: list[dict[str, Any]]

    evidence: dict[str, Any]
    sensitivity_analysis: list[dict[str, Any]]

    data_lineage: list[dict[str, Any]]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "2.0-deterministic"

    def to_dict(self) -> dict:
        return asdict(self)
