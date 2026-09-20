"""
relevance.py — 5-Level Competitor Relevance Engine.

Document 2, Sections 9, 10 & 11.

Enforces the non-negotiable principle: "Nearby ≠ Competitor".
Given a candidate enterprise and a target business intent, classifies
relevance into:
    - DIRECT_COMPETITOR
    - RELATED_BUSINESS
    - INDIRECT_COMPETITOR
    - NON_RELEVANT
    - UNKNOWN

Every classification includes an explicit traceable reason and confidence score.
"""

from __future__ import annotations
import logging
from typing import Optional, Any
from .models import RelevanceClass, CompetitorRecord, BusinessIntent

logger = logging.getLogger("udyam_saathi.intelligence.relevance")


def classify_competitor_relevance(
    business: dict[str, Any],
    intent: BusinessIntent,
) -> CompetitorRecord:
    """
    Classify a single enterprise's competitive relevance to the proposed intent.

    Args:
        business: Dict representation of NearbyBusiness from Document 1.
        intent: The proposed BusinessIntent.

    Returns:
        Structured CompetitorRecord with explicit classification and reason.
    """
    cat = business.get("primary_category", "UNKNOWN").upper().strip()
    cat_label = business.get("primary_category_label", "Unclassified")
    cat_conf = business.get("category_confidence", "UNKNOWN")
    ent_name = business.get("enterprise_name", "")
    acts = business.get("activities_parsed", [])
    first_act_desc = acts[0].get("activity_description", "") if acts else business.get("activities_raw", "")
    nic_code = acts[0].get("nic_code", "") if acts else ""

    lat = business.get("latitude")
    lon = business.get("longitude")
    coord_conf = business.get("coordinate_confidence", "UNKNOWN")
    coord_src = business.get("coordinate_source", "")
    sources = business.get("data_sources", ["UDYAM_MSME"])

    # Check for Unknown category
    if cat == "UNKNOWN" or not cat:
        return CompetitorRecord(
            enterprise_name=ent_name,
            record_fingerprint=business.get("record_fingerprint", ""),
            category="UNKNOWN",
            category_label="Unclassified",
            relevance_class=RelevanceClass.UNKNOWN.value,
            relevance_reason="Activity text could not be mapped to known ontology with sufficient confidence",
            relevance_confidence="UNKNOWN",
            distance_km=business.get("distance_km"),
            market_zone=business.get("market_zone", "UNMAPPED"),
            resolved_locality=business.get("resolved_locality", ""),
            geographic_confidence=coord_conf,
            registration_date=business.get("registration_date"),
            nic_code=nic_code,
            activity_description=first_act_desc,
            data_sources=sources,
            latitude=lat,
            longitude=lon,
            coordinate_confidence=coord_conf,
            coordinate_source=coord_src,
            activities_parsed=acts,
        )

    # 1. DIRECT_COMPETITOR Check
    if cat in [c.upper() for c in intent.direct_categories] or cat == intent.primary_category.upper():
        conf = "HIGH" if cat_conf == "HIGH" else "MEDIUM"
        return CompetitorRecord(
            enterprise_name=ent_name,
            record_fingerprint=business.get("record_fingerprint", ""),
            category=cat,
            category_label=cat_label,
            relevance_class=RelevanceClass.DIRECT_COMPETITOR.value,
            relevance_reason=f"Matches direct target business category ({cat_label})",
            relevance_confidence=conf,
            distance_km=business.get("distance_km"),
            market_zone=business.get("market_zone", "UNMAPPED"),
            resolved_locality=business.get("resolved_locality", ""),
            geographic_confidence=coord_conf,
            registration_date=business.get("registration_date"),
            nic_code=nic_code,
            activity_description=first_act_desc,
            data_sources=sources,
            latitude=lat,
            longitude=lon,
            coordinate_confidence=coord_conf,
            coordinate_source=coord_src,
            activities_parsed=acts,
        )

    # 2. RELATED_BUSINESS Check (Supply chain or complementary ecosystem)
    if cat in [c.upper() for c in intent.related_categories]:
        return CompetitorRecord(
            enterprise_name=ent_name,
            record_fingerprint=business.get("record_fingerprint", ""),
            category=cat,
            category_label=cat_label,
            relevance_class=RelevanceClass.RELATED_BUSINESS.value,
            relevance_reason=f"Operates in related supply-chain / complementary category ({cat_label})",
            relevance_confidence="HIGH",
            distance_km=business.get("distance_km"),
            market_zone=business.get("market_zone", "UNMAPPED"),
            resolved_locality=business.get("resolved_locality", ""),
            geographic_confidence=coord_conf,
            registration_date=business.get("registration_date"),
            nic_code=nic_code,
            activity_description=first_act_desc,
            data_sources=sources,
            latitude=lat,
            longitude=lon,
            coordinate_confidence=coord_conf,
            coordinate_source=coord_src,
            activities_parsed=acts,
        )

    # 3. Keyword Match on enterprise name / activity description (Possible indirect competitor)
    ent_text = f"{ent_name} {first_act_desc}".upper()
    matching_kws = [kw for kw in intent.search_keywords if kw.upper() in ent_text]
    if matching_kws:
        return CompetitorRecord(
            enterprise_name=ent_name,
            record_fingerprint=business.get("record_fingerprint", ""),
            category=cat,
            category_label=cat_label,
            relevance_class=RelevanceClass.INDIRECT_COMPETITOR.value,
            relevance_reason=f"Shares commercial keywords with intent: {', '.join(matching_kws[:3])}",
            relevance_confidence="MEDIUM",
            distance_km=business.get("distance_km"),
            market_zone=business.get("market_zone", "UNMAPPED"),
            resolved_locality=business.get("resolved_locality", ""),
            geographic_confidence=coord_conf,
            registration_date=business.get("registration_date"),
            nic_code=nic_code,
            activity_description=first_act_desc,
            data_sources=sources,
            latitude=lat,
            longitude=lon,
            coordinate_confidence=coord_conf,
            coordinate_source=coord_src,
            activities_parsed=acts,
        )

    # 4. NON_RELEVANT
    return CompetitorRecord(
        enterprise_name=ent_name,
        record_fingerprint=business.get("record_fingerprint", ""),
        category=cat,
        category_label=cat_label,
        relevance_class=RelevanceClass.NON_RELEVANT.value,
        relevance_reason="No meaningful competitive or supply-chain connection to target intent",
        relevance_confidence="HIGH",
        distance_km=business.get("distance_km"),
        market_zone=business.get("market_zone", "UNMAPPED"),
        resolved_locality=business.get("resolved_locality", ""),
        geographic_confidence=coord_conf,
        registration_date=business.get("registration_date"),
        nic_code=nic_code,
        activity_description=first_act_desc,
        data_sources=sources,
        latitude=lat,
        longitude=lon,
        coordinate_confidence=coord_conf,
        coordinate_source=coord_src,
        activities_parsed=acts,
    )


def classify_records_batch(
    businesses: list[dict[str, Any]],
    intent: BusinessIntent,
) -> list[CompetitorRecord]:
    """Classify a list of businesses against a target intent."""
    return [classify_competitor_relevance(b, intent) for b in businesses]
