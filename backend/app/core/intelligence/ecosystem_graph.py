"""
ecosystem_graph.py — Ecosystem Graph Read-Model Adapter.

Document 5: Interactive Business Ecosystem Intelligence Graph/Map.

Transforms validated outputs from MarketOpportunityEngine (Document 2) and
VillageIntelligencePipeline (Document 1) into a versioned graph data contract
suitable for dual-projection (Geographic + Topological) visualization.

Engineering principles:
    - This is a CONSUMER of validated analytical data, not a second source of truth.
    - Reuses existing UDYAM/intelligence contracts — never duplicates ingestion.
    - Zero coordinate fabrication: unmapped records go to unmappedEntities.
    - Relationship edges are derived, never claimed as confirmed transactions.
    - Workforce scale tier defaults to UNKNOWN unless validated data exists.
    - HHI uses the project's existing economic-sector diversification definition.
"""

from __future__ import annotations

import hashlib
import logging
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Any

from app.core.udyam.geography.distance import haversine_distance, calculate_distance
from app.core.udyam.activities.categories import (
    is_potential_competitor,
    is_potential_supply_chain,
    get_category_label,
    BUSINESS_CATEGORIES,
)
from app.core.intelligence.models import RelevanceClass
from app.core.intelligence.msme_density import aggregate_village_density

logger = logging.getLogger("udyam_saathi.ecosystem_graph")

# ── Constants ────────────────────────────────────────────────────────────────

SCHEMA_VERSION = "1.0"
MAX_RADIUS_KM = 50.0
MIN_RADIUS_KM = 0.5
MAX_NODE_CAP = 5000

# Sector color tokens (Document 5 Section 6.1)
SECTOR_COLORS = {
    "DAIRY": "#10B981",
    "FOOD_PROCESSING": "#0284C7",
    "FABRICATION": "#F59E0B",
    "FOOD_RETAIL": "#6366F1",
    "GENERAL_RETAIL": "#6366F1",
    "SERVICES": "#8B5CF6",
    "TAILORING": "#EC4899",
    "POULTRY": "#F97316",
    "GOAT_SHEEP": "#D97706",
    "TRANSPORT": "#64748B",
    "CONSTRUCTION": "#78716C",
    "MANUFACTURING": "#0EA5E9",
    "AGRICULTURE_SUPPORT": "#22C55E",
    "BEAUTY_WELLNESS": "#A855F7",
    "EDUCATION_TRAINING": "#3B82F6",
    "HEALTHCARE": "#EF4444",
    "UNKNOWN": "#94A3B8",
}


# ── Spatial Precision Mapping ────────────────────────────────────────────────

def _map_spatial_precision(coord_confidence: str, coord_source: str) -> str:
    """
    Map existing coordinate confidence and source into the Document 5
    spatial precision hierarchy: EXACT, LOCALITY, VILLAGE, PINCODE, UNMAPPED.

    Rule 2.2: Zero coordinate fabrication.
    Gate B: Administrative, Census, and geocoder sources provide village/locality
    centroids and must NEVER be claimed as enterprise-level EXACT coordinates.
    Only explicit verified enterprise GPS qualifies as EXACT.
    """
    conf = (coord_confidence or "").upper()
    src = (coord_source or "").lower()

    if conf == "UNKNOWN" or not conf or not src:
        return "UNMAPPED"
    if "gps" in src or "manual" in src or "verified" in src:
        return "EXACT" if conf == "HIGH" else "LOCALITY"
    if conf == "HIGH":
        if "census" in src or "admin" in src or "locality" in src:
            return "LOCALITY"
        return "LOCALITY"
    if conf == "MEDIUM":
        return "VILLAGE"
    if conf == "LOW":
        if "pincode" in src:
            return "PINCODE"
        return "VILLAGE"
    return "UNMAPPED"


def _map_spatial_confidence(coord_confidence: str) -> float:
    """Convert textual confidence to a numeric 0.0–1.0 score."""
    return {
        "HIGH": 0.9,
        "MEDIUM": 0.6,
        "LOW": 0.3,
        "UNKNOWN": 0.0,
    }.get((coord_confidence or "").upper(), 0.0)


