# Phase 6 Integration Repository & Architecture Audit
## Udyam Saathi — Cross-Component End-to-End Consistency

> **Document 6 Audit Contract**: Verifies that the existing Udyam Saathi components operate as a single, consistent, reproducible, evidence-backed analytical system from source government data to final user-facing dashboards.

---

## 1. Architectural Chain of Custody

The platform enforces a unidirectional, deterministic analytical pipeline without duplicate or competing scoring formulas across 9 standardized architecture layers:

### 1.1 Standardized 6-Stage Analytical Dataflow Chain (Section 0)
```text
┌────────────────────────────────────────────────────────┐
│ Stage 1: UDYAM Ingestion & Normalization Layer         │
│          (data.gov.in 7-Column API, Census 2011, SHRUG)│
└──────────────────────────┬─────────────────────────────┘
                           │ Canonical Raw Records & SHA-256 Fingerprint
┌──────────────────────────▼─────────────────────────────┐
│ Stage 2: Village Intelligence Engine                   │
│          (pipeline.py, resolver.py, gazetteer.py)      │
└──────────────────────────┬─────────────────────────────┘
                           │ Resolved Spatial Anchors & Nearby Businesses Pool
┌──────────────────────────▼─────────────────────────────┐
│ Stage 3: Market Intelligence & Opportunity Engine      │
│          (engine.py, demand.py, supply.py)             │
└──────────────────────────┬─────────────────────────────┘
                           │ MarketOpportunityReport (composite_score, guardrails, HHI)
┌──────────────────────────▼─────────────────────────────┐
│ Stage 4: Ecosystem Graph Read-Model Adapter            │
│          (ecosystem_graph.py — READ MODEL PROJECTION)  │
└──────────────────────────┬─────────────────────────────┘
                           │ EcosystemGraphResponse (Nodes, Edges, Layers, Metadata)
┌──────────────────────────▼─────────────────────────────┐
│ Stage 5: Decision & Recommendation Presentation Layer  │
│          (Guardrail Overlays & Disclaimers)            │
└──────────────────────────┬─────────────────────────────┘
                           │ Bi-Modal Persona Payloads & Disclosures
┌──────────────────────────▼─────────────────────────────┐
│ Stage 6: Beneficiary / Banker UI & API Client          │
│          (EcosystemIntelligenceMap.jsx, API Client)    │
└────────────────────────────────────────────────────────┘
```

### 1.2 The 9 Standardized Architecture Layers (Section 1)
1. **Layer 1: UDYAM Ingestion & Normalization Layer** (`client.py`, `models.py`, `normalization.py`, `snapshot.py`)
2. **Layer 2: Village Intelligence Engine** (`pipeline.py`, `resolver.py`, `gazetteer.py`)
3. **Layer 3: Market Intelligence & Opportunity Engine** (`engine.py`, `demand.py`, `supply.py`, `opportunity.py`)
4. **Layer 4: Ecosystem Graph Read-Model Adapter** (`ecosystem_graph.py`)
5. **Layer 5: FastAPI Router & API Contract Layer** (`market_intelligence.py`, `schemas.py`)
6. **Layer 6: Beneficiary Journey Experience** (`MarketDemandPage.jsx`, plain-language terminology)
7. **Layer 7: Banker Journey Experience** (`BankerReportPage.jsx`, spatial anchor & metric diagnostics)
8. **Layer 8: Guarded LLM Explanation Layer** (`chat_service.py`, advisory-only boundary)
9. **Layer 9: Shared Schemas & Common Utilities** (`schemas.py`, `categories.py`, `geo.py`)

---

## 2. Component Inventory & Audit Specifications

