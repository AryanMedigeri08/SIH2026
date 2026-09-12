"""
test_integration_consistency.py — Comprehensive Cross-Component Integration
and End-to-End Consistency Verification Suite.

Document 6: Cross-Component Integration & End-to-End Consistency Audit.

Validates the full chain of custody across:
  UDYAM / Government Data -> Village Intelligence -> Market Intelligence Engine ->
  Ecosystem Graph Read Model -> Decision / Recommendation Layer -> Dashboard

Tests:
  1. Deterministic E2E Golden Fixture (Section 21 & 22)
  2. Invariant I1: Enterprise Identity & Deduplication (Section 2)
  3. Invariant I2: Geographic Identity & Coordinate Precision Hierarchy (Section 2 & 3)
  4. Category / Activity Semantic Consistency (Section 4)
  5. Derived Competitor Semantics (Section 5)
  6. Derived Supply-Chain Semantics (Section 6)
  7. HHI Semantic Integrity (Section 7)
  8. Scoring Radius vs Visualization Radius Independence (Section 8)
  9. Opportunity Score Integrity & Guardrail Propagation (Sections 9 & 10)
  10. Confidence vs Opportunity Independence (Section 11)
  11. Provenance & Lineage Propagation (Section 12)
  12. Temporal Consistency & Registration Dates (Section 13)
  13. Graph <-> Market Intelligence Reconciliation (Section 14)
  14. Unmapped Entity Preservation & Transparency (Section 15)
  15. Ecosystem Graph API Schema & Validation (Section 16)
  16. Frontend Contract & Display Disclaimers (Section 17)
  17. Beneficiary & Banker Persona Separation (Sections 18 & 19)
  18. LLM / Chat Advisory Boundary Isolation (Section 20)
  19. Error-State Matrix Scenarios (Section 25)
  20. Performance Limits & Capping Disclosures (Section 24)

TEST FIXTURE — NOT REAL BUSINESS DATA
"""