# ── Graph Node Builder ───────────────────────────────────────────────────────

def _build_graph_node(
    business: dict[str, Any],
    center_lat: Optional[float],
    center_lon: Optional[float],
    index: int,
) -> tuple[Optional[dict], Optional[dict]]:
    """
    Transform a NearbyBusiness or CompetitorRecord dict into a Graph Node.

    Returns (node_dict, None) if mappable, or (None, unmapped_dict) if not.
    """
    lat = business.get("latitude")
    lon = business.get("longitude")
    coord_conf = business.get("coordinate_confidence") or business.get("geographic_confidence", "UNKNOWN")
    coord_src = business.get("coordinate_source", "unknown")

    precision = _map_spatial_precision(coord_conf, coord_src)
    confidence = _map_spatial_confidence(coord_conf)

    # Compute distance from center if coordinates exist
    distance_km = business.get("distance_km")
    if distance_km is None and lat is not None and lon is not None and center_lat is not None and center_lon is not None:
        distance_km = calculate_distance(center_lat, center_lon, lat, lon)
    if distance_km is not None:
        distance_km = round(distance_km, 2)

    # Parse activities
    activities_parsed = business.get("activities_parsed", [])
    activities = []
    for act in activities_parsed:
        if isinstance(act, dict):
            activities.append({
                "code": act.get("nic_code", ""),
                "label": act.get("activity_description", ""),
                "sector": act.get("normalized_category", "UNKNOWN"),
            })

    # Determine primary sector
    primary_cat = business.get("primary_category") or business.get("category", "UNKNOWN")
    sector = primary_cat.upper() if primary_cat else "UNKNOWN"

    # Registration date
    reg_date = business.get("registration_date")
    if reg_date and hasattr(reg_date, "isoformat"):
        reg_date = reg_date.isoformat()

    # Stable node ID from record fingerprint
    fingerprint = business.get("record_fingerprint", "")
    if not fingerprint:
        # Derive a deterministic ID
        raw = f"{business.get('enterprise_name', '')}|{business.get('pincode', '')}|{reg_date or ''}"
        fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    node_id = f"node-{fingerprint[:12]}"

    # Relevance class
    relevance = business.get("relevance_class", "UNKNOWN")

    node = {
        "id": node_id,
        "recordFingerprint": fingerprint,
        "enterpriseName": business.get("enterprise_name", ""),
        "state": business.get("state", ""),
        "district": business.get("district", ""),
        "pincode": business.get("pincode", ""),
        "address": business.get("communication_address", business.get("resolved_locality", "")),
        "activities": activities,
        "registrationDate": reg_date,
        "location": {
            "latitude": lat,
            "longitude": lon,
            "precision": precision,
            "confidence": confidence,
            "source": coord_src,
        },
        "scaleTier": "UNKNOWN",  # Rule 2.3: NEVER infer without validated data
        "scaleSource": None,
        "sector": sector,
        "sectorColor": SECTOR_COLORS.get(sector, "#94A3B8"),
        "sectorLabel": get_category_label(sector),
        "distanceKm": distance_km,
        "relevanceClass": relevance,
        "marketZone": business.get("market_zone", "UNMAPPED"),
        "dataQuality": {
            "verified": False,
            "warnings": [],
        },
        "provenance": {
            "sources": business.get("data_sources", ["UDYAM_MSME"]),
        },
    }

    # Add spatial warnings
    if precision == "PINCODE":
        node["dataQuality"]["warnings"].append(
            "Location uses pincode-level spatial approximation, not enterprise GPS."
        )

    # Route unmappable nodes
    if precision == "UNMAPPED" or lat is None or lon is None:
        return None, node

    return node, None


# ── Graph Edge Builder ────────────────────────────────────────────────────────

