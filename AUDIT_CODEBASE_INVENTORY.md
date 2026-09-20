# AUDIT_CODEBASE_INVENTORY.md — Codebase & Architectural Inventory

**Audit Date:** 2026-09-11  
**Auditor:** Antigravity AI Engine (Document 3 Audit Subsystem)  
**Standard:** Document 3, Section 4 (Gate 1 — Codebase Inventory)  
**Project:** Udyam Saathi — MSME Village Intelligence, Market Analysis & Opportunity Engine  

---

## 1. Runtime & Environment Baseline
* **Python Runtime:** Python 3.10.11 (win32)
* **Virtual Environment:** `C:\SIH2026\venv`
* **Operating System:** Windows 11 Enterprise (NT 10.0)
* **Backend Root:** `c:\SIH2026\backend`
* **Primary Entrypoint:** `backend/app/main.py` (`app:app` via Uvicorn on port 8000)
* **Frontend Root:** `c:\SIH2026\frontend` (Vite + React + TailwindCSS)

---

## 2. Dependency Audit
| Package Category | Key Dependencies | Audited Version | Production Status |
|---|---|---|---|
| **Web / ASGI** | `fastapi`, `uvicorn[standard]`, `starlette` | FastAPI >= 0.111.0, Uvicorn >= 0.30.0 | Production |
| **Data Validation** | `pydantic`, `pydantic-settings`, `python-dotenv` | Pydantic v2.7+, Settings v2.2+ | Production |
| **Authentication** | `firebase-admin`, `pyjwt`, `cryptography` | Firebase Admin 6.5+, PyJWT 2.8+ | Production |
| **Machine Learning** | `numpy`, `pandas`, `scikit-learn`, `xgboost`, `shap`, `scipy`, `joblib` | XGBoost 2.0+, Scikit-Learn 1.4+ | Production |
| **Databases** | `asyncpg`, `psycopg2-binary`, `sqlite3` (std lib) | asyncpg 0.29+, psycopg2 2.9+ | Production |
| **External Clients** | `groq`, `httpx`, `requests`, `urllib` (std lib) | Groq 0.9+, HTTPX 0.27+ | Production |
| **Testing** | `pytest`, `pytest-asyncio`, `anyio` | Pytest 9.1+, AnyIO 4.14+ | Development / CI |

---

## 3. Database & Persistence Subsystems
1. **Neon PostgreSQL (Cloud Serverless):**
   * Configured via `DATABASE_URL` in `.env`
   * Tables: `businesses`, `assessments`, `activity_logs`, `users`
   * Persistence verified in `tests/test_neon_persistence.py`
2. **Local SQLite Databases (On-disk embedded):**
   * `backend/app/data/locality_master.sqlite3`: Gazetteer storing administrative localities, villages, mandals, and verified coordinates.
   * `backend/app/data/translation_cache.sqlite3`: 6-language multi-dialect translation cache.
   * `backend/app/data/udyam_saathi.sqlite3`: Local development / offline business status fallback.

---

## 4. API Endpoints Inventory
| Router Prefix | Method | Endpoint | Description | Phase/Doc |
|---|---|---|---|---|
| `/api/v2/market-analysis` | `POST` | `/` | Document 1 UDYAM village analysis & competitor retrieval | Doc 1 |
| `/api/v2/market-analysis` | `GET` | `/categories` | Supported business category ontology | Doc 1 |
| `/api/v2/market-analysis` | `GET` | `/health` | UDYAM API connectivity, cache status, gazetteer counts | Doc 1 |
| `/api/v2/market-analysis` | `POST` | `/opportunity` | Full Document 2 opportunity assessment report | Doc 2 |
| `/api/v2/market-analysis` | `POST` | `/compare` | Multi-category side-by-side comparative ranking | Doc 2 |
| `/api/v2/market-analysis` | `GET` | `/intents` | Predefined canonical business intents | Doc 2 |
| `/api/v2/market-analysis` | `GET` | `/sources` | Government data sources registry & lineage metadata | Doc 2 |
| `/api/v1/feasibility` | `POST` | `/generate-report` | Comprehensive 8-dimension DPR credit assessment | Legacy |
| `/api/v1/feasibility` | `POST` | `/ml-viability` | XGBoost + TreeSHAP 10-feature financial viability | Legacy |
| `/api/v1/business` | `GET/POST` | `/...` | Business lifecycle & draft persistence | Legacy |
| `/api/v1/chat` | `POST` | `/` | Conversational loan officer chatbot with Groq LLM | Legacy |
| `/api/v1/translate` | `POST` | `/` | Vernacular language translation service | Legacy |

