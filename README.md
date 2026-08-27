# 🇮🇳 Udyam Saathi (उद्यम साथी)
### *AI-Powered Micro & Small Enterprise Feasibility, Credit Appraisal & Bank DPR Engine*
**Smart India Hackathon (SIH 2026) • Ministry of Micro, Small & Medium Enterprises (MoMSME)**

---

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon%20Async-4169E1.svg?logo=postgresql&logoColor=white)](https://neon.tech/)
[![XGBoost](https://img.shields.io/badge/XGBoost-10--Dimensional%20Viability-EB5424.svg?logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![Groq Llama-3-70B](https://img.shields.io/badge/Groq%20Cloud-Llama--3--70B-F05A28.svg?logo=meta&logoColor=white)](https://groq.com/)
[![Tests](https://img.shields.io/badge/Platform%20Tests-332%2F332%20Passed%20(100%25)-10B981.svg)](https://github.com/)

---

## 📌 Executive Summary

**Udyam Saathi (उद्यम साथी)** is an enterprise-grade AI credit appraisal, geographic feasibility, and bank memorandum platform designed to democratize formal bank lending for India's 63+ million micro and small entrepreneurs. 

Unlike generic LLM wrappers that fabricate financial forecasts, Udyam Saathi implements a **4-Tier Hybrid Pipeline** that strictly separates deterministic banking math from narrative generation. It connects ground-truth Census demographics (660k+ villages), MSME registry data (788 districts), live MoSPI inflation indices, 613 district village amenities indicators from Data.gov.in, and a 10-dimensional supervised XGBoost model to generate **100% audit-compliant, bank-ready Detailed Project Reports (DPR)** in under 2 seconds.

---

## 🏛️ 4-Tier Zero-Hallucination Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              TIER 1: DETERMINISTIC MATH & LGD                          │
│  • Census 2011 Catchment Demographics (census_raw) + State CAGR Forward Projections    │
│  • Sector Demand TAM Estimation (Penetration × Frequency × Ticket Size)                │
│  • RBI Working Capital Outlay (Nayak Committee / Tandon Turnover Method)               │
│  • Statutory Scheme Ranking: PMEGP, PMFME, MUDRA (Shishu/Kishore/Tarun), Stand-Up      │
│  • Amortization Schedule with Moratorium + Debt Service Coverage Ratio (DSCR)          │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       TIER 2: MACHINE LEARNING VIABILITY CLASSIFIER                    │
│  • 613 District Resource Village Amenities API (Power, Road, Bank, Internet, Storage)  │
│  • 10-Dimensional Normalized Feature Vector (x0 ... x9)                                │
│  • Supervised XGBoost Multi-Class Classifier (SUITABLE / CAUTION / RECONSIDER)         │
│  • 8-Point Quantified Risk Engine + Grounded Rupee Mitigation Buffers                  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      TIER 3: MULTI-LINGUAL AI EXECUTIVE SYNTHESIS                      │
│  • Groq Cloud Llama-3-70B Single-Call Narrative Generator                              │
│  • 6 Regional Languages Supported: English, Hindi, Marathi, Tamil, Telugu, Kannada     │
│  • Zero Financial Recalculation Invariant (LLM is forbidden from inventing numbers)   │
│  • SHA-256 Prompt Memory Caching (< 1ms instant replay)                                │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TIER 4: STATUTORY 7-SECTION BANK DPR                            │
│  • Section 1: Executive Summary & Enterprise Profile                                   │
│  • Section 2: Capital Outlay & Means of Finance Reconciliation                         │
│  • Section 3: 5-Year Financial & Cash Flow Projections (60% -> 90% Capacity Scaling)   │
│  • Section 4: Market Catchment & Demographic Feasibility (TAM Analysis)                │
│  • Section 5: Grounded SWOT Matrix                                                     │
│  • Section 6: 8-Point Quantified Risk Analysis with Contingency Rupee Buffers          │
│  • Section 7: Statutory Bank Submission Checklist (FSSAI, Udyam, Caste/SHG Docs)      │
│  • Multi-Format Export: JSON, Clean Markdown, Printable Formatted HTML                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

* **⚡ Sub-2-Second End-to-End Pipeline**: Executes demographic projection, financial amortization, 613 amenities parsing, ML viability classification, AI synthesis, and 7-section DPR generation in $< 2\text{s}$.
* **🌐 Live LGD 4-Tier Cascading Administrative Hierarchy**: Dynamically queries 36 Indian States/UTs, 785 Districts, 7,338 Development Blocks, and 698,950 Census Villages directly from PostgreSQL.
* **📊 10-Dimensional ML Viability Engine**: In-memory XGBoost model evaluated on 10 grounded indicators ($x_0$: DSCR, $x_1$: Subsidy Ratio, $x_2$: Loan-to-Income, $x_3$: Population, $x_4$: MSME Density, $x_5$: Infrastructure Score, $x_6$: CPI Inflation, $x_7$: Working Capital Buffer, $x_8$: Competition, $x_9$: Weather Risk).
* **🏛️ 613 District Resource Integration (Data.gov.in)**: Automatic mapping of 613 Mission Antyodaya OGD resource UUIDs with 24-hour TTL caching and regional baseline fallbacks.
* **🗣️ Multi-Lingual Regional Translation**: Executive narrative synthesis and credit memos in 6 Indian languages (`en`, `hi`, `mr`, `ta`, `te`, `kn`).
* **🖨️ Bank-Ready Printable DPR**: One-click official bank memorandum generation formatted for commercial bank loan officers (SBI, PNB, Canara Bank, NABARD).

---

## 📁 Repository Structure

```
SIH/
├── backend/                         # FastAPI Python Backend
│   ├── app/
│   │   ├── config.py                # Pydantic BaseSettings & Environment Loader
│   │   ├── database.py              # PostgreSQL / Neon Asyncpg Connection Pool & LGD Resolvers
│   │   ├── main.py                  # FastAPI Application Entrypoint & CORS Middleware
│   │   ├── core/                    # Core Analytical & Mathematical Engines
│   │   │   ├── amenities_client.py  # 613 District Village Amenities OGD API Client
│   │   │   ├── dpr_generator.py     # 7-Section Statutory Bank DPR Document Compiler
│   │   │   ├── executive_synthesizer.py # Groq Llama-3-70B Multi-Lingual AI Synthesis
│   │   │   ├── feature_extractor.py # 10-Dimensional ML Feature Vector Extractor (x0..x9)
│   │   │   ├── financial_calculator.py # EMI, Moratorium, DSCR, Working Capital & Schemes
│   │   │   ├── inference.py         # Thread-Safe XGBoost Viability Prediction Engine
│   │   │   ├── market_analyzer.py   # Census 2011 Catchment Population & TAM Estimator
│   │   │   ├── pricing_engine.py    # CPI-Adjusted Cost-Plus Pricing Floor Calculator
│   │   │   ├── risk_analyzer.py     # 8-Point Quantified Risk Matrix & Rupee Buffers
│   │   │   ├── swot_analyzer.py     # Grounded SWOT Generator
│   │   │   └── train_model.py       # XGBoost Synthetic Pipeline Training Script
│   │   ├── data/                    # Model Weights, Scheme Rules & LGD Lookup Tables
│   │   │   ├── district_resources.json # 613 District Resource UUID Map
│   │   │   ├── government_schemes.json # PMEGP, PMFME, MUDRA, Stand-Up Slabs
│   │   │   ├── growth_rates.json    # State CAGR Census Population Projections
│   │   │   ├── model_metadata.json  # XGBoost Hyperparameters & Feature Importances
│   │   │   └── viability_xgb.joblib # Serialized XGBoost Model Binary
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic v2 Request/Response Schemas
│   │   └── routers/
│   │       ├── feasibility.py       # End-to-End Feasibility & DPR Endpoints
│   │       ├── financial.py         # Standalone Financial & Loan Calculators
│   │       ├── locations.py         # LGD 4-Tier Location Hierarchy Endpoints
│   │       └── projects.py          # Project State Persistence & JSONB Storage
├── frontend/                        # Vanilla ES6 Modern SPA Web Application
│   ├── index.html                   # Master Single-Page Mount
│   ├── package.json                 # Frontend Manifest & Scripts
│   └── src/
│       ├── api.js                   # REST API Client with Offline Fallbacks
│       ├── app.js                   # Main State Machine & SPA Router
│       ├── case_data.js             # 5 SIH Jury Defense Pitch Case Studies
│       ├── index.css                # Custom CSS Design System (Glassmorphism & Gradients)
│       └── components/
│           ├── CapitalReconciliation.js # Capital Outlay vs Means of Finance Card
│           ├── CaseStudiesBar.js    # 1-Click Pitch Preset Case Switcher
│           ├── Dashboard.js         # Master Analytics Dashboard Container
│           ├── DprViewerModal.js    # Printable 7-Section Bank DPR Modal
│           ├── FinancialProjections.js # 5-Year Cash Flow & Capacity Schedule Table
│           ├── Header.js            # Global Navigation & Live System Status Badge
│           ├── QuickCalculator.js   # Instant DSCR & Loan Repayment Tool
│           ├── RiskRadar.js         # 8-Point Quantified Risk Matrix Card
│           ├── SchemeLeaderboard.js # Eligible Govt Schemes Sorter
│           ├── StatutoryChecklist.js# Mandatory Bank Submission Docs Checklist
│           ├── SwotGrid.js          # Grounded SWOT Analysis Matrix
│           ├── ViabilityMeter.js    # Supervised ML Viability Gauge & Class Probabilities
│           └── Wizard.js            # 6-Step Enterprise Onboarding Form
├── docs/                            # Comprehensive Documentation & Architecture Specs
│   ├── udyam_saathi_master_blueprint.md
│   ├── master_implementation_plan.md
│   └── system_architecture_and_data_flow.md
├── tests/                           # Master Automated Regression Test Suites
│   ├── test_phase2.py               # Deterministic Financial & Demographic Math (57 Tests)
│   ├── test_phase3.py               # XGBoost Inference & 10-D Feature Extractor (45 Tests)
│   ├── test_phase4.py               # Unified AI Synthesis & Multi-Lingual Fallback (68 Tests)
│   ├── test_phase5.py               # 7-Section Bank DPR Accounting Balancing (38 Tests)
│   ├── test_phase6.py               # FastAPI REST API & Neon DB Integration (74 Tests)
│   └── test_phase7.py               # Modern Web Frontend Components & CSS System (50 Tests)
├── .env.example                     # Environment Configuration Template
├── .gitignore                       # Git Ignore Configuration
├── district_resources.json          # 613 District Resource UUID Map (Root Reference)
├── requirements.txt                 # Python Backend & ML Package Dependencies
├── run_tests.py                     # Master Test Suite Runner (325 Tests)
├── start_backend.bat                # Windows 1-Click Backend Launcher
└── start_frontend.bat               # Windows 1-Click Frontend Launcher
```

---

## ⚙️ Quick Start & Installation

### 1. Prerequisites
* **Python 3.10+**
* **Node.js 18+ & npm**
* **PostgreSQL Database** (Neon Serverless PostgreSQL recommended)

### 2. Environment Setup
Clone the repository and create your `.env` configuration:

```bash
# Copy template
cp .env.example .env
```

Edit `.env` with your API keys:
```ini
PORT=8000
HOST=0.0.0.0
DEBUG=True

# Neon Serverless PostgreSQL Database Connection String
DATABASE_URL=postgresql://neondb_owner:npg_DexJQiYjb9G8@ep-spring-cell-az3gxhjg-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Groq Cloud API Key for Llama-3-70B Multi-Lingual Executive Synthesis
GROQ_API_KEY=gsk_your_groq_api_key_here

# Open Government Data (data.gov.in) 613 Village Amenities API Key
DATA_GOV_IN_API_KEY=579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b
AMENITIES_API_BASE_URL=https://api.data.gov.in/resource
```

### 3. Install Dependencies

**Backend Dependencies:**
```bash
pip install -r requirements.txt
```

**Frontend Dependencies:**
```bash
cd frontend
npm install
cd ..
```

### 4. Running the Platform (Decoupled 2-Terminal Workflow)

The system runs as two independent services across dedicated terminal sessions:

#### Terminal 1 — Backend (FastAPI REST API & AI/ML Pipeline)
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*or double-click `start_backend.bat`*

* **REST API & Swagger Docs**: [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
* **System Health Check**: [`http://127.0.0.1:8000/api/v2/health`](http://127.0.0.1:8000/api/v2/health)

#### Terminal 2 — Frontend (Modern React + Vite Single Page Application)
```bash
cd frontend
npm run dev
```
*or double-click `start_frontend.bat`*

* **Web Application UI**: [`http://127.0.0.1:3000`](http://127.0.0.1:3000)


---

## 🧪 Master Automated Test Suite

Udyam Saathi includes **332 automated tests** across all 6 development phases:

```bash
python run_tests.py
```

### Test Suite Output:
```
==========================================================================================
🧪 UDYAM SAATHI — MASTER PLATFORM VERIFICATION TEST RUNNER
==========================================================================================
▶️ Running test_phase2.py ... ✅ test_phase2.py PASSED (57 / 57)
▶️ Running test_phase3.py ... ✅ test_phase3.py PASSED (45 / 45)
▶️ Running test_phase4.py ... ✅ test_phase4.py PASSED (68 / 68)
▶️ Running test_phase5.py ... ✅ test_phase5.py PASSED (38 / 38)
▶️ Running test_phase6.py ... ✅ test_phase6.py PASSED (74 / 74)
▶️ Running test_phase7.py ... ✅ test_phase7.py PASSED (50 / 50)
==========================================================================================
🏁 TEST EXECUTION SUMMARY:
Total Test Suites: 6 / 6 PASSED
Suites Passed:     6 / 6 (100% Success Rate, 0 Failures)
Total Platform Checks: 332 Passed
==========================================================================================
```

---

## 📊 5 SIH 2026 Jury Defense Benchmark Cases

The platform includes 5 pre-configured benchmark case studies representing diverse Indian geographies and social slabs:

| Case ID | Enterprise Name | Sector | Location | Outlay / Revenue | Top Scheme | Verdict | 5-Yr Avg DSCR |
|---|---|---|---|---|---|:---:|:---:|
| **Case 1** | Joypur Fresh Dairy | Dairy Processing | Bankura, WB (Rural) | ₹9.0L / ₹9.5L | **PMEGP (₹2.25L)** | 🟢 `SUITABLE` (99.5%) | **2.26** |
| **Case 2** | Mobile Repair Hub | Electronics Repair | Ramanagara, KA (Urban) | ₹1.8L / ₹3.2L | **MUDRA Kishore** | 🟢 `SUITABLE` (98.9%) | **2.18** |
| **Case 3** | Mahila Designer Boutique | Apparel & Tailoring | Varanasi, UP (Urban) | ₹3.5L / ₹4.2L | **Stand-Up India (₹87k)** | 🟢 `SUITABLE` (97.4%) | **1.78** |
| **Case 4** | Overleveraged Agro Plant | Food Processing | Ujjain, MP (Rural) | ₹45.0L / ₹8.0L | **PMEGP (₹11.25L)** | 🔴 `RECONSIDER` (99.9%) | **0.29** |
| **Case 5** | Khurja Ceramic Pottery | Ceramic Artisan | Bulandshahr, UP (Rural) | ₹2.8L / ₹3.4L | **PM Vishwakarma (₹98k)**| 🟡 `CAUTION` (98.6%) | **1.14** |

---

## 📡 REST API Reference

### 1. `POST /api/v2/feasibility/generate`
Generates a complete multi-tier feasibility report, ML viability classification, and bank credit memorandum.

#### Request Body Example:
```json
{
  "enterprise_name": "Joypur Fresh Dairy Processing",
  "business_category": "manufacturing",
  "sector": "dairy",
  "promoter_name": "Dipankar Ghosh",
  "promoter_category": "general",
  "gender": "Male",
  "state_name": "West Bengal",
  "district_name": "Bankura",
  "block_name": "Joypur",
  "village_name": "Joypur",
  "is_rural": true,
  "project_cost": 900000,
  "annual_turnover_estimate": 950000,
  "tenure_years": 7,
  "moratorium_months": 6,
  "language": "en"
}
```

### 2. `GET /api/v2/locations/states`
Returns all 36 Indian States and Union Territories from the LGD database.

### 3. `GET /api/v2/locations/districts?state_name=West%20Bengal`
Returns all districts for the target state.

### 4. `GET /api/v2/feasibility/{report_id}/dpr?format=html`
Exports the 7-Section Bank DPR document in `html`, `markdown`, or `json` formats.

---

## 👥 Contributors & Acknowledgements

* **Developed for Smart India Hackathon (SIH 2026)**
* **Problem Statement ID**: MoMSME AI Credit Appraisal & Feasibility System
* **Data Sources**: Census of India (2011), Ministry of MSME Udyam Portal, MoSPI Rural CPI Index, Open Government Data (data.gov.in) Mission Antyodaya OGD Platform.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