def _build_edges(
    nodes: list[dict],
    intent_primary_category: str,
    intent_related_categories: list[str],
) -> list[dict]:
    """
    Build deterministic derived edges between graph nodes.

    Competitor edges: nodes sharing the same sector as the intent's primary
    or direct categories, within spatial scope.

    Supply-chain edges: nodes whose sectors satisfy the configured deterministic
    complementary activity matrix.

    All edges are explicitly marked as DERIVED.
    """
    edges = []
    edge_set = set()  # Avoid duplicate edges

    primary_upper = intent_primary_category.upper() if intent_primary_category else ""
    related_upper = [c.upper() for c in intent_related_categories]

    for i, node_a in enumerate(nodes):
        sector_a = node_a.get("sector", "UNKNOWN")
        if sector_a == "UNKNOWN":
            continue

        for j, node_b in enumerate(nodes):
            if j <= i:
                continue
            sector_b = node_b.get("sector", "UNKNOWN")
            if sector_b == "UNKNOWN":
                continue

            edge_key = tuple(sorted([node_a["id"], node_b["id"]]))
            if edge_key in edge_set:
                continue

            # Check competitor relationship
            if is_potential_competitor(sector_a, sector_b):
                dist = None
                if (node_a["location"]["latitude"] is not None and
                        node_b["location"]["latitude"] is not None):
                    dist = calculate_distance(
                        node_a["location"]["latitude"], node_a["location"]["longitude"],
                        node_b["location"]["latitude"], node_b["location"]["longitude"],
                    )
                    if dist is not None:
                        dist = round(dist, 2)

                edges.append({
                    "id": f"edge-comp-{node_a['id'][-8:]}-{node_b['id'][-8:]}",
                    "source": node_a["id"],
                    "target": node_b["id"],
                    "relationshipType": "COMPETITOR",
                    "relationshipStatus": "DERIVED",
                    "confidence": 0.7,
                    "distanceKm": dist,
                    "ruleId": "COMPETITOR_ACTIVITY_V1",
                    "direction": "NONE",
                    "evidence": {
                        "sourceActivity": sector_a,
                        "targetActivity": sector_b,
                        "matchingRule": "Same normalized business category within spatial scope",
                        "spatialRule": "Both enterprises within catchment radius",
                    },
                })
                edge_set.add(edge_key)
                continue

            # Check supply-chain relationship
            if is_potential_supply_chain(sector_a, sector_b):
                dist = None
                if (node_a["location"]["latitude"] is not None and
                        node_b["location"]["latitude"] is not None):
                    dist = calculate_distance(
                        node_a["location"]["latitude"], node_a["location"]["longitude"],
                        node_b["location"]["latitude"], node_b["location"]["longitude"],
                    )
                    if dist is not None:
                        dist = round(dist, 2)

                edges.append({
                    "id": f"edge-sc-{node_a['id'][-8:]}-{node_b['id'][-8:]}",
                    "source": node_a["id"],
                    "target": node_b["id"],
                    "relationshipType": "SUPPLY_CHAIN",
                    "relationshipStatus": "DERIVED",
                    "confidence": 0.5,
                    "distanceKm": dist,
                    "ruleId": "SUPPLY_CHAIN_ACTIVITY_MATRIX_V1",
                    "direction": "NONE",
                    "evidence": {
                        "sourceActivity": sector_a,
                        "targetActivity": sector_b,
                        "matchingRule": "Deterministic activity-complementarity pair from configured matrix",
                        "spatialRule": "Both enterprises within catchment radius",
                    },
                })
                edge_set.add(edge_key)

    return edges


# ── Temporal Metadata Builder ─────────────────────────────────────────────────

