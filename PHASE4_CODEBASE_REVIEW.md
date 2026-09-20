# PHASE4_CODEBASE_REVIEW.md — Comprehensive Platform Architectural Inventory

**Audit Standard:** Document 4, Phase 1 (Codebase Integrity Review)  
**Evaluation Date:** September 2026  
**Auditor:** Antigravity Autonomous Engineering Subsystem  
**System:** Udyam Saathi (उद्यम साथी) — Rural & Semi-Urban MSME Intelligence, Feasibility & Bank Credit Advisory Platform  

---

## 1. Architectural Overview & Component Map

The platform is structured into distinct, decoupled operational tiers:
```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             REACT + VITE FRONTEND                                │
│  (Landing, Wizard, Calculator, Market Demand, DPR Export, Translated Dashboard)  │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ JSON REST HTTP / JWT Auth
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│                           FASTAPI REST APPLICATION                               │
│  (TelemetryMiddleware, AuthRouter, FeasibilityRouter, MarketIntelligenceRouter)  │
└──────┬──────────────────────┬──────────────────────┬──────────────────────┬──────┘
       │                      │                      │                      │
┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐
│  FINANCIAL  │        │ SUPERVISED  │        │    UDYAM    │        │  OPPORTUNITY│
│ CALCULATOR  │        │ ML (XGBoost)│        │   VILLAGE   │        │   ENGINE    │
│  & SCHEMES  │        │ & TreeSHAP  │        │  PIPELINE   │        │ (5-Class,   │
│             │        │             │        │ (Geocoding) │        │ Demand, HHI)│
└─────────────┘        └─────────────┘        └──────┬──────┘        └──────┬──────┘
                                                     │                      │
                                              ┌──────▼──────────────────────▼──────┐
                                              │    IMMUTABLE DATA SNAPSHOT STORE   │
                                              │  (DataSnapshot, SHA-256 Hashes)    │
                                              └────────────────────────────────────┘
```

---

## 2. Core Subsystems & Component Inventory

### A. Application Entrypoints & Configuration