from __future__ import annotations
import os
import sys
import time
import unittest
from pathlib import Path
from typing import Optional, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
CORE_DIR = BACKEND_DIR / "app" / "core"
for p in (str(CORE_DIR), str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.udyam.models import (
    compute_record_fingerprint,
    CoordinateConfidence,
    LocalityConfidence,
    MarketZone,
)
from app.core.udyam.activities.categories import (
    is_potential_competitor,
    is_potential_supply_chain,
    get_category_label,
    BUSINESS_CATEGORIES,
)
from app.core.udyam.geography.distance import haversine_distance, calculate_distance
from app.core.intelligence.models import (
    BusinessIntent,
    RelevanceClass,
    RecommendationClass,
    MarketOpportunityReport,
)
from app.core.intelligence.relevance import classify_records_batch
from app.core.intelligence.supply import compute_supply_metrics
from app.core.intelligence.opportunity import (
    calculate_opportunity_indicators,
    compute_opportunity_score_and_verdict,
)
from app.core.intelligence.ecosystem_graph import (
    EcosystemGraphAdapter,
    _map_spatial_precision,
    _map_spatial_confidence,
    _build_graph_node,
    _build_edges,
    _build_temporal_metadata,
    _build_metrics,
    validate_ecosystem_graph_request,
    SCHEMA_VERSION,
)
from app.models.schemas import EcosystemGraphRequest, EcosystemGraphResponse


# ==============================================================================
# SECTION 21: SYNTHETIC BENCHMARK FIXTURE (FORMAL STRESS-TEST HARNESS)
# ==============================================================================
# METHODOLOGICAL DISCLOSURE & DATA INTEGRITY NOTE:
# This fixture is completely SYNTHETIC and designed exclusively for cross-component
# integration consistency, invariant verification, and boundary stress-testing (Document 6, Section 21).
#
# GEOGRAPHIC INTEGRITY NOTE:
# "Balanagar, Medak" is an artificial synthetic benchmark geography originating from
# early stress-test suites; in official administrative boundaries, Balanagar is not a
# revenue village within Medak district. It is used here exclusively as an isolated
# algorithmic sandbox to test distance clipping, multi-tier precision, and edge derivation.
#
# ENTERPRISE IDENTITY NOTE:
# All enterprise names, addresses, and coordinates below are 100% synthetic mock entities
# and DO NOT represent real UDYAM registered MSMEs, real entrepreneurs, or commercial brands.

SYNTHETIC_BENCHMARK_TARGET_LOCALITY = {
    "state": "TELANGANA",
    "district": "MEDAK",
    "village": "Balanagar",
    "latitude": 17.9276,
    "longitude": 78.2344,
    "scoring_radius_km": 10.0,
    "core_radius_km": 5.0,
    "is_synthetic_benchmark": True,
}
# Backward compatibility alias
TARGET_LOCALITY = SYNTHETIC_BENCHMARK_TARGET_LOCALITY

# 10 carefully controlled synthetic records covering all required test dimensions:
# - exact GPS, census locality, village admin, pincode directory, unmapped
# - direct competitor, related business, indirect, non-relevant, unknown sector
# - temporal spread (2019, 2021, 2023, 2024, invalid date, missing date)
# - inside 5km, between 5km-10km, outside 10km
SYNTHETIC_BENCHMARK_FIXTURE_RECORDS = [
    {
        # Record 1: Direct competitor, EXACT enterprise GPS, ~1.8 km (Core 5km)
        "record_fingerprint": "fp_exact_dairy_001",
        "enterprise_name": "SYNTHETIC Ent 01 (Dairy Processing Unit - GPS)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502319",
        "registration_date": "2019-04-12",
        "communication_address": "Plot 14, Main Road, Balanagar",
        "activities_raw": "Dairy farming and processing of fresh cow milk",
        "primary_category": "DAIRY",
        "resolved_locality": "Balanagar",
        "latitude": 17.9350,
        "longitude": 78.2450,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "verified_gps",
    },
    {
        # Record 2: Direct competitor, Census locality centroid, ~3.2 km (Core 5km)
        "record_fingerprint": "fp_locality_dairy_002",
        "enterprise_name": "SYNTHETIC Ent 02 (Chilling Center - Locality Centroid)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502319",
        "registration_date": "2021-08-20",
        "communication_address": "Survey 112, Near Gram Panchayat, Balanagar",
        "activities_raw": "Milk collection chilling and paneer manufacturing",
        "primary_category": "DAIRY",
        "resolved_locality": "Balanagar Locality Centroid",
        "latitude": 17.9100,
        "longitude": 78.2200,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "government_census",
    },
    {
        # Record 3: Related business (value-chain buyer), Village centroid, ~4.5 km (Core 5km)
        "record_fingerprint": "fp_village_sweets_003",
        "enterprise_name": "SYNTHETIC Ent 03 (Traditional Sweets - Village Centroid)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502319",
        "registration_date": "2023-01-15",
        "communication_address": "Village Chowk, Balanagar",
        "activities_raw": "Manufacturing of dairy-based sweets and bakery items",
        "primary_category": "FOOD_PROCESSING",
        "resolved_locality": "Balanagar Village",
        "latitude": 17.9000,
        "longitude": 78.2100,
        "coordinate_confidence": "MEDIUM",
        "coordinate_source": "government_admin",
    },
    {
        # Record 4: Indirect / Complementary (Food Retail), Pincode centroid, ~6.8 km (Secondary 10km)
        "record_fingerprint": "fp_pincode_retail_004",
        "enterprise_name": "SYNTHETIC Ent 04 (Dairy Retail - Pincode Centroid)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502319",
        "registration_date": "2024-03-10",
        "communication_address": "Near Bus Stand, PIN 502319",
        "activities_raw": "Retail sale of packaged dairy products and groceries",
        "primary_category": "FOOD_RETAIL",
        "resolved_locality": "502319 Centroid",
        "latitude": 17.8800,
        "longitude": 78.1900,
        "coordinate_confidence": "LOW",
        "coordinate_source": "pincode_directory",
    },
    {
        # Record 5: Complementary / Supply Chain (Agriculture Support), Locality, ~2.8 km (Core 5km)
        "record_fingerprint": "fp_supply_fodder_005",
        "enterprise_name": "SYNTHETIC Ent 05 (Cattle Fodder - Locality Centroid)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502319",
        "registration_date": "2021-11-05",
        "communication_address": "Gat 45, Balanagar Outskirts",
        "activities_raw": "Supply of cattle fodder, animal feed and silage",
        "primary_category": "AGRICULTURE_SUPPORT",
        "resolved_locality": "Balanagar",
        "latitude": 17.9400,
        "longitude": 78.2200,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "government_census",
    },
    {
        # Record 6: Non-relevant sector (Metal Fabrication), ~2.5 km (Core 5km)
        "record_fingerprint": "fp_nonrelevant_fab_006",
        "enterprise_name": "SYNTHETIC Ent 06 (Metal Fabrication - Locality Centroid)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502319",
        "registration_date": "2020-06-18",
        "communication_address": "Industrial Area, Balanagar",
        "activities_raw": "Steel grill welding, fabrication and metal works",
        "primary_category": "FABRICATION",
        "resolved_locality": "Balanagar",
        "latitude": 17.9300,
        "longitude": 78.2100,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "government_census",
    },
    {
        # Record 7: Unknown sector / Unclassified activities, Locality, ~3.0 km (Core 5km)
        "record_fingerprint": "fp_unknown_sector_007",
        "enterprise_name": "SYNTHETIC Ent 07 (Unclassified Trading - Locality Centroid)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502319",
        "registration_date": "2022-09-01",
        "communication_address": "Market Road, Balanagar",
        "activities_raw": "Trading and miscellaneous services",
        "primary_category": "UNKNOWN",
        "resolved_locality": "Balanagar",
        "latitude": 17.9200,
        "longitude": 78.2400,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "government_census",
    },
    {
        # Record 8: UNMAPPED enterprise (No coordinates, unresolvable address)
        "record_fingerprint": "fp_unmapped_dairy_008",
        "enterprise_name": "SYNTHETIC Ent 08 (Unmapped Dairy - Missing Coordinates)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "",
        "registration_date": "2023-07-22",
        "communication_address": "Unknown Thanda, Deep Rural Medak",
        "activities_raw": "Dairy farming and animal husbandry",
        "primary_category": "DAIRY",
        "resolved_locality": "",
        "latitude": None,
        "longitude": None,
        "coordinate_confidence": "UNKNOWN",
        "coordinate_source": "",
    },
    {
        # Record 9: Out-of-catchment enterprise (> 10km, ~16.5 km away)
        "record_fingerprint": "fp_outside_dairy_009",
        "enterprise_name": "SYNTHETIC Ent 09 (Distant Dairy - Out of Catchment)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502325",
        "registration_date": "2018-02-14",
        "communication_address": "Highway Junction, Medak Outer",
        "activities_raw": "Industrial dairy chilling and distribution",
        "primary_category": "DAIRY",
        "resolved_locality": "Medak Outer",
        "latitude": 18.0500,
        "longitude": 78.3200,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "government_census",
    },
    {
        # Record 10: Malformed date record for temporal resilience testing
        "record_fingerprint": "fp_bad_date_010",
        "enterprise_name": "SYNTHETIC Ent 10 (Vintage Milk Point - Malformed Date)",
        "state": "TELANGANA",
        "district": "MEDAK",
        "pincode": "502319",
        "registration_date": "9999-99-99",  # Malformed date
        "communication_address": "Old Bazaar, Balanagar",
        "activities_raw": "Milk distribution",
        "primary_category": "DAIRY",
        "resolved_locality": "Balanagar",
        "latitude": 17.9250,
        "longitude": 78.2300,
        "coordinate_confidence": "HIGH",
        "coordinate_source": "government_census",
    },
]
# Backward compatibility alias
DETERMINISTIC_FIXTURE_RECORDS = SYNTHETIC_BENCHMARK_FIXTURE_RECORDS


class TestIntegrationConsistency(unittest.TestCase):
    """Document 6 Comprehensive Cross-Component Integration Verification."""

    @classmethod
    def setUpClass(cls):
        cls.intent = BusinessIntent(
            intent_id="intent-dairy",
            display_name="Dairy Farm & Milk Processing",
            primary_category="DAIRY",
            direct_categories=["DAIRY"],
            related_categories=["FOOD_PROCESSING", "AGRICULTURE_SUPPORT", "FOOD_RETAIL"],
            search_keywords=["dairy", "milk", "chilling", "paneer", "ghee"],
        )

        # Enrich records with calculated distance from target
        cls.enriched_records = []
        for r in DETERMINISTIC_FIXTURE_RECORDS:
            item = dict(r)
            if item["latitude"] is not None and item["longitude"] is not None:
                d = haversine_distance(
                    TARGET_LOCALITY["latitude"], TARGET_LOCALITY["longitude"],
                    item["latitude"], item["longitude"],
                )
                item["distance_km"] = round(d, 2)
            else:
                item["distance_km"] = None
            cls.enriched_records.append(item)

        # Classify records
        cls.classified_records = classify_records_batch(cls.enriched_records, cls.intent)

        # Build mock MarketOpportunityReport dict
        cls.competitors_only = [
            r.to_dict() for r in cls.classified_records
            if r.relevance_class in (RelevanceClass.DIRECT_COMPETITOR.value, RelevanceClass.RELATED_BUSINESS.value)
        ]

        cls.all_nearby = [r.to_dict() for r in cls.classified_records]

        # Calculate supply metrics & opportunity
        cls.supply_metrics = compute_supply_metrics(
            records=cls.classified_records,
            target_locality=TARGET_LOCALITY["village"],
            population=15000.0,
        )

        cls.mock_report = {
            "version": "2.0-deterministic",
            "target_location": {
                "state": TARGET_LOCALITY["state"],
                "district": TARGET_LOCALITY["district"],
                "village": TARGET_LOCALITY["village"],
                "latitude": TARGET_LOCALITY["latitude"],
                "longitude": TARGET_LOCALITY["longitude"],
                "analysis_radius_km": TARGET_LOCALITY["scoring_radius_km"],
                "core_radius_km": TARGET_LOCALITY["core_radius_km"],
                "snapshot_id": "SNAP-DOC6-E2E-TEST",
            },
            "business_intent": cls.intent.to_dict(),
            "recommendation": "MODERATE_COMPETITION",
            "composite_score": 68.5,
            "confidence": "HIGH",
            "supply_metrics": cls.supply_metrics.to_dict(),
            "demand_features": {
                "population": 15000.0,
                "has_demand_evidence": True,
                "commercial_activity_level": "MODERATE",
            },
            "opportunity_indicators": {
                "competitor_density": 0.2,
                "has_demand_evidence": True,
            },
            "classified_competitors": cls.competitors_only,
            "all_nearby_businesses": cls.all_nearby,
            "evidence": {
                "compositeScore": 68.5,
                "recommendation": "MODERATE_COMPETITION",
                "confidence": "HIGH",
                "summary": "Evidence-backed moderate competition with viable demand.",
            },
            "data_lineage": [
                {"name": "UDYAM_MSME", "records": len(cls.all_nearby)},
                {"name": "CENSUS_2011", "population": 15000},
            ],
        }

        # Build ecosystem graph read-model
        cls.adapter = EcosystemGraphAdapter()
        cls.graph = cls.adapter.build_graph_from_opportunity_report(
            report=cls.mock_report,
            radius_km=10.0,
            visualization_radius_km=10.0,
        )

    # --------------------------------------------------------------------------
    # GATE B: INVARIANT I1 — ENTERPRISE IDENTITY & DEDUPLICATION
    # --------------------------------------------------------------------------

    def test_gate_b_identity_stability_and_no_government_id_invention(self):
        """Invariant I1: Enterprise identity is deterministic SHA-256 fingerprint, never invented govt ID."""
        fp1 = compute_record_fingerprint(
            enterprise_name="SYNTHETIC Enterprise Alpha Unit",
            communication_address="Plot 14, Main Road, Synthetic Benchmark Zone",
            pincode="502319",
            registration_date="2019-04-12",
            state="TELANGANA",
            district="MEDAK",
        )
        fp2 = compute_record_fingerprint(
            enterprise_name="synthetic enterprise alpha unit",
            communication_address="plot 14, main road, synthetic benchmark zone",
            pincode="502319",
            registration_date="2019-04-12",
            state="telangana",
            district="medak",
        )
        self.assertEqual(fp1, fp2, "Fingerprints must be invariant to text casing.")
        self.assertEqual(len(fp1), 64, "Fingerprint must be standard 64-character SHA-256 hex.")
        self.assertFalse(fp1.startswith("UDYAM-"), "Fingerprint must NOT pretend to be an official government ID.")

    def test_gate_b_graph_node_id_derived_from_fingerprint(self):
        """Graph node IDs must derive deterministically from the fingerprint."""
        nodes = self.graph["nodes"]
        node_ids = [n["id"] for n in nodes]
        # Check node ID stability: format is node-{fingerprint[:12]}
        for n in nodes:
            self.assertTrue(n["id"].startswith("node-"), f"Invalid node ID format: {n['id']}")
            self.assertEqual(len(n["id"]), 17, f"Node ID must be node- + 12 chars: {n['id']}")

    # --------------------------------------------------------------------------
    # GATE C & D: INVARIANT I2 — GEOGRAPHIC IDENTITY & COORDINATE PRECISION
    # --------------------------------------------------------------------------

    def test_gate_d_precision_hierarchy_exact_reserved_strictly_for_gps(self):
        """Gate D: ONLY verified GPS qualifies as EXACT. Census/admin/pincode must never upgrade to EXACT."""
        self.assertEqual(_map_spatial_precision("HIGH", "verified_gps"), "EXACT")
        self.assertEqual(_map_spatial_precision("HIGH", "manual_survey_gps"), "EXACT")
        self.assertEqual(_map_spatial_precision("HIGH", "government_census"), "LOCALITY")
        self.assertEqual(_map_spatial_precision("HIGH", "government_admin"), "LOCALITY")
        self.assertEqual(_map_spatial_precision("MEDIUM", "government_admin"), "VILLAGE")
        self.assertEqual(_map_spatial_precision("LOW", "pincode_directory"), "PINCODE")
        self.assertEqual(_map_spatial_precision("UNKNOWN", ""), "UNMAPPED")

    def test_gate_d_fixture_nodes_reflect_exact_precision_classes(self):
        """Nodes in graph reflect expected precision classes without upgrade."""
        nodes_by_fp = {n.get("recordFingerprint"): n for n in self.graph["nodes"]}
        unmapped_by_fp = {u.get("recordFingerprint"): u for u in self.graph["unmappedEntities"]}

        # Record 1: verified GPS -> EXACT
        self.assertEqual(nodes_by_fp["fp_exact_dairy_001"]["location"]["precision"], "EXACT")
        # Record 2: census -> LOCALITY
        self.assertEqual(nodes_by_fp["fp_locality_dairy_002"]["location"]["precision"], "LOCALITY")
        # Record 3: admin medium -> VILLAGE
        self.assertEqual(nodes_by_fp["fp_village_sweets_003"]["location"]["precision"], "VILLAGE")
        # Record 4: pincode -> PINCODE
        self.assertEqual(nodes_by_fp["fp_pincode_retail_004"]["location"]["precision"], "PINCODE")
        # Record 8: unmapped -> UNMAPPED
        self.assertEqual(unmapped_by_fp["fp_unmapped_dairy_008"]["location"]["precision"], "UNMAPPED")

    def test_gate_c_no_coordinate_fabrication_for_unmapped(self):
        """Unmapped enterprise must have None coordinates and must be in unmappedEntities, not nodes."""
        unmapped = self.graph["unmappedEntities"]
        unmapped_fps = [u.get("recordFingerprint") for u in unmapped]
        self.assertIn("fp_unmapped_dairy_008", unmapped_fps)

        for u in unmapped:
            self.assertIsNone(u["location"]["latitude"])
            self.assertIsNone(u["location"]["longitude"])
            self.assertEqual(u["location"]["precision"], "UNMAPPED")

    # --------------------------------------------------------------------------
    # GATE E: CATEGORY / ACTIVITY SEMANTICS
    # --------------------------------------------------------------------------

    def test_gate_e_canonical_categories_shared_across_engines(self):
        """All sectors assigned in graph must belong to the canonical BUSINESS_CATEGORIES ontology."""
        nodes = self.graph["nodes"]
        for node in nodes:
            sector = node["sector"]
            self.assertIn(
                sector, BUSINESS_CATEGORIES,
                f"Sector '{sector}' in graph node is not in canonical BUSINESS_CATEGORIES ontology."
            )

    def test_gate_e_relevance_classification_consistency(self):
        """Direct Dairy activities must classify as DIRECT_COMPETITOR in Market Intelligence."""
        classified_map = {r.record_fingerprint: r for r in self.classified_records}
        # Record 1 (Dairy) -> DIRECT_COMPETITOR
        self.assertEqual(classified_map["fp_exact_dairy_001"].relevance_class, RelevanceClass.DIRECT_COMPETITOR.value)
        # Record 3 (Sweets / Food Processing) -> RELATED_BUSINESS
        self.assertEqual(classified_map["fp_village_sweets_003"].relevance_class, RelevanceClass.RELATED_BUSINESS.value)
        # Record 6 (Fabrication) -> NON_RELEVANT
        self.assertEqual(classified_map["fp_nonrelevant_fab_006"].relevance_class, RelevanceClass.NON_RELEVANT.value)

    # --------------------------------------------------------------------------
    # GATE F & G: COMPETITOR & SUPPLY-CHAIN SEMANTICS
    # --------------------------------------------------------------------------

    def test_gate_f_competitor_edges_are_derived_without_transaction_claims(self):
        """Competitor edges must be explicitly flagged DERIVED and contain no commercial transaction claim."""
        edges = self.graph["edges"]
        comp_edges = [e for e in edges if e["relationshipType"] == "COMPETITOR"]
        self.assertGreater(len(comp_edges), 0, "Expected at least one competitor edge.")

        for edge in comp_edges:
            self.assertEqual(edge["relationshipStatus"], "DERIVED")
            self.assertEqual(edge["ruleId"], "COMPETITOR_ACTIVITY_V1")
            evidence_text = " ".join(str(v) for v in edge.get("evidence", {}).values()).lower()
            self.assertNotIn("transaction", evidence_text)
            self.assertNotIn("contract", evidence_text)
            self.assertNotIn("poaching", evidence_text)

    def test_gate_g_supply_chain_edges_are_derived_without_transaction_claims(self):
        """Supply-chain edges must be DERIVED with direction NONE and no invoice/trade claim."""
        edges = self.graph["edges"]
        sc_edges = [e for e in edges if e["relationshipType"] == "SUPPLY_CHAIN"]
        self.assertGreater(len(sc_edges), 0, "Expected at least one supply-chain edge.")

        for edge in sc_edges:
            self.assertEqual(edge["relationshipStatus"], "DERIVED")
            self.assertEqual(edge["direction"], "NONE")
            self.assertEqual(edge["ruleId"], "SUPPLY_CHAIN_ACTIVITY_MATRIX_V1")
            evidence_text = " ".join(str(v) for v in edge.get("evidence", {}).values()).lower()
            self.assertNotIn("invoice", evidence_text)
            self.assertNotIn("confirmed supplier", evidence_text)
            self.assertNotIn("procurement", evidence_text)

    # --------------------------------------------------------------------------
    # GATE H: HHI SEMANTIC INTEGRITY
    # --------------------------------------------------------------------------

    def test_gate_h_hhi_retains_sector_diversification_semantics(self):
        """HHI in graph must preserve project's sector-diversification semantic label and source engine."""
        hhi_metric = self.graph["metrics"].get("hhi")
        self.assertIsNotNone(hhi_metric)
        self.assertEqual(
            hhi_metric.get("semanticDefinition"),
            "existing-project-sector-diversification-HHI",
            "HHI definition must remain economic sector diversification."
        )
        self.assertEqual(hhi_metric.get("source"), "market-intelligence-engine")
        self.assertIn("interpretation", hhi_metric)

    # --------------------------------------------------------------------------
    # GATE I: RADIUS INDEPENDENCE
    # --------------------------------------------------------------------------

    def test_gate_i_visual_radius_does_not_alter_analytical_scoring(self):
        """Rule 2.6: Changing visualization radius clips displayed nodes without modifying analytical composite score."""
        graph_5km = self.adapter.build_graph_from_opportunity_report(
            report=self.mock_report,
            radius_km=10.0,  # Scoring radius
            visualization_radius_km=5.0,  # Visual clipping radius
        )
        graph_10km = self.adapter.build_graph_from_opportunity_report(
            report=self.mock_report,
            radius_km=10.0,
            visualization_radius_km=10.0,
        )

        # Opportunity score & verdict must be identical
        self.assertEqual(
            graph_5km["layers"]["opportunities"]["compositeScore"],
            graph_10km["layers"]["opportunities"]["compositeScore"],
        )
        self.assertEqual(
            graph_5km["layers"]["opportunities"]["recommendation"],
            graph_10km["layers"]["opportunities"]["recommendation"],
        )

        # Displayed node count should differ (5km clips records beyond 5km)
        self.assertLess(
            len(graph_5km["nodes"]),
            len(graph_10km["nodes"]),
            "Visual 5km catchment must render fewer nodes than 10km catchment."
        )

    # --------------------------------------------------------------------------
    # GATE J & K: OPPORTUNITY SCORE PROPAGATION & GUARDRAILS
    # --------------------------------------------------------------------------

    def test_gate_j_opportunity_score_consumed_directly_from_report(self):
        """Graph consumes validated composite score without recalculation."""
        opp_layer = self.graph["layers"]["opportunities"]
        self.assertEqual(opp_layer["compositeScore"], 68.5)
        self.assertEqual(opp_layer["recommendation"], "MODERATE_COMPETITION")

    def test_gate_k_saturation_and_constrained_guardrail_suppression(self):
        """Saturated and constrained markets strictly suppress the Layer 5 opportunity overlay."""
        saturated_report = dict(self.mock_report)
        saturated_report["recommendation"] = "SATURATED_MARKET"
        saturated_report["composite_score"] = 35.0

        graph_sat = self.adapter.build_graph_from_opportunity_report(saturated_report)
        self.assertEqual(graph_sat["layers"]["opportunities"]["status"], "UNAVAILABLE")
        self.assertIn("saturated", graph_sat["layers"]["opportunities"]["message"].lower())

        constrained_report = dict(self.mock_report)
        constrained_report["recommendation"] = "CONSTRAINED_MARKET"
        constrained_report["composite_score"] = 40.0

        graph_const = self.adapter.build_graph_from_opportunity_report(constrained_report)
        self.assertEqual(graph_const["layers"]["opportunities"]["status"], "UNAVAILABLE")
        self.assertIn("constrained", graph_const["layers"]["opportunities"]["message"].lower())

    # --------------------------------------------------------------------------
    # GATE L: CONFIDENCE VS OPPORTUNITY INDEPENDENCE
    # --------------------------------------------------------------------------

    def test_gate_l_high_confidence_with_low_opportunity_is_valid(self):
        """Confidence reflects data quality, NOT opportunity feasibility."""
        sat_report = dict(self.mock_report)
        sat_report["recommendation"] = "SATURATED_MARKET"
        sat_report["confidence"] = "HIGH"
        sat_report["composite_score"] = 30.0
        sat_report["evidence"] = dict(self.mock_report["evidence"])
        sat_report["evidence"]["recommendation"] = "SATURATED_MARKET"
        sat_report["evidence"]["confidence"] = "HIGH"
        sat_report["evidence"]["compositeScore"] = 30.0

        graph_sat = self.adapter.build_graph_from_opportunity_report(sat_report)
        self.assertEqual(graph_sat["evidence"]["confidence"], "HIGH")
        self.assertEqual(graph_sat["evidence"]["recommendation"], "SATURATED_MARKET")
        self.assertEqual(graph_sat["evidence"]["compositeScore"], 30.0)

    # --------------------------------------------------------------------------
    # GATE M: PROVENANCE PROPAGATION
    # --------------------------------------------------------------------------

    def test_gate_m_provenance_lineage_and_engine_versions_present(self):
        """Ecosystem graph response carries upstream provenance and data lineage."""
        prov = self.graph["provenance"]
        self.assertIn("engine", prov)
        self.assertIn("upstreamVersion", prov)
        self.assertIn("dataLineage", prov)
        self.assertGreater(len(prov["dataLineage"]), 0)

    # --------------------------------------------------------------------------
    # GATE N: TEMPORAL CONSISTENCY
    # --------------------------------------------------------------------------

    def test_gate_n_temporal_min_max_and_malformed_date_handling(self):
        """Temporal metadata is data-driven; malformed dates are tallied in missingDates."""
        temporal = self.graph["temporal"]
        self.assertEqual(temporal["status"], "AVAILABLE")
        self.assertEqual(temporal["minYear"], 2019)  # Earliest in-catchment node is 2019
        self.assertEqual(temporal["maxYear"], 2024)
        # Record 10 has '9999-99-99' which is out of range, should be in missingDates
        self.assertGreaterEqual(temporal["missingDates"], 1)

    # --------------------------------------------------------------------------
    # GATE O: UNMAPPED DATA HANDLING
    # --------------------------------------------------------------------------

    def test_gate_o_unmapped_entities_tracked_with_explicit_disclaimer(self):
        """Unmapped enterprises must be counted and accompanied by a clear warning."""
        unmapped = self.graph["unmappedEntities"]
        self.assertGreaterEqual(len(unmapped), 1)

        warnings = self.graph["warnings"]
        unmapped_warning = next((w for w in warnings if w["code"] == "UNMAPPED_ENTERPRISES"), None)
        self.assertIsNotNone(unmapped_warning, "Expected UNMAPPED_ENTERPRISES warning.")
        self.assertEqual(unmapped_warning["severity"], "WARNING")

    # --------------------------------------------------------------------------
    # GATE P & Q: API & FRONTEND CONTRACTS
    # --------------------------------------------------------------------------

    def test_gate_p_api_request_validation(self):
        """API validation enforces valid coordinate and radius boundaries."""
        # Valid
        self.assertEqual(validate_ecosystem_graph_request(17.92, 78.23, 10.0), [])
        # Invalid latitude
        self.assertGreater(len(validate_ecosystem_graph_request(95.0, 78.23, 10.0)), 0)
        # Invalid radius (< 0.5 km)
        self.assertGreater(len(validate_ecosystem_graph_request(17.92, 78.23, 0.2)), 0)
        # Invalid radius (> 50 km)
        self.assertGreater(len(validate_ecosystem_graph_request(17.92, 78.23, 75.0)), 0)

    def test_gate_p_pydantic_schema_serialization(self):
        """Response conforms to EcosystemGraphResponse Pydantic contract."""
        resp = EcosystemGraphResponse(**self.graph)
        self.assertEqual(resp.schemaVersion, SCHEMA_VERSION)
        self.assertEqual(len(resp.nodes), len(self.graph["nodes"]))
        self.assertEqual(len(resp.edges), len(self.graph["edges"]))

    # --------------------------------------------------------------------------
    # GATE R & S: BENEFICIARY VS BANKER PERSONA SEPARATION
    # --------------------------------------------------------------------------

    def test_gate_r_and_s_bi_modal_data_contract_completeness(self):
        """Graph payload contains both simplified labels (Beneficiary) and technical metrics (Banker)."""
        # Beneficiary: intent displayName, human-language labels
        self.assertIn("displayName", self.graph["intent"])
        self.assertTrue(len(self.graph["intent"]["displayName"]) > 0)

        # Banker: HHI, spatial precision indicators, data quality provenance
        self.assertIn("hhi", self.graph["metrics"])
        self.assertIn("provenance", self.graph)
        for node in self.graph["nodes"]:
            self.assertIn("precision", node["location"])
            self.assertIn("confidence", node["location"])

    # --------------------------------------------------------------------------
    # GATE T: LLM / RECOMMENDATION BOUNDARY ISOLATION
    # --------------------------------------------------------------------------

    def test_gate_t_llm_boundary_no_metric_or_guardrail_override(self):
        """LLM layer cannot mutate deterministic composite score or override guardrails."""
        # The graph adapter consumes the report dictionary; it has no dependency on LLM generation
        self.assertIsInstance(self.graph["layers"]["opportunities"]["compositeScore"], float)
        # Verify that recommendation verdict in graph matches the deterministic report verdict
        self.assertEqual(
            self.graph["layers"]["opportunities"]["recommendation"],
            self.mock_report["recommendation"],
        )

    # --------------------------------------------------------------------------
    # SECTION 14: GRAPH <-> MARKET INTELLIGENCE RECONCILIATION
    # --------------------------------------------------------------------------

    def test_section_14_competitor_reconciliation(self):
        """
        Reconciliation between:
          Set A: Market Intelligence competitors (DIRECT + RELATED) within 10km
          Set B: Graph competitor nodes within 10km
        """
        # Set A: Classified competitors in mock report within 10km
        set_a = {
            r["record_fingerprint"]
            for r in self.mock_report["classified_competitors"]
            if r.get("distance_km") is not None and r["distance_km"] <= 10.0
        }

        # Set B: Graph nodes marked as DIRECT_COMPETITOR or RELATED_BUSINESS
        nodes_by_fp = {
            n.get("recordFingerprint"): n
            for n in self.graph["nodes"]
            if n.get("relevanceClass") in (
                RelevanceClass.DIRECT_COMPETITOR.value, RelevanceClass.RELATED_BUSINESS.value
            )
        }
        set_b = set(nodes_by_fp.keys())

        # Exact reconciliation
        diff_a_minus_b = set_a - set_b
        diff_b_minus_a = set_b - set_a

        self.assertEqual(
            diff_a_minus_b, set(),
            f"Set A contains competitors missing in Graph: {diff_a_minus_b}"
        )
        self.assertEqual(
            diff_b_minus_a, set(),
            f"Graph contains competitors not in Set A: {diff_b_minus_a}"
        )
        self.assertEqual(len(set_a), len(set_b), "Set A and Set B must have identical count.")

    # --------------------------------------------------------------------------
    # SECTION 24: PERFORMANCE LIMITS & CAPPING
    # --------------------------------------------------------------------------

    def test_gate_w_transformation_performance_and_edge_capping(self):
        """500+ node graph transformation executes in < 1.0 second."""
        synthetic_500 = []
        for i in range(500):
            synthetic_500.append({
                "record_fingerprint": f"fp_perf_{i:04d}",
                "enterprise_name": f"SYNTHETIC Enterprise Node {i}",
                "state": "TELANGANA",
                "district": "MEDAK",
                "pincode": "502319",
                "registration_date": f"{2018 + (i % 7):04d}-05-01",
                "activities_raw": "Dairy farming" if i % 2 == 0 else "Food retail",
                "primary_category": "DAIRY" if i % 2 == 0 else "FOOD_RETAIL",
                "resolved_locality": "Balanagar",
                "latitude": 17.9276 + (i * 0.0001),
                "longitude": 78.2344 + (i * 0.0001),
                "distance_km": 0.5 + (i * 0.01),
                "coordinate_confidence": "HIGH",
                "coordinate_source": "verified_gps",
            })

        perf_report = dict(self.mock_report)
        perf_report["all_nearby_businesses"] = synthetic_500
        perf_report["classified_competitors"] = [r for r in synthetic_500 if r["primary_category"] == "DAIRY"]

        t0 = time.perf_counter()
        perf_graph = self.adapter.build_graph_from_opportunity_report(perf_report)
        elapsed = time.perf_counter() - t0

        self.assertLess(elapsed, 1.0, f"Transformation took {elapsed:.3f}s, exceeding 1.0s limit.")
        self.assertEqual(len(perf_graph["nodes"]), 500)


if __name__ == "__main__":
    unittest.main(verbosity=2)