### Component 1: UDYAM Ingestion, Normalization & Cache
- **Actual Module / File:**
  - Ingestion Client: [`backend/app/core/udyam/client.py`](file:///c:/SIH2026/backend/app/core/udyam/client.py)
  - Data Models & Fingerprinting: [`backend/app/core/udyam/models.py`](file:///c:/SIH2026/backend/app/core/udyam/models.py)
  - Text/Address Normalization: [`backend/app/core/udyam/normalization.py`](file:///c:/SIH2026/backend/app/core/udyam/normalization.py)
  - Snapshot Store: [`backend/app/core/udyam/snapshot.py`](file:///c:/SIH2026/backend/app/core/udyam/snapshot.py)
- **Public Interface:**
  - `UdyamClient.get_records(state, district, max_records, snapshot_id)`
  - `compute_record_fingerprint(record)` -> 64-char hex SHA-256 string
  - `normalize_address(address)`, `normalize_text_basic(text)`
- **Upstream Dependency:** External data.gov.in API resource (`8b68ae56-84cf-4728-a0a6-1be11028dea7`) or offline immutable raw storage (`backend/app/core/data/raw/udyam/`).
- **Downstream Consumer:** `VillageIntelligencePipeline` (`pipeline.py`).
- **Source-of-Truth Status:** **AUTHORITATIVE RAW SOURCE** for enterprise registration vintage, reported enterprise name, raw communication address, and declared operational activities.
- **Duplicated Logic:** None. Centralized in `client.py` and `normalization.py`.
- **Risks:** 7-column schema lacks enterprise balance sheets, exact door numbers, or direct verified GPS. Handled via spatial precision hierarchy and unmapped segregation.
- **Classification:** **`PASS`**

---

### Component 2: Village Intelligence Engine
- **Actual Module / File:**
  - Pipeline Orchestrator: [`backend/app/core/udyam/pipeline.py`](file:///c:/SIH2026/backend/app/core/udyam/pipeline.py)
  - Geographic Resolver: [`backend/app/core/udyam/geography/resolver.py`](file:///c:/SIH2026/backend/app/core/udyam/geography/resolver.py)
  - Gazetteer: [`backend/app/core/udyam/geography/gazetteer.py`](file:///c:/SIH2026/backend/app/core/udyam/geography/gazetteer.py)
  - Distance Utilities: [`backend/app/core/udyam/geography/distance.py`](file:///c:/SIH2026/backend/app/core/udyam/geography/distance.py)
  - Activity Parser: [`backend/app/core/udyam/activities/parser.py`](file:///c:/SIH2026/backend/app/core/udyam/activities/parser.py)
  - Category Ontology: [`backend/app/core/udyam/activities/categories.py`](file:///c:/SIH2026/backend/app/core/udyam/activities/categories.py)
- **Public Interface:**
  - `VillageIntelligencePipeline.analyze(state, district, village, target_lat, target_lon, radius_km, core_radius_km, business_category, pincode, max_records, snapshot_id)` -> `VillageMarketResult`
  - `GeographicResolver.resolve_record(record, target)` -> `GeographicResolution`
  - `parse_activities(activities_str)` -> `list[ActivityRecord]`
- **Upstream Dependency:** `UdyamClient`, Gazetteer dictionary (`backend/app/data/`).
- **Downstream Consumer:** `MarketOpportunityEngine` (`backend/app/core/intelligence/engine.py`).
- **Source-of-Truth Status:** **AUTHORITATIVE SPATIAL ANCHOR & ACTIVITY EXTRACTION LAYER**.
- **Duplicated Logic:** None. Distance calculation strictly utilizes `haversine_distance` from `distance.py`.
- **Risks:** Ambiguous village names resolved via administrative district/taluka bounding with confidence tracking (`HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`).
- **Classification:** **`PASS`**

---

### Component 3: Market Intelligence & Opportunity Engine
- **Actual Module / File:**
  - Master Engine: [`backend/app/core/intelligence/engine.py`](file:///c:/SIH2026/backend/app/core/intelligence/engine.py)
  - Competitor Relevance: [`backend/app/core/intelligence/relevance.py`](file:///c:/SIH2026/backend/app/core/intelligence/relevance.py)
  - Supply Concentration: [`backend/app/core/intelligence/supply.py`](file:///c:/SIH2026/backend/app/core/intelligence/supply.py)
  - Government Demand Features: [`backend/app/core/intelligence/demand.py`](file:///c:/SIH2026/backend/app/core/intelligence/demand.py)
  - Opportunity Indicators & Scoring: [`backend/app/core/intelligence/opportunity.py`](file:///c:/SIH2026/backend/app/core/intelligence/opportunity.py)
  - Evidence & Explainability: [`backend/app/core/intelligence/explainability.py`](file:///c:/SIH2026/backend/app/core/intelligence/explainability.py)
  - Sensitivity Stress Testing: [`backend/app/core/intelligence/scenarios.py`](file:///c:/SIH2026/backend/app/core/intelligence/scenarios.py)
  - External Adapters: [`backend/app/core/adapters/`](file:///c:/SIH2026/backend/app/core/adapters/)
- **Public Interface:**
  - `MarketOpportunityEngine.analyze_opportunity(...)` -> `MarketOpportunityReport`
  - `MarketOpportunityEngine.compare_categories(...)` -> `list[dict]`
- **Upstream Dependency:** `VillageIntelligencePipeline`, `DemandFeatureStore` (Census 2011, 613 Amenities).
- **Downstream Consumer:** `EcosystemGraphAdapter` (`backend/app/core/intelligence/ecosystem_graph.py`), `market_intelligence` router.
- **Source-of-Truth Status:** **AUTHORITATIVE ANALYTICAL TRUTH** for composite feasibility scoring, concentration (HHI), guardrail verdicts (`SATURATED_MARKET`, `CONSTRAINED_MARKET`, `INSUFFICIENT_DATA`), and explainability evidence.
- **Duplicated Logic:** None. Single analytical formula used uniformly.
- **Risks:** High competitor density in small radii correctly triggers `SATURATED_MARKET` guardrail.
- **Classification:** **`PASS`**

---

### Component 4: Ecosystem Graph Read-Model Adapter
- **Actual Module / File:**
  - Adapter Module: [`backend/app/core/intelligence/ecosystem_graph.py`](file:///c:/SIH2026/backend/app/core/intelligence/ecosystem_graph.py)
- **Public Interface:**
  - `EcosystemGraphAdapter.build_graph(...)` -> `dict[str, Any]`
  - `EcosystemGraphAdapter.build_graph_from_opportunity_report(report, radius_km, visualization_radius_km)` -> `dict[str, Any]`
  - `validate_ecosystem_graph_request(target_lat, target_lon, radius_km)` -> `list[str]`
- **Upstream Dependency:** `MarketOpportunityEngine`, `MarketOpportunityReport`.
- **Downstream Consumer:** REST API Router (`/api/v2/market-analysis/ecosystem-graph`), Frontend UI.
- **Source-of-Truth Status:** **READ-MODEL CONSUMER / PROJECTION LAYER ONLY**.
- **Duplicated Logic:** None. Does not recalculate opportunity scores or HHI; consumes them verbatim from `MarketOpportunityReport`.
- **Risks:** Must never fabricate coordinates or claim derived edges are confirmed commercial transactions. Handled via explicit `DERIVED` edge flags and coordinate segregation.
- **Classification:** **`PASS`**

---

### Component 5: Frontend API Client
- **Actual Module / File:**
  - Client Services: [`frontend/src/services/api.js`](file:///c:/SIH2026/frontend/src/services/api.js)
- **Public Interface:**
  - `marketOpportunityApi.getEcosystemGraph(payload, token)` -> `POST /api/v2/market-analysis/ecosystem-graph`
  - `marketOpportunityApi.analyzeOpportunity(payload, token)` -> `POST /api/v2/market-analysis/analyze`
  - `marketOpportunityApi.getCategories(token)` -> `GET /api/v2/market-analysis/categories`
- **Upstream Dependency:** FastAPI REST backend endpoints.
- **Downstream Consumer:** `MarketDemandPage.jsx`, `FeasibilityWizard.jsx`.
- **Source-of-Truth Status:** Transport layer. Zero local analytical recalculations.
- **Duplicated Logic:** None.
- **Risks:** Token expiration / backend timeout. Handled via graceful fallback error states.
- **Classification:** **`PASS`**

---

### Component 6: Beneficiary Journey Flow
- **Actual Module / File:**
  - Feasibility Wizard: [`frontend/src/components/Wizard/FeasibilityWizard.jsx`](file:///c:/SIH2026/frontend/src/components/Wizard/FeasibilityWizard.jsx)
  - Market Demand Page: [`frontend/src/pages/report/MarketDemandPage.jsx`](file:///c:/SIH2026/frontend/src/pages/report/MarketDemandPage.jsx)
  - Map Component: [`frontend/src/components/Dashboard/EcosystemIntelligenceMap.jsx`](file:///c:/SIH2026/frontend/src/components/Dashboard/EcosystemIntelligenceMap.jsx) (Beneficiary Mode)
- **Public Interface:**
  - User selection of locality (state, district, village) and business intent (e.g., Dairy, Kirana).
  - 1-tap walking radius toggle (5 km / 10 km).
  - Plain-language "Business Neighborhood Map", competitor radar, and demand breakdown.
- **Upstream Dependency:** `MarketOpportunityEngine`, `EcosystemGraphAdapter`.
- **Downstream Consumer:** Rural borrower / micro-entrepreneur.
- **Source-of-Truth Status:** Presentation layer.
- **Duplicated Logic:** None. All counts and metrics rendered directly from backend payload.
- **Risks:** Cognitive overload. Solved by bi-modal persona adaptation hiding deep banking indices in beneficiary view.
- **Classification:** **`PASS`**

---

### Component 7: Banker Journey Flow
- **Actual Module / File:**
  - Appraisal Page: [`frontend/src/pages/report/BankerReportPage.jsx`](file:///c:/SIH2026/frontend/src/pages/report/BankerReportPage.jsx)
  - Map Component: [`frontend/src/components/Dashboard/EcosystemIntelligenceMap.jsx`](file:///c:/SIH2026/frontend/src/components/Dashboard/EcosystemIntelligenceMap.jsx) (Banker Mode)
  - Node Detail Panel & Unmapped Entities Drawer.
- **Public Interface:**
  - Deep underwriting workspace: Sector Diversification HHI, decadal CAGR, spatial precision indicators, ego-network inspection.
- **Upstream Dependency:** `MarketOpportunityEngine`, `EcosystemGraphAdapter`.
- **Downstream Consumer:** Bank branch manager / credit loan appraisal officer.
- **Source-of-Truth Status:** Presentation & underwriting audit layer.
- **Duplicated Logic:** None.
- **Risks:** Misinterpreting derived edges as audited invoices. Mitigated by prominent `DERIVED` badge and explicit rule ID disclosure.
- **Classification:** **`PASS`**

---

### Component 8: LLM / Conversational Advisory Layer
- **Actual Module / File:**
  - Advisory Service: [`backend/app/core/chat_service.py`](file:///c:/SIH2026/backend/app/core/chat_service.py)
  - Chat Router: [`backend/app/routers/chat.py`](file:///c:/SIH2026/backend/app/routers/chat.py)
- **Public Interface:**
  - `ChatService.generate_response(message, session_id, language, dpr_context)`
- **Upstream Dependency:** Institutional Data Sources Catalog, session history, verified DPR context.
- **Downstream Consumer:** Interactive conversational assistant in dashboard.
- **Source-of-Truth Status:** **ADVISORY ONLY**. Strictly downstream of deterministic scoring.
- **Duplicated Logic:** None. Does not calculate opportunity scores, competitor counts, or spatial distances.
- **Risks:** Hallucination / overriding guardrails. Prevented by strict context injection: LLM cannot override `SATURATED_MARKET` or fabricate business coordinates.
- **Classification:** **`PASS`**

---

### Component 9: Shared Schemas & Data Contracts
- **Actual Module / File:**
  - Pydantic Schemas: [`backend/app/models/schemas.py`](file:///c:/SIH2026/backend/app/models/schemas.py)
- **Public Interface:**
  - `EcosystemGraphRequest`, `EcosystemGraphResponse`, `MarketOpportunityReport`
- **Upstream Dependency:** Pydantic V2 core.
- **Downstream Consumer:** All FastAPI route handlers, OpenAPI schema generation, frontend consumers.
- **Source-of-Truth Status:** **AUTHORITATIVE REST API SCHEMA DEFINITION**.
- **Duplicated Logic:** None.
- **Risks:** Schema drifting across client/server. Prevented by strict field validation and typed response models.
- **Classification:** **`PASS`**

---

## 3. Cross-Component Integration Inventory Summary

| # | Component Area | Source-of-Truth Role | Duplication | Risk Level | Status |
|:---:|:---|:---|:---:|:---:|:---:|
| 1 | UDYAM Ingestion / Cache | Authoritative Raw Source | None | Low | **PASS** |
| 2 | Village Intelligence | Authoritative Spatial Anchors | None | Low | **PASS** |
| 3 | Market Intelligence Engine | Authoritative Analytical Truth | None | Low | **PASS** |
| 4 | Ecosystem Graph Read-Model | Read-Model Projection Only | None | Low | **PASS** |
| 5 | Frontend API Client | Transport Layer | None | Low | **PASS** |
| 6 | Beneficiary Flow | Presentation Layer | None | Low | **PASS** |
| 7 | Banker Flow | Underwriting Presentation Layer | None | Low | **PASS** |
| 8 | LLM Advisory Layer | Advisory / Explanatory Only | None | Low | **PASS** |
| 9 | Shared Pydantic Schemas | Authoritative Data Contract | None | Low | **PASS** |

**Conclusion:** All 9 major component areas have clear architectural boundaries, explicit sources of truth, zero duplicate competing scoring pipelines, and strict compliance with Document 6 integration requirements.