def _build_temporal_metadata(nodes: list[dict]) -> dict:
    """
    Compute data-driven temporal metadata from actual RegistrationDate values.
    Never hard-code 2018 as the earliest year (Rule 2.5).
    """
    years = []
    missing_dates = 0

    for node in nodes:
        rd = node.get("registrationDate")
        if rd:
            try:
                year = int(str(rd)[:4])
                if 1900 < year < 2100:
                    years.append(year)
                else:
                    missing_dates += 1
            except (ValueError, TypeError):
                missing_dates += 1
        else:
            missing_dates += 1

    if not years:
        return {
            "minYear": None,
            "maxYear": None,
            "selectedMaxYear": None,
            "yearlyRegistrations": {},
            "registrationVelocity": [],
            "missingDates": missing_dates,
            "status": "NO_TEMPORAL_DATA",
        }

    year_counts = Counter(years)
    min_year = min(years)
    max_year = max(years)

    yearly = {str(y): year_counts.get(y, 0) for y in range(min_year, max_year + 1)}

    # Registration velocity (year-over-year change)
    velocity = []
    sorted_years = sorted(yearly.keys())
    for i in range(1, len(sorted_years)):
        prev = int(sorted_years[i - 1])
        curr = int(sorted_years[i])
        prev_count = yearly[sorted_years[i - 1]]
        curr_count = yearly[sorted_years[i]]
        velocity.append({
            "year": curr,
            "registrations": curr_count,
            "change": curr_count - prev_count,
            "label": "Registration acceleration" if curr_count > prev_count else "Registration deceleration",
        })

    return {
        "minYear": min_year,
        "maxYear": max_year,
        "selectedMaxYear": max_year,
        "yearlyRegistrations": yearly,
        "registrationVelocity": velocity,
        "missingDates": missing_dates,
        "status": "AVAILABLE",
    }


# ── Metrics Builder ──────────────────────────────────────────────────────────

def _build_metrics(
    nodes: list[dict],
    edges: list[dict],
    unmapped: list[dict],
    supply_metrics: Optional[dict],
    radius_km: float,
) -> dict:
    """
    Compile graph-level metrics, reusing existing validated values.
    Each metric carries definition, source, and radius.
    """
    total_mapped = len(nodes)
    total_unmapped = len(unmapped)
    competitor_edges = [e for e in edges if e["relationshipType"] == "COMPETITOR"]
    supply_chain_edges = [e for e in edges if e["relationshipType"] == "SUPPLY_CHAIN"]

    # Sector distribution
    sector_counts = Counter(n.get("sector", "UNKNOWN") for n in nodes)

    metrics = {
        "totalMappedEnterprises": {
            "value": total_mapped,
            "definition": "Count of enterprises with defensible geographic coordinates within catchment",
            "radiusKm": radius_km,
            "source": "ecosystem-graph-adapter",
            "status": "AVAILABLE",
        },
        "totalUnmappedEnterprises": {
            "value": total_unmapped,
            "definition": "Count of enterprises without defensible coordinates",
            "radiusKm": radius_km,
            "source": "ecosystem-graph-adapter",
            "status": "AVAILABLE",
        },
        "competitorRelationships": {
            "value": len(competitor_edges),
            "definition": "Count of derived competitor relationships based on activity classification",
            "radiusKm": radius_km,
            "source": "COMPETITOR_ACTIVITY_V1 rule",
            "status": "AVAILABLE" if competitor_edges else "NONE_FOUND",
        },
        "supplyChainRelationships": {
            "value": len(supply_chain_edges),
            "definition": "Count of derived supply-chain relationships from activity complementarity matrix",
            "radiusKm": radius_km,
            "source": "SUPPLY_CHAIN_ACTIVITY_MATRIX_V1 rule",
            "status": "AVAILABLE" if supply_chain_edges else "NONE_FOUND",
        },
        "sectorDistribution": {
            "value": dict(sector_counts),
            "definition": "Distribution of enterprises by normalized business category",
            "radiusKm": radius_km,
            "source": "NIC-to-category mapping",
            "status": "AVAILABLE",
        },
    }

    # Reuse existing HHI from supply metrics if available
    if supply_metrics:
        hhi_val = supply_metrics.get("hhi_concentration_index", 0.0)
        metrics["hhi"] = {
            "name": "HHI",
            "value": hhi_val,
            "semanticDefinition": "existing-project-sector-diversification-HHI",
            "radiusKm": radius_km,
            "source": "market-intelligence-engine",
            "status": "AVAILABLE" if hhi_val > 0 else "INSUFFICIENT_DATA",
            "interpretation": (
                "Competitive" if hhi_val < 1500
                else "Moderate" if hhi_val < 2500
                else "Concentrated"
            ) if hhi_val > 0 else "Insufficient data",
        }

    return metrics


