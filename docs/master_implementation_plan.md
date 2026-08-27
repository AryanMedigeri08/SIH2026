# 🚀 UDYAM SAATHI — Master Phased Implementation Plan

> **Objective**: A complete, rock-solid, 100% buildable, end-to-end implementation roadmap for **Udyam Saathi (SIH 2026 PS 26091)**.

---

## Phase Breakdown Matrix

| Phase | Core Focus Area | Tech Stack | Key Deliverables | Verification Milestone |
| :---: | :--- | :--- | :--- | :--- |
| **Phase 1** | **Database & Spatial Foundation** | PostgreSQL, PostGIS, asyncpg | LGD Tables (6-tier), Census 2011, MSME, CPI, IMD Weather, Amenities Cache | Location hierarchy resolves village down to pin-point Census metrics in <50ms |
| **Phase 2** | **Deterministic Financial & Scheme Core** | Python 3.10, pure math, JSON | Multi-scheme ranking (10+ schemes), EMI + Moratorium amortization, DSCR, 8-Point Risk, Grounded SWOT, CPI Pricing | 100% deterministic outputs with ₹ numbers; 0 LLM dependencies |
| **Phase 3** | **Flagship ML Viability Engine** | XGBoost, scikit-learn, joblib, numpy | 10-D Feature Extractor, XGBoost 3-Class Classifier, `viability_xgb.joblib`, Feature Gain Ranking | 98.9%+ Stratified CV Accuracy; real-time inference in <5ms |
| **Phase 4** | **Unified AI Synthesis & Multi-Language** | Groq API (Llama 3.3 70B), SHA-256 Cache | Single-call synthesis prompt, 1-Hour TTL in-memory cache, 100% deterministic offline fallback, 6 languages | Instant <1ms cached response; zero rate-limit stalls; multi-lingual output |
| **Phase 5** | **Bank-Ready DPR Generator** | Pydantic v2, ReportLab / HTML-to-PDF | 7-Section Official Bank Appraisal Report (Means of Finance, Capital Outlay, DSCR, Checklist) | Complete bank DPR payload matching PMEGP/PMFME/MUDRA bank formats |
| **Phase 6** | **FastAPI REST Backend & Persistence** | FastAPI, Neon PostgreSQL, Firebase Auth | `/api/v2/feasibility/*`, `/api/v2/projects/*`, `/api/v2/locations/*` | Clean REST API with JSONB analysis persistence and user project isolation |
| **Phase 7** | **Next.js Modern Frontend Application** | Next.js 15, Tailwind CSS, Framer Motion, Lucide | 6-Step Feasibility Wizard, Interactive Analytics Dashboard, Recharts, Leaflet Map, 1-Click PDF Export | Flawless, responsive, wow-factor UI with real-time updates and i18n support |
| **Phase 8** | **Full System Audit & Pitch Defense** | Pytest, End-to-End Test Harness | Automated test suite, presentation slide deck script, live jury demo checklist | 100% test pass rate; foolproof pitch defense against jury questions |

---

## Detailed Phase Execution Roadmap

### 📦 Phase 1: Database & Spatial Data Pipeline
- **Step 1.1**: Connect to Neon PostgreSQL instance with PostGIS extension enabled.
- **Step 1.2**: Verify and index LGD administrative hierarchy tables:
  - `states`, `districts`, `subdistricts`, `blocks`, `villages`
- **Step 1.3**: Verify and optimize data source tables:
  - `census_raw`: Indexed on `matched_village_code`
  - `msme_district`: Indexed on `lg_dt_code`
  - `cpi_data`: State and sector indexed for rapid monthly inflation lookups
  - `imd_weather_cache`: District-level daily rainfall and risk flags
  - `village_amenities_cache`: Binary flags for roads, weekly haats, power, banks, PDS
- **Step 1.4**: Implement `location_resolver.py` with in-memory caching for state/district lookups (<10ms latency).

---

### 🧮 Phase 2: Deterministic Financial, Scheme & Risk Core
- **Step 2.1**: Implement `government_schemes.json` registry with complete parameterization:
  - PMEGP (15–35% subsidy, ₹50L mfg / ₹20L svc limit)
  - PMFME (35% subsidy up to ₹10L for food processing)
  - MUDRA Shishu (₹50k), Kishore (₹5L), Tarun (₹10L), Tarun Plus (₹20L)
  - Stand-Up India (85% composite loan for SC/ST/Women)
  - PM Vishwakarma (5% fixed interest for 18 artisan trades)
  - DAY-NRLM (4%–7% subvention for Women SHGs)
  - NABARD AHIDF (3% subvention for dairy & livestock)
- **Step 2.2**: Implement `financial_calculator.py`:
  - Formulaic EMI amortization with moratorium support
  - Working capital estimation based on sector turnover ratios
  - Debt Service Coverage Ratio (DSCR) computation
  - `rank_eligible_schemes()` calculating Net Financial Benefit ($Subsidy - Total\_Interest$)
- **Step 2.3**: Implement `market_analyzer.py`:
  - Population forward projection formula ($P_{2011} \times (1+r)^{15}$)
  - Household conversion & monthly TAM calculation step-by-step
  - District MSME enterprise density and trade catchment competitors
- **Step 2.4**: Implement `swot_analyzer.py` and `risk_analyzer.py`:
  - Grounded SWOT matrix with exact rupee values and data source tags
  - 8-point quantitative risk engine with concrete operational mitigations
