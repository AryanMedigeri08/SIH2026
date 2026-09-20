# PHASE 5 — INTERACTIVE BUSINESS ECOSYSTEM GRAPH / MAP
# REPOSITORY INSPECTION AUDIT REPORT

**Date:** 2026-09-12  
**Specification:** `Document_5_Interactive_Business_Ecosystem_Graph_Map_Implementation_Specification.md`  
**Reference Document:** `docs/ECOSYSTEM_GRAPH_CONTEXT_WINDOW.md`  
**Primary Execution Principle:** Re-use existing validated data/analytics contracts from Documents 1–4. Build an adapter/read-model for visualization rather than duplicating UDYAM ingestion or market intelligence pipelines. Zero data fabrication.

---

## 1. COMPREHENSIVE REPOSITORY AUDIT MATRIX

| Area | Existing Implementation | Reusable? | Required Change / Read-Model Adaptation | Risk & Mitigation |
|---|---|:---:|---|---|
| **1. Backend Framework & Routing** | FastAPI with `APIRouter` instances in `backend/app/routers/` mounted in `backend/app/main.py`. | **YES** | Expose ecosystem graph endpoints at `/api/v2/market-analysis/ecosystem-graph` and `GET /api/v1/ecosystem/catchment` per Document 5 Section 5. | Very Low. Fully supported by FastAPI routing. |
| **2. Frontend Framework** | React 18.3.1 + Vite 5.4.11 + TailwindCSS 3.4.16. | **YES** | Add interactive, self-contained `EcosystemIntelligenceMap` and integrate into `MarketDemandPage.jsx`. | Very Low. Tested production build succeeds with Vite. |
| **3. Map Projection** | No external Leaflet in package.json; HTML5 Canvas / SVG geometry supported natively. | **YES** | Build geodesic equirectangular/Mercator Canvas/SVG Geographic Projection with true 5 km & 10 km concentric geodesic rings, pan, zoom, and spatial precision indicators. | Zero external dependency risk; high frame rate, zero CDN failures, 100% offline-capable. |
| **4. Topological Graph Projection** | No external D3 in package.json; pure JS vector physics supported natively. | **YES** | Implement deterministic force-directed physics layout operating on `node.renderPosition` while strictly keeping `node.location` as immutable geographic truth. | Low. Debounced simulation, collision detection, and memoized edge positions avoid layout thrashing. |
| **5. State-Management Approach** | React Context (`ViewModeContext`, `AuthContext`) + component local state. | **YES** | Graph-local state matches Document 5 Section 15 (`viewMode`, `projectionMode`, `catchment`, `temporal`, `activeFilters`, `activeLayers`, `selection`). | None. Clean unidirectional data flow. |
| **6. UDYAM Ingestion Client** | `backend/app/core/udyam/client.py` with OGD API integration and canonical file cache. | **YES** | Consume directly via `VillageIntelligencePipeline`. Do NOT duplicate ingestion or caching. | None. Single source of truth. |
| **7. Enterprise Data Model** | `backend/app/core/udyam/models.py` (`UdyamCanonicalRecord`, `NearbyBusiness`). | **YES** | Transform `NearbyBusiness` into versioned Graph Node schema with `spatialPrecision`, `spatialConfidence`, and `scaleTier`. | Zero. Strict zero-fabrication guarantees. |
| **8. Geography & Location Resolver** | `backend/app/core/udyam/geography/resolver.py` & `gazetteer.py`. | **YES** | Respect `locality_confidence` and `coordinate_confidence`. Map pincode centroids to `spatialPrecision="PINCODE"`. Unresolved nodes go to `unmappedEntities`. | None. Non-negotiable Rule 2.1 enforced. |
| **9. Haversine Utilities** | `backend/app/core/udyam/geography/distance.py` (`haversine_distance`, `calculate_distance`, `classify_market_zone`). | **YES** | Use directly for geodesic distance calculation between graph nodes and catchment center. | Zero. Already validated across 19 test suites. |
| **10. Market Intelligence Engine** | `backend/app/core/intelligence/engine.py` (`MarketOpportunityEngine`). | **YES** | Adapter consumes `analyze_opportunity` output directly (`classified_competitors`, `all_nearby_businesses`, `supply_metrics`). | None. Graph remains a consumer/read-model. |
| **11. HHI Implementation** | `backend/app/core/intelligence/supply.py` (Economic-sector diversification HHI: $\sum \text{pct}_i^2$). | **YES** | Preserve existing validated value. Label strictly as `"existing-project-sector-diversification-HHI"`. Do NOT label as firm revenue market-share. | Zero. Conforms to Rule 2.4. |
| **12. Activity & NIC Classification** | `backend/app/core/udyam/activities/categories.py` & `parser.py`. | **YES** | Map parsed activities to sector color tokens and labels. | None. Consistent category ontology. |
| **13. Competitor Relevance Engine** | `backend/app/core/intelligence/relevance.py` (5-level classifier). | **YES** | Map directly to node `relevanceClass` (`DIRECT_COMPETITOR`, `RELATED_BUSINESS`, etc.). Edge creation strictly derived. | Zero. Conforms to Rule 2.2. |
| **14. Supply-Chain Activity Matrix** | `is_potential_supply_chain` in `categories.py` (deterministic input-output pairs). | **YES** | Use deterministic rules for supply-chain edges with status `"DERIVED"`. Supply chain direction only rendered when configured. | Zero. No transaction claim made. |
| **15. Provenance & Confidence** | `CoordinateConfidence`, `LocalityConfidence`, `PipelineRunMetadata`, `snapshot_id`. | **YES** | Propagate explicit metadata into graph node and edge payloads. | Zero. Full audit trail preserved. |
| **16. Caching Layer** | `client.py` response cache + `snapshot_store` in `snapshot.py`. | **YES** | Cache graph read-models by dataset version + lat/lon + radius + intent. Do not create competing ingestion cache. | None. Fast repeat queries. |
| **17. Database / Persistence** | SQLite / in-memory / JSON snapshot store with no migrations needed for read model. | **YES** | No schema migrations required. Graph read-model is purely an analytical projection. | Zero. Complies with Rule 0. |
| **18. ViewModeContext** | `frontend/src/context/ViewModeContext.jsx` (`isBeneficiary` vs `isBanker`). | **YES** | Wire bi-modal persona rendering directly into the graph component. | None. Seamless user toggle. |
| **19. Test Infrastructure** | Unified test runner in `run_tests.py` with 19 passing suites. | **YES** | Add dedicated test suite `tests/test_ecosystem_graph.py` to `run_tests.py`. | None. CI/CD verified. |
| **20. Design System & Tokens** | `frontend/src/index.css` (`Outfit`, `Inter`, `.glass-panel`, tailored color tokens). | **YES** | Follow project design system with high-contrast, accessible palettes for nodes, rings, and edges. | None. Wow-factor aesthetic maintained. |