# ── Warnings Builder ─────────────────────────────────────────────────────────

def _build_warnings(nodes: list[dict], unmapped: list[dict], edges: list[dict]) -> list[dict]:
    """Generate provenance and data-quality warnings per Document 5 Section 18."""
    warnings = []

    # Check for pincode approximations
    pincode_nodes = [n for n in nodes if n.get("location", {}).get("precision") == "PINCODE"]
    if pincode_nodes:
        warnings.append({
            "code": "PINCODE_APPROXIMATION",
            "severity": "INFO",
            "message": f"{len(pincode_nodes)} enterprise location(s) use pincode-level spatial anchors, not exact GPS coordinates.",
            "count": len(pincode_nodes),
        })

    # Unmapped enterprises
    if unmapped:
        warnings.append({
            "code": "UNMAPPED_ENTERPRISES",
            "severity": "WARNING",
            "message": f"{len(unmapped)} enterprise(s) could not be placed on the map due to missing or unresolvable coordinates.",
            "count": len(unmapped),
        })

    # Supply chain derived relationship disclaimer
    supply_edges = [e for e in edges if e["relationshipType"] == "SUPPLY_CHAIN"]
    if supply_edges:
        warnings.append({
            "code": "SUPPLY_CHAIN_IS_DERIVED",
            "severity": "INFO",
            "message": "Supply-chain links are activity-based inferred relationships, not observed transactions.",
        })

    # Competitor derived relationship disclaimer
    comp_edges = [e for e in edges if e["relationshipType"] == "COMPETITOR"]
    if comp_edges:
        warnings.append({
            "code": "COMPETITOR_IS_DERIVED",
            "severity": "INFO",
            "message": "Competitor relationships are derived from activity/sector classification, not confirmed commercial competition.",
        })

    return warnings


# ── Validation ───────────────────────────────────────────────────────────────

def validate_ecosystem_graph_request(
    target_lat: Optional[float],
    target_lon: Optional[float],
    radius_km: float,
) -> list[str]:
    """Validate input parameters. Returns list of error strings (empty if valid)."""
    errors = []

    if target_lat is not None and not (-90 <= target_lat <= 90):
        errors.append(f"target_lat must be between -90 and 90, got {target_lat}")
    if target_lon is not None and not (-180 <= target_lon <= 180):
        errors.append(f"target_lon must be between -180 and 180, got {target_lon}")
    if radius_km < MIN_RADIUS_KM or radius_km > MAX_RADIUS_KM:
        errors.append(f"radius_km must be between {MIN_RADIUS_KM} and {MAX_RADIUS_KM}, got {radius_km}")

    return errors


# ── Main Adapter ──────────────────────────────────────────────────────────────

