"""
test_ecosystem_graph.py — Comprehensive Test Suite for Ecosystem Graph Adapter.

Document 5: Interactive Business Ecosystem Intelligence Graph/Map.

Tests:
    - Geometry: Haversine, radius boundaries, coordinate validation
    - Data integrity: zero fabrication, spatial precision, workforce tier
    - Relationships: deterministic competitor/supply-chain edges
    - Temporal: data-driven min/max year, missing dates
    - Metrics: HHI semantics, radius-specific counts
    - API validation: structured 400 errors
    - Performance: 500+ node benchmark
    - Golden dataset: deterministic fixture

TEST FIXTURE — NOT REAL BUSINESS DATA
"""

import os
import sys
import time
import unittest
from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
CORE_DIR = BACKEND_DIR / "app" / "core"
for p in (str(CORE_DIR), str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.intelligence.ecosystem_graph import (
    EcosystemGraphAdapter,
    _build_graph_node,
    _build_edges,
    _build_temporal_metadata,
    _build_metrics,
    _build_warnings,
    _map_spatial_precision,
    _map_spatial_confidence,
    validate_ecosystem_graph_request,
    SCHEMA_VERSION,
    MAX_RADIUS_KM,
    MIN_RADIUS_KM,
)
from app.core.udyam.geography.distance import haversine_distance, calculate_distance


# ── Golden Test Dataset ───────────────────────────────────────────────────────
# TEST FIXTURE — NOT REAL BUSINESS DATA

GOLDEN_CENTER_LAT = 17.9276
GOLDEN_CENTER_LON = 78.2344

GOLDEN_BUSINESSES = [
    {
        "record_fingerprint": "fp_dairy_exact_001",
        "enterprise_name": "TEST Mauli Dairy Farm",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502001",
        "registration_date": "2022-06-15",
        "communication_address": "Test Village, Medak",
        "latitude": 17.9300,
        "longitude": 78.2370,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "government_census",
        "distance_km": 0.35,
        "market_zone": "CORE_5KM",
        "primary_category": "DAIRY",
        "primary_category_label": "Dairy & Milk Products",
        "category_confidence": "HIGH",
        "activities_parsed": [{"nic_code": "1050", "activity_description": "Dairy products manufacture", "normalized_category": "DAIRY"}],
        "relevance_class": "DIRECT_COMPETITOR",
        "data_sources": ["UDYAM_MSME"],
    },
    {
        "record_fingerprint": "fp_dairy_pincode_002",
        "enterprise_name": "TEST Shree Ganesh Milk Chilling",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502001",
        "registration_date": "2021-11-03",
        "communication_address": "Near Bus Stand, Medak",
        "latitude": 17.9350,
        "longitude": 78.2400,
        "coordinate_confidence": "LOW",
        "coordinate_source": "pincode_directory",
        "distance_km": 1.05,
        "market_zone": "CORE_5KM",
        "primary_category": "DAIRY",
        "primary_category_label": "Dairy & Milk Products",
        "category_confidence": "HIGH",
        "activities_parsed": [{"nic_code": "1050", "activity_description": "Milk chilling plant", "normalized_category": "DAIRY"}],
        "relevance_class": "DIRECT_COMPETITOR",
        "data_sources": ["UDYAM_MSME"],
    },
    {
        "record_fingerprint": "fp_food_retail_003",
        "enterprise_name": "TEST Laxmi Kirana Store",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502002",
        "registration_date": "2020-03-22",
        "communication_address": "Main Road, Medak",
        "latitude": 17.9280,
        "longitude": 78.2340,
        "coordinate_confidence": "MEDIUM",
        "coordinate_source": "geocoder",
        "distance_km": 0.05,
        "market_zone": "CORE_5KM",
        "primary_category": "FOOD_RETAIL",
        "primary_category_label": "Food & Grocery Retail",
        "category_confidence": "MEDIUM",
        "activities_parsed": [{"nic_code": "4711", "activity_description": "Retail grocery store", "normalized_category": "FOOD_RETAIL"}],
        "relevance_class": "RELATED_BUSINESS",
        "data_sources": ["UDYAM_MSME"],
    },
    {
        "record_fingerprint": "fp_fabrication_004",
        "enterprise_name": "TEST Ram Steel Fabricators",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502003",
        "registration_date": "2019-08-10",
        "communication_address": "Industrial Area, Medak",
        "latitude": 17.9400,
        "longitude": 78.2500,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "government_admin",
        "distance_km": 2.1,
        "market_zone": "CORE_5KM",
        "primary_category": "FABRICATION",
        "primary_category_label": "Metal Fabrication & Welding",
        "category_confidence": "HIGH",
        "activities_parsed": [{"nic_code": "2511", "activity_description": "Structural metal fabrication", "normalized_category": "FABRICATION"}],
        "relevance_class": "NON_RELEVANT",
        "data_sources": ["UDYAM_MSME"],
    },
    {
        # UNMAPPED enterprise — no coordinates
        "record_fingerprint": "fp_unmapped_005",
        "enterprise_name": "TEST Unknown Location Enterprise",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502004",
        "registration_date": None,
        "communication_address": "Somewhere, Medak",
        "latitude": None,
        "longitude": None,
        "coordinate_confidence": "UNKNOWN",
        "coordinate_source": "unknown",
        "distance_km": None,
        "market_zone": "UNMAPPED",
        "primary_category": "UNKNOWN",
        "primary_category_label": "Unclassified",
        "category_confidence": "UNKNOWN",
        "activities_parsed": [],
        "relevance_class": "UNKNOWN",
        "data_sources": ["UDYAM_MSME"],
    },
    {
        "record_fingerprint": "fp_agri_006",
        "enterprise_name": "TEST Kisaan Agri Suppliers",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502001",
        "registration_date": "2023-01-20",
        "communication_address": "Agri Market, Medak",
        "latitude": 17.9310,
        "longitude": 78.2360,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "government_census",
        "distance_km": 0.42,
        "market_zone": "CORE_5KM",
        "primary_category": "AGRICULTURE_SUPPORT",
        "primary_category_label": "Agriculture Support Services",
        "category_confidence": "HIGH",
        "activities_parsed": [{"nic_code": "0111", "activity_description": "Farm seed supply", "normalized_category": "AGRICULTURE_SUPPORT"}],
        "relevance_class": "RELATED_BUSINESS",
        "data_sources": ["UDYAM_MSME"],
    },
]

GOLDEN_REPORT = {
    "target_location": {
        "name": "Balanagar",
        "state": "TELANGANA",
        "district": "MEDAK",
        "latitude": GOLDEN_CENTER_LAT,
        "longitude": GOLDEN_CENTER_LON,
        "source": "government_census",
        "confidence": "HIGH",
    },
    "business_intent": {
        "intent_id": "dairy",
        "display_name": "Dairy & Milk Products",
        "primary_category": "DAIRY",
        "direct_categories": ["DAIRY"],
        "related_categories": ["FOOD_RETAIL", "FOOD_PROCESSING", "AGRICULTURE_SUPPORT"],
        "search_keywords": ["DAIRY", "MILK", "GHEE", "PANEER"],
    },
    "recommendation": "MODERATE_OPPORTUNITY",
    "composite_score": 62.5,
    "confidence": "MEDIUM",
    "supply_metrics": {
        "total_nearby_enterprises": 6,
        "direct_competitors_count": 2,
        "hhi_concentration_index": 2800.0,
        "businesses_per_1000_people": 3.2,
    },
    "demand_features": {
        "population": 5000,
        "households": 1042,
        "has_sufficient_demand_evidence": True,
    },
    "opportunity_indicators": {
        "supply_gap_score": 55.0,
        "accessibility_gap_score": 60.0,
        "demand_support_score": 65.0,
    },
    "classified_competitors": GOLDEN_BUSINESSES[:2],
    "all_nearby_businesses": GOLDEN_BUSINESSES,
    "evidence": {
        "recommendation": "MODERATE_OPPORTUNITY",
        "composite_score": 62.5,
        "confidence": "MEDIUM",
        "top_positive_drivers": ["Growing population"],
        "top_risk_factors": ["Moderate competition"],
    },
    "sensitivity_analysis": [],
    "data_lineage": [{"source": "UDYAM_MSME", "year": "2024"}],
    "generated_at": "2026-01-01T00:00:00Z",
    "version": "2.0-deterministic",
}


class TestSpatialPrecision(unittest.TestCase):
    """Document 5, Section 2.1 & Gate B: Spatial precision hierarchy."""

    def test_exact_precision_from_verified_gps(self):
        """Only explicit enterprise GPS/manual verification qualifies as EXACT."""
        self.assertEqual(_map_spatial_precision("HIGH", "verified_gps"), "EXACT")
        self.assertEqual(_map_spatial_precision("HIGH", "manual_survey_gps"), "EXACT")

    def test_locality_precision_from_census(self):
        """Census and admin directories provide village/locality centroids, NOT enterprise GPS."""
        self.assertEqual(_map_spatial_precision("HIGH", "government_census"), "LOCALITY")

    def test_locality_precision_from_admin(self):
        self.assertEqual(_map_spatial_precision("HIGH", "government_admin"), "LOCALITY")

    def test_locality_precision_from_geocoder(self):
        self.assertEqual(_map_spatial_precision("HIGH", "geocoder"), "LOCALITY")

    def test_village_precision_from_medium(self):
        self.assertEqual(_map_spatial_precision("MEDIUM", "geocoder"), "VILLAGE")

    def test_pincode_precision(self):
        self.assertEqual(_map_spatial_precision("LOW", "pincode_directory"), "PINCODE")

    def test_unmapped_from_unknown(self):
        self.assertEqual(_map_spatial_precision("UNKNOWN", "unknown"), "UNMAPPED")

    def test_unmapped_from_empty(self):
        self.assertEqual(_map_spatial_precision("", ""), "UNMAPPED")

    def test_confidence_high_numeric(self):
        self.assertAlmostEqual(_map_spatial_confidence("HIGH"), 0.9)

    def test_confidence_unknown_numeric(self):
        self.assertAlmostEqual(_map_spatial_confidence("UNKNOWN"), 0.0)


class TestGateGSaturationSuppression(unittest.TestCase):
    """Gate G: Opportunity overlay suppressed on market saturation."""

    def test_saturation_suppression_gate_g(self):
        adapter = EcosystemGraphAdapter()
        sat_report = dict(GOLDEN_REPORT)
        sat_report["recommendation"] = "SATURATED_MARKET"
        result = adapter.build_graph_from_opportunity_report(sat_report, radius_km=10.0)
        self.assertEqual(result["layers"]["opportunities"]["status"], "UNAVAILABLE")
        self.assertIn("suppressed", result["layers"]["opportunities"]["message"].lower())

    def test_constrained_suppression_gate_g(self):
        adapter = EcosystemGraphAdapter()
        con_report = dict(GOLDEN_REPORT)
        con_report["recommendation"] = "CONSTRAINED_MARKET"
        result = adapter.build_graph_from_opportunity_report(con_report, radius_km=10.0)
        self.assertEqual(result["layers"]["opportunities"]["status"], "UNAVAILABLE")
        self.assertIn("suppressed", result["layers"]["opportunities"]["message"].lower())


class TestGeometry(unittest.TestCase):
    """Document 5, Section 24: Geometry validation."""

    def test_zero_distance(self):
        dist = haversine_distance(17.9276, 78.2344, 17.9276, 78.2344)
        self.assertAlmostEqual(dist, 0.0, places=5)

    def test_known_haversine_pair(self):
        # Mumbai to Pune: ~120 km (great-circle distance)
        dist = haversine_distance(19.0760, 72.8777, 18.5204, 73.8567)
        self.assertGreater(dist, 110)
        self.assertLess(dist, 130)

    def test_invalid_coordinates_return_none(self):
        result = calculate_distance(91.0, 0.0, 0.0, 0.0)
        self.assertIsNone(result)

    def test_missing_coordinates_return_none(self):
        result = calculate_distance(17.0, 78.0, None, None)
        self.assertIsNone(result)

    def test_exact_radius_boundary_5km(self):
        # Point approximately 5 km away
        dist = haversine_distance(17.9276, 78.2344, 17.9726, 78.2344)
        self.assertGreater(dist, 4.5)
        self.assertLess(dist, 5.5)


class TestNodeBuilding(unittest.TestCase):
    """Document 5, Section 7: Node contract and data integrity."""

    def test_mapped_node_has_spatial_precision(self):
        node, unmapped = _build_graph_node(GOLDEN_BUSINESSES[0], GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, 0)
        self.assertIsNotNone(node)
        self.assertIsNone(unmapped)
        self.assertIn(node["location"]["precision"], ["EXACT", "LOCALITY", "VILLAGE", "PINCODE"])
        self.assertNotEqual(node["location"]["precision"], "UNMAPPED")

    def test_unmapped_node_goes_to_unmapped_entities(self):
        node, unmapped = _build_graph_node(GOLDEN_BUSINESSES[4], GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, 4)
        self.assertIsNone(node)
        self.assertIsNotNone(unmapped)

    def test_no_coordinate_fabrication(self):
        """No coordinate must be fabricated for an unmapped enterprise."""
        _, unmapped = _build_graph_node(GOLDEN_BUSINESSES[4], GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, 4)
        self.assertIsNone(unmapped["location"]["latitude"])
        self.assertIsNone(unmapped["location"]["longitude"])

    def test_workforce_tier_always_unknown(self):
        """Rule 2.3: Scale tier must be UNKNOWN unless validated data exists."""
        for biz in GOLDEN_BUSINESSES:
            node, unmapped = _build_graph_node(biz, GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, 0)
            target = node if node else unmapped
            self.assertEqual(target["scaleTier"], "UNKNOWN")

    def test_pincode_node_has_warning(self):
        """Pincode-level nodes must carry spatial approximation warning."""
        node, _ = _build_graph_node(GOLDEN_BUSINESSES[1], GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, 1)
        self.assertIsNotNone(node)
        self.assertEqual(node["location"]["precision"], "PINCODE")
        warnings = node["dataQuality"]["warnings"]
        self.assertTrue(any("pincode" in w.lower() for w in warnings))

    def test_stable_node_ids(self):
        """Node IDs must be deterministic and stable across runs."""
        node1, _ = _build_graph_node(GOLDEN_BUSINESSES[0], GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, 0)
        node2, _ = _build_graph_node(GOLDEN_BUSINESSES[0], GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, 0)
        self.assertEqual(node1["id"], node2["id"])

    def test_unique_node_ids(self):
        """Different enterprises must have different node IDs."""
        nodes = []
        for i, biz in enumerate(GOLDEN_BUSINESSES):
            node, _ = _build_graph_node(biz, GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, i)
            if node:
                nodes.append(node)
        ids = [n["id"] for n in nodes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_sector_color_assigned(self):
        node, _ = _build_graph_node(GOLDEN_BUSINESSES[0], GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, 0)
        self.assertEqual(node["sectorColor"], "#10B981")  # DAIRY color


class TestEdgeBuilding(unittest.TestCase):
    """Document 5, Sections 8 & 24: Edge contract and relationship semantics."""

    def setUp(self):
        self.nodes = []
        for i, biz in enumerate(GOLDEN_BUSINESSES):
            node, _ = _build_graph_node(biz, GOLDEN_CENTER_LAT, GOLDEN_CENTER_LON, i)
            if node:
                self.nodes.append(node)

    def test_competitor_edges_are_derived(self):
        edges = _build_edges(self.nodes, "DAIRY", ["FOOD_RETAIL", "AGRICULTURE_SUPPORT"])
        comp_edges = [e for e in edges if e["relationshipType"] == "COMPETITOR"]
        for edge in comp_edges:
            self.assertEqual(edge["relationshipStatus"], "DERIVED")

    def test_supply_chain_edges_are_derived(self):
        edges = _build_edges(self.nodes, "DAIRY", ["FOOD_RETAIL", "AGRICULTURE_SUPPORT"])
        sc_edges = [e for e in edges if e["relationshipType"] == "SUPPLY_CHAIN"]
        for edge in sc_edges:
            self.assertEqual(edge["relationshipStatus"], "DERIVED")

    def test_dairy_competitor_pair_exists(self):
        """Two DAIRY nodes should produce a COMPETITOR edge."""
        edges = _build_edges(self.nodes, "DAIRY", ["FOOD_RETAIL"])
        comp_edges = [e for e in edges if e["relationshipType"] == "COMPETITOR"]
        dairy_ids = [n["id"] for n in self.nodes if n["sector"] == "DAIRY"]
        self.assertGreaterEqual(len(dairy_ids), 2)
        self.assertGreater(len(comp_edges), 0)

    def test_supply_chain_dairy_food_retail(self):
        """DAIRY ↔ FOOD_RETAIL should produce a SUPPLY_CHAIN edge."""
        edges = _build_edges(self.nodes, "DAIRY", ["FOOD_RETAIL"])
        sc_edges = [e for e in edges if e["relationshipType"] == "SUPPLY_CHAIN"]
        has_dairy_food = any(
            (e["evidence"]["sourceActivity"] in ["DAIRY", "FOOD_RETAIL"] and
             e["evidence"]["targetActivity"] in ["DAIRY", "FOOD_RETAIL"])
            for e in sc_edges
        )
        self.assertTrue(has_dairy_food, "Expected DAIRY↔FOOD_RETAIL supply-chain edge")

    def test_supply_chain_dairy_agriculture(self):
        """DAIRY ↔ AGRICULTURE_SUPPORT should produce a SUPPLY_CHAIN edge."""
        edges = _build_edges(self.nodes, "DAIRY", ["AGRICULTURE_SUPPORT"])
        sc_edges = [e for e in edges if e["relationshipType"] == "SUPPLY_CHAIN"]
        has_dairy_agri = any(
            (e["evidence"]["sourceActivity"] in ["DAIRY", "AGRICULTURE_SUPPORT"] and
             e["evidence"]["targetActivity"] in ["DAIRY", "AGRICULTURE_SUPPORT"])
            for e in sc_edges
        )
        self.assertTrue(has_dairy_agri, "Expected DAIRY↔AGRICULTURE_SUPPORT supply-chain edge")

    def test_no_edges_for_unknown_sector(self):
        """UNKNOWN sector nodes must NOT generate edges."""
        edges = _build_edges(self.nodes, "DAIRY", ["FOOD_RETAIL"])
        for edge in edges:
            self.assertNotEqual(edge["evidence"]["sourceActivity"], "UNKNOWN")
            self.assertNotEqual(edge["evidence"]["targetActivity"], "UNKNOWN")

    def test_no_duplicate_edges(self):
        edges = _build_edges(self.nodes, "DAIRY", ["FOOD_RETAIL"])
        pairs = [(e["source"], e["target"]) for e in edges]
        normalized = [tuple(sorted(p)) for p in pairs]
        self.assertEqual(len(normalized), len(set(normalized)))

    def test_edge_has_rule_id(self):
        edges = _build_edges(self.nodes, "DAIRY", ["FOOD_RETAIL"])
        for edge in edges:
            self.assertIn(edge["ruleId"], ["COMPETITOR_ACTIVITY_V1", "SUPPLY_CHAIN_ACTIVITY_MATRIX_V1"])

    def test_no_transaction_claim_in_evidence(self):
        """No edge evidence should claim confirmed transactions."""
        edges = _build_edges(self.nodes, "DAIRY", ["FOOD_RETAIL"])
        for edge in edges:
            evidence_text = str(edge["evidence"]).lower()
            self.assertNotIn("confirmed", evidence_text)
            self.assertNotIn("actual buyer", evidence_text)
            self.assertNotIn("guaranteed", evidence_text)


class TestTemporalMetadata(unittest.TestCase):
    """Document 5, Section 13 & Rule 2.5: Temporal scrubber."""

    def test_data_driven_min_max_year(self):
        nodes = [{"registrationDate": "2019-01-01"}, {"registrationDate": "2023-06-15"}]
        temporal = _build_temporal_metadata(nodes)
        self.assertEqual(temporal["minYear"], 2019)
        self.assertEqual(temporal["maxYear"], 2023)

    def test_no_hardcoded_2018(self):
        nodes = [{"registrationDate": "2015-01-01"}, {"registrationDate": "2020-06-15"}]
        temporal = _build_temporal_metadata(nodes)
        self.assertEqual(temporal["minYear"], 2015)

    def test_missing_date_tracked(self):
        nodes = [{"registrationDate": None}, {"registrationDate": "2022-01-01"}]
        temporal = _build_temporal_metadata(nodes)
        self.assertEqual(temporal["missingDates"], 1)

    def test_invalid_date_tracked(self):
        nodes = [{"registrationDate": "invalid"}, {"registrationDate": "2022-01-01"}]
        temporal = _build_temporal_metadata(nodes)
        self.assertEqual(temporal["missingDates"], 1)

    def test_empty_nodes_no_temporal(self):
        temporal = _build_temporal_metadata([])
        self.assertIsNone(temporal["minYear"])
        self.assertEqual(temporal["status"], "NO_TEMPORAL_DATA")

    def test_registration_velocity(self):
        nodes = [
            {"registrationDate": "2020-01-01"},
            {"registrationDate": "2021-06-01"},
            {"registrationDate": "2021-12-01"},
            {"registrationDate": "2022-06-01"},
        ]
        temporal = _build_temporal_metadata(nodes)
        self.assertGreater(len(temporal["registrationVelocity"]), 0)


class TestGraphAdapter(unittest.TestCase):
    """Document 5: Full adapter integration test using golden dataset."""

    def test_build_graph_from_golden_report(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT, radius_km=10.0)

        self.assertEqual(graph["schemaVersion"], SCHEMA_VERSION)
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertIn("unmappedEntities", graph)
        self.assertIn("metrics", graph)
        self.assertIn("temporal", graph)
        self.assertIn("layers", graph)
        self.assertIn("warnings", graph)

    def test_unmapped_entities_populated(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)
        self.assertGreater(len(graph["unmappedEntities"]), 0)

    def test_mapped_nodes_have_coordinates(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)
        for node in graph["nodes"]:
            self.assertIsNotNone(node["location"]["latitude"])
            self.assertIsNotNone(node["location"]["longitude"])

    def test_catchment_center(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)
        self.assertEqual(graph["catchment"]["center"]["latitude"], GOLDEN_CENTER_LAT)
        self.assertEqual(graph["catchment"]["center"]["longitude"], GOLDEN_CENTER_LON)
        self.assertEqual(graph["catchment"]["distanceMethod"], "HAVERSINE")

    def test_hhi_semantic_label(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)
        hhi = graph["metrics"].get("hhi", {})
        self.assertEqual(hhi.get("semanticDefinition"), "existing-project-sector-diversification-HHI")

    def test_density_layer_status(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)
        density = graph["layers"]["density"]
        self.assertIn(density["status"], ["AVAILABLE", "INSUFFICIENT_DATA"])

    def test_opportunity_layer_status(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)
        opp = graph["layers"]["opportunities"]
        self.assertIn(opp["status"], ["AVAILABLE", "UNAVAILABLE"])

    def test_warnings_contain_provenance(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)
        warning_codes = [w["code"] for w in graph["warnings"]]
        self.assertIn("UNMAPPED_ENTERPRISES", warning_codes)

    def test_visualization_radius_does_not_alter_scoring(self):
        """Rule 2.6: visual radius changes must not alter scoring catchment."""
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(
            GOLDEN_REPORT, radius_km=10.0, visualization_radius_km=5.0,
        )
        self.assertEqual(graph["catchment"]["scoringRadiusKm"], 10.0)
        self.assertEqual(graph["catchment"]["radiusKm"], 5.0)


class TestValidation(unittest.TestCase):
    """Document 5, Section 23: Input validation."""

    def test_valid_inputs(self):
        errors = validate_ecosystem_graph_request(17.9, 78.2, 10.0)
        self.assertEqual(len(errors), 0)

    def test_invalid_latitude(self):
        errors = validate_ecosystem_graph_request(91.0, 78.0, 10.0)
        self.assertGreater(len(errors), 0)

    def test_invalid_longitude(self):
        errors = validate_ecosystem_graph_request(17.0, 181.0, 10.0)
        self.assertGreater(len(errors), 0)

    def test_negative_radius(self):
        errors = validate_ecosystem_graph_request(17.0, 78.0, -1.0)
        self.assertGreater(len(errors), 0)

    def test_radius_too_large(self):
        errors = validate_ecosystem_graph_request(17.0, 78.0, 100.0)
        self.assertGreater(len(errors), 0)

    def test_none_coordinates_valid(self):
        errors = validate_ecosystem_graph_request(None, None, 10.0)
        self.assertEqual(len(errors), 0)


class TestPerformance(unittest.TestCase):
    """Document 5, Section 19: Performance benchmarks."""

    def test_500_node_transformation(self):
        """500+ node transformation must complete in under 2 seconds."""
        # Generate 500 synthetic businesses
        businesses = []
        for i in range(500):
            businesses.append({
                "record_fingerprint": f"fp_perf_{i:04d}",
                "enterprise_name": f"TEST Performance Enterprise {i}",
                "state": "TELANGANA",
                "district": "MEDAK",
                "pincode": f"50200{i % 10}",
                "registration_date": f"20{20 + i % 6}-{(i % 12) + 1:02d}-15",
                "communication_address": f"Location {i}, Medak",
                "latitude": 17.9276 + (i % 50) * 0.001,
                "longitude": 78.2344 + (i % 50) * 0.001,
                "coordinate_confidence": "HIGH",
                "coordinate_source": "government_census",
                "distance_km": (i % 50) * 0.2,
                "market_zone": "CORE_5KM" if i % 3 == 0 else "NEARBY_10KM",
                "primary_category": ["DAIRY", "FOOD_RETAIL", "FABRICATION", "SERVICES"][i % 4],
                "primary_category_label": "Test Category",
                "category_confidence": "HIGH",
                "activities_parsed": [{"nic_code": "1050", "activity_description": "Test", "normalized_category": ["DAIRY", "FOOD_RETAIL", "FABRICATION", "SERVICES"][i % 4]}],
                "relevance_class": "DIRECT_COMPETITOR",
                "data_sources": ["UDYAM_MSME"],
            })

        report = dict(GOLDEN_REPORT)
        report["classified_competitors"] = businesses[:50]
        report["all_nearby_businesses"] = businesses

        adapter = EcosystemGraphAdapter()
        start = time.time()
        graph = adapter.build_graph_from_opportunity_report(report, radius_km=10.0)
        elapsed = time.time() - start

        self.assertGreaterEqual(len(graph["nodes"]), 100)
        self.assertLess(elapsed, 2.0, f"500-node transform took {elapsed:.2f}s (limit: 2.0s)")
        print(f"  [PERF] 500+ node graph built in {elapsed:.3f}s ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")


class TestMetrics(unittest.TestCase):
    """Document 5, Sections 17 & 24: Metric provenance and semantics."""

    def test_metrics_have_provenance(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)
        for key, metric in graph["metrics"].items():
            if isinstance(metric, dict) and "value" in metric:
                self.assertIn("source", metric, f"Metric {key} missing source")
                has_definition = "definition" in metric or "semanticDefinition" in metric
                self.assertTrue(has_definition, f"Metric {key} missing definition or semanticDefinition")
                self.assertIn("status", metric, f"Metric {key} missing status")


class TestWarnings(unittest.TestCase):
    """Document 5, Section 18: Provenance warnings."""

    def test_warning_structure(self):
        adapter = EcosystemGraphAdapter()
        graph = adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)
        for warning in graph["warnings"]:
            self.assertIn("code", warning)
            self.assertIn("severity", warning)
            self.assertIn("message", warning)


class TestVillageDensityHeatmap(unittest.TestCase):
    """Step 1: Village-Level MSME Density Heatmap aggregation & schema tests."""

    def setUp(self):
        self.adapter = EcosystemGraphAdapter()
        self.graph = self.adapter.build_graph_from_opportunity_report(GOLDEN_REPORT)

    def test_village_density_in_response(self):
        """Graph response must contain villageDensity key with non-empty list."""
        self.assertIn("villageDensity", self.graph)
        vd = self.graph["villageDensity"]
        self.assertIsInstance(vd, list)
        self.assertGreater(len(vd), 0, "villageDensity should contain aggregated clusters")

    def test_village_density_schema_attributes(self):
        """Each village density record must provide required spatial and density fields."""
        vd = self.graph["villageDensity"]
        for record in vd:
            self.assertIn("villageName", record)
            self.assertIn("latitude", record)
            self.assertIn("longitude", record)
            self.assertIn("msmeCount", record)
            self.assertIn("mappedCount", record)
            self.assertIn("unmappedCount", record)
            self.assertIn("pincode", record)
            self.assertIn("precision", record)
            self.assertIn("sectorBreakdown", record)
            self.assertIn("intensityNormalized", record)

            self.assertIsInstance(record["latitude"], float)
            self.assertIsInstance(record["longitude"], float)
            self.assertGreaterEqual(record["msmeCount"], 1)
            self.assertGreaterEqual(record["intensityNormalized"], 0.0)
            self.assertLessEqual(record["intensityNormalized"], 1.0)

    def test_intensity_normalized_max_is_one(self):
        """The highest-density cluster must have intensityNormalized == 1.0."""
        vd = self.graph["villageDensity"]
        max_intensity = max(r["intensityNormalized"] for r in vd)
        self.assertEqual(max_intensity, 1.0)

    def test_density_sorted_descending(self):
        """Clusters must be sorted descending by msmeCount."""
        vd = self.graph["villageDensity"]
        counts = [r["msmeCount"] for r in vd]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_unmapped_entities_contribute_without_coordinate_fabrication(self):
        """Unmapped entities must be counted in density without fabricating coordinates."""
        total_density_msmes = sum(r["msmeCount"] for r in self.graph["villageDensity"])
        # Total density count should encompass mapped nodes plus any matched unmapped entities
        self.assertGreaterEqual(total_density_msmes, len(self.graph["nodes"]))


class TestAlandiLocationResolution(unittest.TestCase):
    """
    Tests verifying that entering Alandi resolves to Alandi Devachi (18.6776, 73.8987)
    and NOT the district centroid (Burkegaon 18.6131, 74.1043), ensuring zero location discrepancy.
    """

    def setUp(self):
        from app.core.udyam.geography.gazetteer import Gazetteer
        self.gazetteer = Gazetteer()
        self.adapter = EcosystemGraphAdapter()

    def test_alandi_gazetteer_resolution(self):
        """'Alandi' in Pune must resolve to Alandi Devachi coordinates (18.6776, 73.8987)."""
        coords = self.gazetteer.resolve_locality_coords("Alandi", "Pune", "Maharashtra")
        self.assertIsNotNone(coords)
        lat, lon = coords
        self.assertAlmostEqual(lat, 18.6776, places=3)
        self.assertAlmostEqual(lon, 73.8987, places=3)
        # Must NOT be Burkegaon centroid (18.6131, 74.1043)
        self.assertNotAlmostEqual(lat, 18.6131, places=2)
        self.assertNotAlmostEqual(lon, 74.1043, places=2)

    def test_alandi_devachi_gazetteer_resolution(self):
        """'Alandi Devachi' in Pune must resolve to (18.6776, 73.8987)."""
        coords = self.gazetteer.resolve_locality_coords("Alandi Devachi", "Pune", "Maharashtra")
        self.assertIsNotNone(coords)
        lat, lon = coords
        self.assertAlmostEqual(lat, 18.6776, places=3)
        self.assertAlmostEqual(lon, 73.8987, places=3)

    def test_build_graph_alandi_resolves_catchment_origin(self):
        """build_graph with village='Alandi' without coords must anchor catchment at Alandi Devachi."""
        graph = self.adapter.build_graph(
            state="Maharashtra",
            district="Pune",
            village="Alandi",
            target_lat=None,
            target_lon=None,
            business_intent="dairy",
            radius_km=10.0,
        )
        center = graph["catchment"]["center"]
        self.assertAlmostEqual(center["latitude"], 18.6776, places=3)
        self.assertAlmostEqual(center["longitude"], 73.8987, places=3)

    def test_build_graph_explicit_gps_coords_take_absolute_precedence(self):
        """When user auto-detects or supplies GPS coords, they must be preserved exactly."""
        gps_lat = 18.6780
        gps_lon = 73.8990
        graph = self.adapter.build_graph(
            state="Maharashtra",
            district="Pune",
            village="Alandi",
            target_lat=gps_lat,
            target_lon=gps_lon,
            business_intent="dairy",
            radius_km=10.0,
        )
        center = graph["catchment"]["center"]
        self.assertEqual(center["latitude"], gps_lat)
        self.assertEqual(center["longitude"], gps_lon)


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("=" * 80)
    print("DOCUMENT 5 — ECOSYSTEM GRAPH ADAPTER TEST SUITE")
    print("TEST FIXTURE — NOT REAL BUSINESS DATA")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestSpatialPrecision,
        TestGeometry,
        TestNodeBuilding,
        TestEdgeBuilding,
        TestTemporalMetadata,
        TestGraphAdapter,
        TestValidation,
        TestPerformance,
        TestMetrics,
        TestWarnings,
        TestVillageDensityHeatmap,
        TestAlandiLocationResolution,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n{'=' * 80}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures:  {len(result.failures)}")
    print(f"Errors:    {len(result.errors)}")
    print(f"{'=' * 80}")

    sys.exit(0 if result.wasSuccessful() else 1)