| File | Component / Responsibility | Inputs | Outputs | Test Coverage | Wiring / Production Status |
|---|---|---|---|---|---|
| [`backend/app/main.py`](file:///c:/SIH2026/backend/app/main.py) | Master FastAPI application entrypoint, lifespan manager, CORS middleware, global exception handler | HTTP Requests | JSON HTTP Responses | `test_modular_endpoints.py`, `test_api_and_pipeline.py` | **WIRED & ACTIVE** (Port 8000, Uvicorn) |
| [`backend/app/config.py`](file:///c:/SIH2026/backend/app/config.py) | Application settings, environment loading (`.env`), CORS parser, paths | OS environment variables, `.env` | `Settings` singleton | Unit tests | **WIRED & ACTIVE** |
| [`backend/app/core/telemetry.py`](file:///c:/SIH2026/backend/app/core/telemetry.py) | Distributed correlation tracing, latency tracking, PII sanitization | HTTP Requests/Responses | `X-Correlation-ID`, `X-Response-Time-ms` headers | `test_modular_endpoints.py` | **WIRED & ACTIVE** |
| [`backend/app/database.py`](file:///c:/SIH2026/backend/app/database.py) | Neon Serverless PostgreSQL connection pool with durable SQLite local fallback | SQL queries, CRUD requests | Connection pool, records, session management | `test_neon_persistence.py`, `test_business_management.py` | **WIRED & ACTIVE** |

---

### B. UDYAM Village Intelligence Engine (Document 1)

| File | Component / Responsibility | Inputs | Outputs | Test Coverage | Wiring / Production Status |
|---|---|---|---|---|---|
| [`backend/app/core/udyam/client.py`](file:///c:/SIH2026/backend/app/core/udyam/client.py) | Official UDYAM / data.gov.in API client with retry and error handling | State, District, max_records | Raw MSME enterprise records | `test_udyam_api_and_pipeline.py` | **WIRED & ACTIVE** |
| [`backend/app/core/udyam/address.py`](file:///c:/SIH2026/backend/app/core/udyam/address.py) | Address cleaner, token extraction, pincode extraction, deduplication | Raw address strings | `NormalizedAddress` objects | `test_udyam_engine.py` | **WIRED & ACTIVE** |
| [`backend/app/core/udyam/geocoding.py`](file:///c:/SIH2026/backend/app/core/udyam/geocoding.py) | Non-fabricating geocoding engine, spatial gazetteer lookup, confidence tracking | Normalized address, village, district | `GeocodingResult` (lat, lon, resolution, confidence) | `test_udyam_engine.py`, `test_audit_regression.py` | **WIRED & ACTIVE** (Zero guessed coordinates) |
| [`backend/app/core/udyam/pipeline.py`](file:///c:/SIH2026/backend/app/core/udyam/pipeline.py) | End-to-end Village Intelligence Pipeline (fetch, normalize, geocode, zone, snapshot) | Target location parameters | `VillageMarketResult`, snapshot record | `test_udyam_api_and_pipeline.py` | **WIRED & ACTIVE** |
| [`backend/app/core/udyam/snapshot.py`](file:///c:/SIH2026/backend/app/core/udyam/snapshot.py) | Immutable SHA-256 hashed DataSnapshot repository and replay engine | Raw pipeline records, query parameters | `DataSnapshot`, canonical hash, disk JSON | `test_audit_regression.py` | **WIRED & ACTIVE** |
| [`backend/app/core/udyam/activities/categories.py`](file:///c:/SIH2026/backend/app/core/udyam/activities/categories.py) | Business ontology mapping keywords and NIC codes to 18 enterprise categories | Enterprise activity text, NIC code | Category identifier and label | `test_udyam_engine.py` | **WIRED & ACTIVE** |

---

### C. MSME Market Intelligence & Opportunity Engine (Document 2)

| File | Component / Responsibility | Inputs | Outputs | Test Coverage | Wiring / Production Status |
|---|---|---|---|---|---|
| [`backend/app/core/intelligence/models.py`](file:///c:/SIH2026/backend/app/core/intelligence/models.py) | Core dataclasses: `CompetitorRecord`, `SupplyMetrics`, `DemandFeatures`, `EvidenceObject`, `MarketOpportunityReport` | Data fields | Typed intelligence objects | Used across all suites | **WIRED & ACTIVE** |
| [`backend/app/core/intelligence/intents.py`](file:///c:/SIH2026/backend/app/core/intelligence/intents.py) | Business intent catalog, synonyms, NIC code mappings, intent resolver | User business query | Canonical `BusinessIntent` | `test_opportunity_engine.py` | **WIRED & ACTIVE** |
| [`backend/app/core/intelligence/relevance.py`](file:///c:/SIH2026/backend/app/core/intelligence/relevance.py) | Deterministic 5-class competitor classifier (`DIRECT`, `RELATED`, `INDIRECT`, `NON_RELEVANT`, `UNKNOWN`) | Enterprise record, BusinessIntent | `CompetitorRecord` with relevance class and reason | `test_audit_gold_set.py` (105 records) | **WIRED & ACTIVE** |
| [`backend/app/core/intelligence/supply.py`](file:///c:/SIH2026/backend/app/core/intelligence/supply.py) | Supply concentration, core 5km/nearby 10km counts, nearest distance, Sector Diversification HHI | Classified records, population | `SupplyMetrics` | `test_opportunity_engine.py` | **WIRED & ACTIVE** |
| [`backend/app/core/intelligence/demand.py`](file:///c:/SIH2026/backend/app/core/intelligence/demand.py) | Demand Feature Store querying Census, Antyodaya, and ODOP adapters | Location parameters, BusinessIntent | `DemandFeatures` | `test_opportunity_engine.py` | **WIRED & ACTIVE** |
| [`backend/app/core/intelligence/opportunity.py`](file:///c:/SIH2026/backend/app/core/intelligence/opportunity.py) | 5 transparent indicators, composite score formula (0–100), hard guardrails (`SATURATED`, `CONSTRAINED`) | SupplyMetrics, DemandFeatures | OpportunityIndicators, composite score, verdict, confidence | `test_opportunity_engine.py`, `test_audit_regression.py` | **WIRED & ACTIVE** |
| [`backend/app/core/intelligence/explainability.py`](file:///c:/SIH2026/backend/app/core/intelligence/explainability.py) | Decision-support evidence generator: top drivers, risk factors, missing evidence, confidence reasons | Opportunity calculations, location | `EvidenceObject` with zero fabricated numbers | `test_audit_regression.py` | **WIRED & ACTIVE** |
| [`backend/app/core/intelligence/scenarios.py`](file:///c:/SIH2026/backend/app/core/intelligence/scenarios.py) | Multi-radius sweeps (5, 10, 15, 20 km) and 4-tier unmapped uncertainty stress tests (0%, 15%, 50%, 100%) | Classified records, DemandFeatures | `list[SensitivityScenario]` | `test_audit_regression.py` | **WIRED & ACTIVE** |
| [`backend/app/core/intelligence/engine.py`](file:///c:/SIH2026/backend/app/core/intelligence/engine.py) | Master orchestrator coordinating pipeline, adapters, scoring, explainability, and multi-category comparison | User request parameters | `MarketOpportunityReport` | `test_opportunity_engine.py`, `test_audit_cross_state.py` | **WIRED & ACTIVE** |

---

### D. Government Dataset Adapters (`backend/app/core/adapters/`)

| File | Component / Responsibility | Inputs | Outputs | Test Coverage | Wiring / Production Status |
|---|---|---|---|---|---|
| [`base.py`](file:///c:/SIH2026/backend/app/core/adapters/base.py) | Abstract interface `GovernmentDatasetAdapter` and `DatasetMetadata` | Contract methods | Standardized metadata & features | All adapter tests | **WIRED & ACTIVE** |
| [`registry.py`](file:///c:/SIH2026/backend/app/core/adapters/registry.py) | Registry of official government sources (UDYAM, Census 2011, Antyodaya, ODOP) | Source ID lookups | `DatasetMetadata` entries | `test_opportunity_engine.py` | **WIRED & ACTIVE** |
| [`population.py`](file:///c:/SIH2026/backend/app/core/adapters/population.py) | Ingests Census 2011 population baseline and computes projected population baseline to 2026 using state CAGRs | Village, District, State | Projected population, households, CAGR source | `test_audit_cross_state.py` | **WIRED & ACTIVE** |
| [`amenities.py`](file:///c:/SIH2026/backend/app/core/adapters/amenities.py) | Ingests Mission Antyodaya indicators (power hours, road connectivity, banking, storage) | Village, District, State | Amenities features, infrastructure score, join_level | `test_audit_cross_state.py` | **WIRED & ACTIVE** |
| [`odop.py`](file:///c:/SIH2026/backend/app/core/adapters/odop.py) | Ingests statutory One District One Product (ODOP) designations | District, State, BusinessIntent | `is_odop_aligned`, product name | `test_opportunity_engine.py` | **WIRED & ACTIVE** |

---

### E. Financial Viability, DPR & AI Advisory

| File | Component / Responsibility | Inputs | Outputs | Test Coverage | Wiring / Production Status |
|---|---|---|---|---|---|
| [`financial_calculator.py`](file:///c:/SIH2026/backend/app/core/financial_calculator.py) | P&L, DSCR, IRR, BEP, and Working Capital calculations | Project cost, revenues, expenses | Complete 5-year financial statements | `test_phase2.py` | **WIRED & ACTIVE** |
| [`inference.py`](file:///c:/SIH2026/backend/app/core/inference.py) | Supervised XGBoost viability classification & TreeSHAP local explanations | 10 financial and market features | Viability score, class, SHAP waterfall | `test_phase3.py` | **WIRED & ACTIVE** |
| [`dpr_generator.py`](file:///c:/SIH2026/backend/app/core/dpr_generator.py) | 7-section Bank Detailed Project Report (DPR) compiler | Full project intelligence | Structured DPR JSON & PDF export | `test_phase5.py` | **WIRED & ACTIVE** |
| [`synthesizer.py`](file:///c:/SIH2026/backend/app/core/synthesizer.py) | Groq LLM executive synthesis with strict prompt injection guardrails | Financial & market metrics | Plain-language executive memo | `test_phase6.py`, `test_chat_service.py` | **WIRED & ACTIVE** |

---

### F. REST API Routers (`backend/app/routers/`)

| File | Prefix | Endpoints | Test Coverage | Status |
|---|---|---|---|---|
| [`market_intelligence.py`](file:///c:/SIH2026/backend/app/routers/market_intelligence.py) | `/api/v2/market-analysis` | `POST /`, `POST /opportunity`, `POST /compare`, `GET /categories`, `GET /intents`, `GET /sources`, `GET /health` | `test_modular_endpoints.py`, `test_udyam_api_and_pipeline.py` | **WIRED & ACTIVE** |
| [`feasibility.py`](file:///c:/SIH2026/backend/app/routers/feasibility.py) | `/api/v2/feasibility` | `POST /generate`, `GET /{id}`, `GET /{id}/dpr` | `test_modular_endpoints.py` | **WIRED & ACTIVE** |
| [`financial.py`](file:///c:/SIH2026/backend/app/routers/financial.py) | `/api/v2/financial` | `POST /calculate` | `test_modular_endpoints.py` | **WIRED & ACTIVE** |
| [`data_sources.py`](file:///c:/SIH2026/backend/app/routers/data_sources.py) | `/api/v2/data-sources` | `GET /`, `GET /schemes`, `GET /stats` | `test_modular_endpoints.py` | **WIRED & ACTIVE** |
| [`locations.py`](file:///c:/SIH2026/backend/app/routers/locations.py) | `/api/v2/locations` | `GET /states`, `GET /districts`, `GET /blocks` | `test_modular_endpoints.py` | **WIRED & ACTIVE** |
| [`auth.py`](file:///c:/SIH2026/backend/app/routers/auth.py) | `/api/v2/auth` | `POST /register`, `POST /session`, `GET /me`, `PATCH /me`, `POST /logout` | `test_modular_endpoints.py` | **WIRED & ACTIVE** |
| [`projects.py`](file:///c:/SIH2026/backend/app/routers/projects.py) | `/api/v2/projects` | `GET /`, `POST /`, `GET /{id}`, `DELETE /{id}` | `test_modular_endpoints.py` | **WIRED & ACTIVE** |
| [`chat.py`](file:///c:/SIH2026/backend/app/routers/chat.py) | `/api/v2/chat` | `POST /query`, `POST /audio`, `GET /health` | `test_chat_service.py`, `test_audio_chat_service.py` | **WIRED & ACTIVE** |
| [`translation.py`](file:///c:/SIH2026/backend/app/routers/translation.py) | `/api/v2/translate` | `POST /`, `POST /batch` | `test_translation_service.py` | **WIRED & ACTIVE** |

---

## 3. Frontend Architecture & API Integration

* **Framework:** React 18 + Vite 5 + TailwindCSS.
* **Component Model:** Fully modular dashboard with dynamic routing (`react-router-dom`), translated text wrapper (`TranslatedText`), and glassmorphism styling tokens in `index.css`.
* **State Management:** React Context (`AuthContext`, `ProjectContext`) with local storage caching.
* **API Integration:** Client service layer in [`frontend/src/services/api.js`](file:///c:/SIH2026/frontend/src/services/api.js).
* **Demographic Representation:** Uses `"Projected Pop (2026)"` and `"Base Pop (2011)"` with CAGR indications; never claims projected population is observed headcount.

---

## 4. Test Suite Inventory

18 active verification suites in [`run_tests.py`](file:///c:/SIH2026/run_tests.py):
1. `test_phase2.py`: Financial engine validation
2. `test_phase3.py`: ML viability model & SHAP explainer
3. `test_phase4.py`: Government scheme matching
4. `test_phase5.py`: Automated DPR memorandum generation
5. `test_phase6.py`: AI narrative synthesis
6. `test_phase7.py`: Audio & conversational multi-modality
7. `test_business_management.py`: User & project persistence
8. `test_neon_persistence.py`: Database pool and fallback
9. `test_chat_service.py`: LLM security guardrails & prompt injection defense
10. `test_audio_chat_service.py`: Voice STT / TTS pipelines
11. `test_translation_service.py`: Indic localization
12. `test_opportunity_matcher.py`: Category & scheme rules
13. `test_udyam_engine.py`: Address cleaning & classification
14. `test_udyam_api_and_pipeline.py`: Pipeline integration & endpoints
15. `test_opportunity_engine.py`: Document 2 market intelligence suite (29 tests)
16. `test_audit_gold_set.py`: 105-record gold competitor benchmark
17. `test_audit_regression.py`: Deterministic snapshot replay & guardrails
18. `test_audit_cross_state.py`: Multi-state validation (TS, MH, KA, UP)

---

## 5. Summary Finding
The codebase has zero orphaned or mock-only intelligence layers: all components are fully imported, registered in `main.py`, tested by automated suites, and ready for production hardening.