---

## 5. Architectural Module Responsibility Matrix
| Module | Responsibility | Inputs | Outputs | Test Suite | Dependencies | Audit Status |
|---|---|---|---|---|---|---|
| `app.core.udyam.client` | Ingests live UDYAM records via OGD API with 429 backoff & fallback | State, District, Pincode, API Key | Raw records JSON | `test_udyam_engine.py` | `urllib`, `data.gov.in` | PASS |
| `app.core.udyam.normalization` | Text tokenization, uppercase normalization, address parsing | Raw address strings | Normalized tokens | `test_udyam_engine.py` | stdlib `re`, `unicodedata` | PASS |
| `app.core.udyam.geography.gazetteer` | SQLite locality master for verified village coordinates | Village, District, State | Verified Lat/Lon, Confidence | `test_udyam_engine.py` | `sqlite3` | PASS |
| `app.core.udyam.geography.distance` | Spherical Haversine distance & market zone tagging | Point A, Point B, Radii | Distance km, MarketZone | `test_udyam_engine.py` | `math` | PASS |
| `app.core.udyam.pipeline` | Orchestrates Doc 1 village MSME retrieval and competitor zone assignment | Location, Category, Radius | `VillageMarketIntelligenceResult` | `test_udyam_api_and_pipeline.py` | Pipeline components | PASS |
| `app.core.intelligence.intents` | Resolves user intent to canonical categories, NIC codes, synonyms | Freeform string / intent code | `BusinessIntent` | `test_opportunity_engine.py` | None | PASS |
| `app.core.intelligence.relevance` | Deterministic 5-class competitor relevance classifier | Business dict, BusinessIntent | `CompetitorRecord` | `test_opportunity_engine.py` | None | PASS |
| `app.core.intelligence.supply` | Calculates distance distribution, nearby counts, and Diversification HHI | `CompetitorRecord` list | `SupplyMetrics` | `test_opportunity_engine.py` | `statistics`, `collections` | PASS |
| `app.core.adapters.population` | Census 2011 projection using state-specific official CAGRs | State, District, Village | Projected Pop, Households | `test_opportunity_engine.py` | `growth_rates.json` | PASS_WITH_LIMITATION |
| `app.core.adapters.amenities` | Mission Antyodaya 613 village amenities query & baseline fallback | State, District, Village | Power hrs, Road, Bank, Score | `test_opportunity_engine.py` | `district_resources.json` | PASS |
| `app.core.adapters.odop` | Statutory ODOP directory alignment and cluster incentive matching | State, District, Sector | ODOP Product, Alignment flag | `test_opportunity_engine.py` | `odop_registry.json` | PASS |
| `app.core.adapters.registry` | Central immutable catalog of government dataset lineage | None | `DatasetMetadata` dicts | `test_opportunity_engine.py` | None | PASS |
| `app.core.intelligence.opportunity` | 5 transparent indicators, composite score, and hard guardrails | `SupplyMetrics`, `DemandFeatures` | Indicators, Score, Verdict | `test_opportunity_engine.py` | None | PASS |
| `app.core.intelligence.explainability` | Generates evidence object, positive drivers, risks, limitations | Metrics, Score, Location | `EvidenceObject` | `test_opportunity_engine.py` | None | PASS |
| `app.core.intelligence.scenarios` | Multi-radius sweeps and unmapped uncertainty stress testing | Records, Demand, Intent | `list[SensitivityScenario]` | `test_opportunity_engine.py` | None | PASS |
| `app.core.intelligence.engine` | Master orchestrator coordinating supply, demand, and comparisons | Location, Intent, Radius | `MarketOpportunityReport` | `test_opportunity_engine.py` | Engine subsystems | PASS |

---

## 6. Audit Conclusion for Gate 1
* All 16 key components are present on disk, actively tested, and integrated.
* No phantom or pseudo-implemented components exist in the Document 1/2 stack.
* Gate 1 Result: **PASS**
