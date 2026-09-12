"""
supply.py — Supply-Side Metrics & Market Concentration Engine.

Document 2, Sections 12-16.

Calculates distance-aware competition metrics, market zone distributions,
target locality geographic concentration, category market shares, and
the Herfindahl-Hirschman Index (HHI).
"""

from __future__ import annotations
import statistics
import logging
from typing import Optional
from collections import Counter

from .models import CompetitorRecord, RelevanceClass, SupplyMetrics

logger = logging.getLogger("udyam_saathi.intelligence.supply")


def compute_supply_metrics(
    records: list[CompetitorRecord],
    target_locality: str = "",
    population: Optional[int] = None,
) -> SupplyMetrics:
    """
    Calculate comprehensive supply-side metrics per Sections 12-16.

    Args:
        records: List of classified CompetitorRecord objects.
        target_locality: Target village/locality name for concentration check.
        population: Optional projected population for density calculation.

    Returns:
        Populated SupplyMetrics object.
    """
    total = len(records)
    direct = [r for r in records if r.relevance_class == RelevanceClass.DIRECT_COMPETITOR.value]
    related = [r for r in records if r.relevance_class == RelevanceClass.RELATED_BUSINESS.value]
    indirect = [r for r in records if r.relevance_class == RelevanceClass.INDIRECT_COMPETITOR.value]
    non_relevant = [r for r in records if r.relevance_class == RelevanceClass.NON_RELEVANT.value]
    unknown = [r for r in records if r.relevance_class == RelevanceClass.UNKNOWN.value]

    # Distance metrics for direct competitors
    direct_distances = [r.distance_km for r in direct if r.distance_km is not None]
    nearest_direct = min(direct_distances) if direct_distances else None
    median_direct = statistics.median(direct_distances) if direct_distances else None

    # Distance metrics for related businesses
    related_distances = [r.distance_km for r in related if r.distance_km is not None]
    nearest_related = min(related_distances) if related_distances else None

    # Market zone distribution of direct competitors
    core_5km = sum(1 for r in direct if r.market_zone == "CORE_5KM")
    nearby_10km = sum(1 for r in direct if r.market_zone == "NEARBY_10KM")
    outside_10km = sum(1 for r in direct if r.market_zone == "OUTSIDE_10KM")
    unmapped = sum(1 for r in direct if r.market_zone == "UNMAPPED")

    # Target locality geographic concentration
    target_norm = target_locality.upper().strip() if target_locality else ""
    in_target = 0
    if target_norm:
        for r in direct:
            loc_norm = r.resolved_locality.upper().strip()
            if loc_norm and (target_norm in loc_norm or loc_norm in target_norm):
                in_target += 1

    share_target_pct = round((in_target / len(direct) * 100.0), 1) if direct else 0.0

    # Category concentration & share
    category_share = round((len(direct) / total * 100.0), 1) if total > 0 else 0.0

    # Economic Sector Diversification HHI (Herfindahl-Hirschman Index across observed categories)
    # Measures whether the local rural enterprise cluster is diversified or a mono-industry cluster.
    # Note: Turnover HHI is not possible from public OGD data as private enterprise revenue is confidential.
    categories = [r.category for r in records if r.category and r.category != "UNKNOWN"]
    cat_counts = Counter(categories)
    hhi = 0.0
    if cat_counts:
        tot_known = sum(cat_counts.values())
        for count in cat_counts.values():
            pct = (count / tot_known) * 100.0
            hhi += pct * pct

    # Market density per 1,000 residents
    density_per_1k = None
    if population and population > 0:
        density_per_1k = round((total / population) * 1000.0, 2)

    return SupplyMetrics(
        total_nearby_enterprises=total,
        direct_competitors_count=len(direct),
        related_businesses_count=len(related),
        indirect_competitors_count=len(indirect),
        non_relevant_count=len(non_relevant),
        unknown_relevance_count=len(unknown),
        nearest_direct_competitor_km=round(nearest_direct, 2) if nearest_direct is not None else None,
        nearest_related_business_km=round(nearest_related, 2) if nearest_related is not None else None,
        median_direct_competitor_distance_km=round(median_direct, 2) if median_direct is not None else None,
        direct_in_core_5km=core_5km,
        direct_in_nearby_10km=nearby_10km,
        direct_outside_10km=outside_10km,
        direct_unmapped=unmapped,
        direct_in_target_locality=in_target,
        share_in_target_locality_pct=share_target_pct,
        category_share_pct=category_share,
        hhi_concentration_index=round(hhi, 1),
        businesses_per_1000_people=density_per_1k,
    )