class EcosystemGraphAdapter:
    """
    Adapter that transforms validated MarketOpportunityEngine outputs
    into the versioned ecosystem graph data contract.

    This is a read-model / projection layer. It NEVER duplicates
    UDYAM ingestion, MSME classification, or market-intelligence pipelines.
    """

    def __init__(self, opportunity_engine=None, udyam_pipeline=None):
        self.opportunity_engine = opportunity_engine
        self.udyam_pipeline = udyam_pipeline

    def build_graph_from_opportunity_report(
        self,
        report: dict[str, Any],
        radius_km: float = 10.0,
        visualization_radius_km: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Build the ecosystem graph response from a MarketOpportunityReport dict.

        Args:
            report: The output of MarketOpportunityEngine.analyze_opportunity().to_dict()
            radius_km: The analysis radius used by the scoring engine.
            visualization_radius_km: Optional visual catchment radius (does NOT
                alter market-scoring semantics — Rule 2.6).
        """
        viz_radius = visualization_radius_km or radius_km

        # Extract center from target_location
        target = report.get("target_location", {})
        center_lat = target.get("latitude")
        center_lon = target.get("longitude")

        if center_lat is None or center_lon is None:
            dist = target.get("district", "")
            st = target.get("state", "")
            if dist:
                from app.core.udyam.geography.gazetteer import Gazetteer
                g = Gazetteer()
                centroid = g.get_district_centroid(st, dist)
                if centroid:
                    center_lat, center_lon = centroid

        # Extract intent info
        intent_info = report.get("business_intent", {})
        primary_category = intent_info.get("primary_category", "UNKNOWN")
        related_categories = intent_info.get("related_categories", [])

        # Combine classified competitors and all nearby businesses (deduplicate by fingerprint)
        all_businesses = []
        seen_fps = set()

        for biz in report.get("classified_competitors", []):
            fp = biz.get("record_fingerprint", "")
            if fp and fp not in seen_fps:
                seen_fps.add(fp)
                all_businesses.append(biz)

        for biz in report.get("all_nearby_businesses", []):
            fp = biz.get("record_fingerprint", "")
            if fp and fp not in seen_fps:
                seen_fps.add(fp)
                all_businesses.append(biz)

        # Build nodes and unmapped entities
        nodes = []
        unmapped_entities = []

        for idx, biz in enumerate(all_businesses):
            node, unmapped = _build_graph_node(biz, center_lat, center_lon, idx)
            if node is not None:
                # Apply visualization radius filter (Rule 2.6: does not alter scoring)
                if node["distanceKm"] is not None and node["distanceKm"] <= viz_radius:
                    nodes.append(node)
                elif node["distanceKm"] is None:
                    unmapped_entities.append(node)
                elif node["distanceKm"] > viz_radius:
                    pass  # Outside visual catchment, excluded from visualization
            elif unmapped is not None:
                unmapped_entities.append(unmapped)

        # Cap node count for performance
        if len(nodes) > MAX_NODE_CAP:
            logger.warning(f"Node count {len(nodes)} exceeds cap {MAX_NODE_CAP}, truncating.")
            nodes = sorted(nodes, key=lambda n: n.get("distanceKm") or 999)[:MAX_NODE_CAP]

        # Build edges
        edges = _build_edges(nodes, primary_category, related_categories)

        # Build temporal metadata
        all_nodes_for_temporal = nodes + unmapped_entities
        temporal = _build_temporal_metadata(all_nodes_for_temporal)

        # Build metrics
        supply_metrics = report.get("supply_metrics", {})
        metrics = _build_metrics(nodes, edges, unmapped_entities, supply_metrics, radius_km)

        # Build warnings
        warnings = _build_warnings(nodes, unmapped_entities, edges)

        # Build village-level MSME density aggregation (Step 1 heatmap)
        village_density = aggregate_village_density(
            nodes=nodes,
            unmapped=unmapped_entities,
            center_lat=center_lat,
            center_lon=center_lon,
        )

        # Density layer status (Gate F)
        density_status = "AVAILABLE" if len(nodes) >= 10 else "INSUFFICIENT_DATA"

        # Opportunity layer status (Gate G: must derive from Document 2 analytical evidence)
        # SATURATED_MARKET and CONSTRAINED_MARKET must NEVER be presented as attractive white space
        opp_indicators = report.get("opportunity_indicators", {})
        rec = report.get("recommendation", "UNKNOWN")
        composite_score = report.get("composite_score", 0.0)
        has_demand_evidence = bool(report.get("demand_features", {}).get("has_sufficient_demand_evidence", False))

        if rec in ("SATURATED_MARKET", "CONSTRAINED_MARKET"):
            opportunity_status = "UNAVAILABLE"
            opportunity_msg = f"Opportunity overlay suppressed: Market is classified as {rec}. High competitor density or infrastructure constraints prevent white-space claims."
        elif not has_demand_evidence or len(nodes) < 3:
            opportunity_status = "INSUFFICIENT_DATA"
            opportunity_msg = "Opportunity overlay unavailable: Insufficient demand/infrastructure evidence or sparse enterprise presence."
        else:
            opportunity_status = "AVAILABLE"
            opportunity_msg = f"Opportunity overlay computed from validated demand proxy and competitor presence (Composite Score: {composite_score:.1f})."

        return {
            "schemaVersion": SCHEMA_VERSION,
            "catchment": {
                "center": {
                    "latitude": center_lat,
                    "longitude": center_lon,
                    "source": target.get("source", ""),
                },
                "radiusKm": viz_radius,
                "scoringRadiusKm": radius_km,
                "distanceMethod": "HAVERSINE",
            },
            "nodes": nodes,
            "edges": edges,
            "unmappedEntities": unmapped_entities,
            "metrics": metrics,
            "temporal": temporal,
            "layers": {
                "catchmentRings": {"status": "AVAILABLE" if center_lat else "UNAVAILABLE"},
                "nodes": {"status": "AVAILABLE" if nodes else "EMPTY"},
                "relationships": {"status": "AVAILABLE" if edges else "NONE_FOUND"},
                "density": {
                    "status": density_status,
                    "message": (
                        f"Density computed from {len(nodes)} mapped observations."
                        if density_status == "AVAILABLE"
                        else f"Only {len(nodes)} mapped enterprise(s) — insufficient for reliable density surface."
                    ),
                },
                "opportunities": {
                    "status": opportunity_status,
                    "message": opportunity_msg,
                    "recommendation": rec,
                    "compositeScore": composite_score,
                },
            },
            "provenance": {
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "engine": "ecosystem-graph-adapter-v1.0",
                "upstreamVersion": report.get("version", "unknown"),
                "dataLineage": report.get("data_lineage", []),
            },
            "warnings": warnings,
            "intent": {
                "primaryCategory": primary_category,
                "displayName": intent_info.get("display_name", ""),
                "relatedCategories": related_categories,
            },
            "evidence": report.get("evidence", {}),
            "villageDensity": village_density,
        }

    def build_graph(
        self,
        state: str,
        district: str,
        village: str = "",
        target_lat: Optional[float] = None,
        target_lon: Optional[float] = None,
        business_intent: str = "dairy",
        radius_km: float = 10.0,
        visualization_radius_km: Optional[float] = None,
        pincode: Optional[str] = None,
        max_records: Optional[int] = 1000,
        snapshot_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        End-to-end: run opportunity analysis then build the graph.
        """
        if not self.opportunity_engine:
            from app.core.intelligence.engine import MarketOpportunityEngine
            from app.core.udyam.pipeline import VillageIntelligencePipeline
            pipeline = self.udyam_pipeline or VillageIntelligencePipeline()
            self.opportunity_engine = MarketOpportunityEngine(udyam_pipeline=pipeline)

        t_lat = target_lat
        t_lon = target_lon
        if t_lat is None or t_lon is None:
            from app.core.udyam.geography.gazetteer import Gazetteer
            g = Gazetteer()
            # 1. Attempt village-level coordinate resolution first
            if village and village.strip() and village.strip().upper() != "N/A":
                v_coords = g.resolve_locality_coords(village=village, district=district, state=state)
                if v_coords:
                    t_lat, t_lon = v_coords
            # 2. Fall back to district centroid if village resolution was not found
            if (t_lat is None or t_lon is None) and district:
                centroid = g.get_district_centroid(state, district)
                if centroid:
                    t_lat, t_lon = centroid

        report = self.opportunity_engine.analyze_opportunity(
            state=state,
            district=district,
            village=village,
            target_lat=t_lat,
            target_lon=t_lon,
            business_intent=business_intent,
            radius_km=radius_km,
            pincode=pincode,
            max_records=max_records,
            snapshot_id=snapshot_id,
        )

        return self.build_graph_from_opportunity_report(
            report=report.to_dict(),
            radius_km=radius_km,
            visualization_radius_km=visualization_radius_km,
        )