- **Step 2.5**: Implement `pricing_engine.py`:
  - Unit cost floor from cost stack (EMI + WC + Living) adjusted for CPI inflation

---

### 🤖 Phase 3: Flagship Supervised ML Viability Engine
- **Step 3.1**: Implement `feature_extractor.py`:
  - Extracts 10-D normalized feature vector ($x_0 \dots x_9$) with safe median defaults for missing values.
- **Step 3.2**: Implement `train_model.py`:
  - Generates empirical training samples from real PostgreSQL distributions.
  - Trains XGBoost multi-class classifier with 5-fold stratified cross-validation.
  - Logs feature gain importances and classification metrics.
  - Serializes `viability_xgb.joblib` and `model_metadata.json`.
- **Step 3.3**: Implement `inference.py`:
  - Thread-safe singleton model loader.
  - `predict_viability()` returning class probabilities (`suitable`, `caution`, `reconsider`) + confidence level.
  - Deterministic rule-based fallback when model artifact is offline.

---

### ⚡ Phase 4: Unified AI Synthesis & SHA-256 In-Memory Cache
- **Step 4.1**: Implement `executive_synthesizer.py`:
  - Consolidates all Tier 1 and Tier 2 outputs into **one single Groq synthesis prompt**.
  - Generates executive narrative, 4 strategic recommendations, and bank appraisal notes.
- **Step 4.2**: Implement SHA-256 In-Memory Cache:
  - Computes payload hash; identical requests return in **0.00ms** from memory.
- **Step 4.3**: Implement 100% Deterministic Grounded Narrative Fallback:
  - Zero crashes when offline, unauthenticated, or rate-limited.
- **Step 4.4**: Implement multi-language localization (English, Hindi, Marathi, Tamil, Telugu, Kannada).

---

### 📄 Phase 5: Bank-Ready Detailed Project Report (DPR) & PDF Export
- **Step 5.1**: Implement `dpr_generator.py`:
  - Transforms `FeasibilityReport` into official 7-section banking document:
    1. Executive Profile & Location Identifiers
    2. Capital Outlay & Means of Finance Table
    3. Financial & Cash Flow Projections (Turnover, Profit, DSCR)
    4. Multi-Scheme Subsidy Optimization Matrix
    5. Machine Learning Viability & Feature Gain Assessment
    6. Grounded SWOT & 8-Point Risk Mitigation Table
    7. Statutory Bank Submission Document Checklist
- **Step 5.2**: Expose `/api/v2/feasibility/{report_id}/dpr` and `/api/v2/projects/{project_id}/dpr` endpoints.

---

### 🌐 Phase 6: REST API Gateway & Project State Persistence
- **Step 6.1**: Implement `projects.py` routes for project state management:
  - `POST /api/v2/projects` (Create project record)
  - `GET /api/v2/projects` (List user projects)
  - `GET /api/v2/projects/{project_id}` (Retrieve project & analysis)
  - `POST /api/v2/projects/{project_id}/analyze` (Execute pipeline & save JSONB to Neon)
- **Step 6.2**: Implement Pydantic v2 `mode="json"` serialization to guarantee seamless JSONB Postgres compatibility.

---

### 💻 Phase 7: Next.js Modern Frontend Application
- **Step 7.1**: Setup Next.js 15 App Router with Tailwind CSS, Framer Motion animations, and Lucide icons.
- **Step 7.2**: Build **6-Step Onboarding Feasibility Wizard**:
  - Step 1: Enterprise Profile & Category (Manufacturing vs Service)
  - Step 2: Location Selector (Cascading State -> District -> Block -> Village dropdowns)
  - Step 3: Promoter Category & Subsidy Eligibility (General, SC, ST, OBC, Women)
  - Step 4: Investment & Capital Outlay
  - Step 5: Loan Tenure & Interest Preferences
  - Step 6: Preferred Language Selection (EN, HI, MR, TA, TE, KN)
- **Step 7.3**: Build **Interactive Feasibility Dashboard**:
  - Top Metric Cards (Viability Score, Subsidy Grant, Monthly EMI, DSCR)
  - Interactive Amortization & Repayment Chart (Recharts)
  - Scheme Comparison Leaderboard with 1-click apply links
  - Geographic Catchment Map (Leaflet / Google Maps)
  - 8-Point Risk Radar / Matrix with Expandable Mitigation Steps
  - Grounded SWOT Quadrant Matrix
- **Step 7.4**: Build **1-Click Bank DPR Export & Print Modal**:
  - Formatted printable view with official Government / Bank headers.

---

### 🏆 Phase 8: Full End-to-End Verification & SIH Pitch Validation
- **Step 8.1**: Run automated test suite across all 8 phases.
- **Step 8.2**: Validate against 5 real-world pitch case studies:
  1. *Dairy Processing in Joypur, Bankura (WB)* -> PMEGP/PMFME Subsidy, High DSCR, Suitable.
  2. *Mobile Repair Shop in Ramanagara (KA)* -> MUDRA Kishore, Low Risk, Suitable.
  3. *Women Tailoring Boutique in Varanasi (UP)* -> Stand-Up India / PMEGP, High Subsidy.
  4. *Overleveraged Agro Unit (₹25L outlay on ₹50k margin)* -> Reconsider, Low DSCR.
  5. *Artisan Pottery Cluster in Khurja (UP)* -> PM Vishwakarma / SFURTI, 5% Subvention.