---

## 2. KEY ARCHITECTURAL DECISIONS

1. **Read-Model Adapter Boundary (`backend/app/core/intelligence/ecosystem_graph.py`):**
   - Implements `EcosystemGraphAdapter`.
   - Takes validated outputs from `MarketOpportunityEngine.analyze_opportunity` or orchestrates a catchment query.
   - Transforms records into versioned `EcosystemGraphResponse` conforming to Document 5 Sections 5–8.
   - Enforces zero-fabrication: nodes lacking coordinates are collected into `unmappedEntities` and excluded from `nodes`.
   - Edges are generated deterministically using configured competitor activity rules and supply-chain matrix rules. All edges are explicitly marked `relationshipStatus="DERIVED"`.
   - Workforce scale tier is strictly `"UNKNOWN"` unless validated employment data exists for that specific enterprise.

2. **Dual-Projection Frontend Component (`frontend/src/components/Dashboard/EcosystemIntelligenceMap.jsx`):**
   - Self-contained, modular component with zero invasive coupling to unrelated pages.
   - Supports seamless projection switching:
     - **Geographic Mode:** Canvas/SVG with geodesic scale (center lat/lon), 5 km and 10 km concentric geodesic buffer rings, enterprise node pins, spatial precision rings, and derived edge links.
     - **Topological Mode:** D3-style force simulation (spring tension along derived edges, charge repulsion, collision avoidance, and sector clustering) that calculates `renderPosition` without altering `location`.
   - Features 5 composable layers: Catchment Rings, Business Nodes, Economic Relationships, Density Surface (with honest `INSUFFICIENT_DATA` handling), and Opportunity / White-Space overlay (with honest `UNAVAILABLE` handling).
   - Bi-modal persona rendering: Beneficiary view (plain-language radar, nearest competitor, 1-tap 3/5/10km radius) vs Banker view (HHI sector-diversification gauge, decadal CAGR, ego-network drill-down).
   - Composable filters, dynamic interactive legend, and temporal scrubber driven by actual `RegistrationDate` years.
   - Accessible node and edge inspection panels with full provenance and data quality warnings.

3. **Validation & Verification:**
   - Dedicated backend test suite: `tests/test_ecosystem_graph.py` covering geometry, data integrity, relationships, temporal filtering, metrics, and error states.
   - Golden test dataset: deterministic fixture explicitly labelled `TEST FIXTURE — NOT REAL BUSINESS DATA`.
   - Full master test suite validation via `run_tests.py` (targeting 20/20 passing suites).
   - Vite frontend production build verification (`npm run build`).

---
*Audit Completed by Opus 4.6 per Document 5 Section 4 instructions.*
