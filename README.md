# 🇮🇳 Udyam Saathi (उद्यम साथी)
### *AI-Powered Micro & Small Enterprise Feasibility, Credit Appraisal & Statutory Bank DPR Engine*
**Smart India Hackathon (SIH 2026) • Ministry of Micro, Small & Medium Enterprises (MoMSME)**

---

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon%20Async-4169E1.svg?logo=postgresql&logoColor=white)](https://neon.tech/)
[![Firebase](https://img.shields.io/badge/Auth-Firebase%20%2B%20OAuth-FFA611.svg?logo=firebase&logoColor=white)](https://firebase.google.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-10--D%20Viability-EB5424.svg?logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/Explainability-Lundberg%20TreeSHAP-brightgreen.svg)](https://shap.readthedocs.io/)
[![Groq Cloud](https://img.shields.io/badge/Groq%20Cloud-LLM%20%26%20Whisper-F05A28.svg?logo=meta&logoColor=white)](https://groq.com/)
[![Schemes](https://img.shields.io/badge/Government%20Schemes-17%20Integrated-8B5CF6.svg)](https://www.jansamarth.in/)
[![Languages](https://img.shields.io/badge/Languages-6%20Indian%20Languages-10B981.svg)](https://cloud.google.com/translate)
[![Tests](https://img.shields.io/badge/Platform%20Tests-325%2F325%20Passed%20(100%25)-10B981.svg)](https://github.com/)

---

## 📌 Executive Summary

**Udyam Saathi (उद्यम साथी)** is an enterprise-grade AI credit appraisal, geographic feasibility, and statutory bank memorandum platform designed to democratize formal bank credit access for India's 63+ million micro and small entrepreneurs.

Unlike generic LLM wrappers that hallucinate financial metrics and lack institutional compliance, Udyam Saathi implements a **4-Tier Zero-Hallucination Architecture** that strictly separates deterministic banking math from narrative generation. It integrates ground-truth Census demographics (660,000+ villages), MSME registry density data (788 districts), live MoSPI inflation indices, 613 district resource amenities indicators from Data.gov.in, 17 Central & State credit-linked subsidy schemes, and a 10-dimensional supervised XGBoost model with **Lundberg TreeSHAP feature attributions** to generate **100% audit-compliant, bank-ready Detailed Project Reports (DPR)** in under 2 seconds.

---

## 🏛️ 4-Tier Zero-Hallucination Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              TIER 1: DETERMINISTIC MATH & LGD                          │
│  • Census 2011 Catchment Demographics (census_raw) + State CAGR Forward Projections    │
│  • Sector Demand TAM Estimation (Penetration × Frequency × Ticket Size)                │
│  • RBI Working Capital Outlay (Nayak Committee / Tandon Turnover Method)               │
│  • 17 Statutory Schemes Ranking: PMEGP, PMFME, MUDRA, Stand-Up India, NSFDC, etc.     │
│  • Amortization Schedule with Moratorium + Debt Service Coverage Ratio (DSCR)          │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                  TIER 2: MACHINE LEARNING VIABILITY & TREESHAP EXPLAINABILITY          │
│  • 613 District Resource Village Amenities API (Power, Road, Bank, Internet, Storage)  │
│  • 10-Dimensional Normalized Feature Vector (x0 ... x9)                                │
│  • Supervised XGBoost Multi-Class Classifier (SUITABLE / CAUTION / RECONSIDER)         │
│  • Lundberg TreeSHAP Exact Game-Theoretic Marginal Factor Attributions                 │
│  • 8-Point Quantified Risk Engine + Grounded Rupee Mitigation Buffers                  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               TIER 3: MULTI-LINGUAL AI SYNTHESIS & VOICE TELEMETRY                     │
│  • Groq Cloud LLaMA 3.3 70B Versatile Single-Call Executive Synthesis                   │
│  • Groq Whisper v3 High-Speed Multilingual Speech-to-Text (< 400ms)                    │
│  • gTTS Audio Synthesis for regional audio responses                                   │
│  • 6 Languages Supported: English, Hindi, Marathi, Tamil, Telugu, Kannada              │
│  • Zero Financial Recalculation Invariant (LLM is strictly forbidden from editing math)│
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TIER 4: STATUTORY 7-SECTION BANK DPR                            │
│  • Section 1: Executive Summary, Promoter Action Plan & Credit Officer Appraisal Notes  │
│  • Section 2: Itemized Capital Outlay & Means of Finance (100% Sourced Balance Check)  │
│  • Section 3: 5-Year Financial Horizon (60% -> 90% Capacity, EBITDA, WDV Depr, DSCR)   │
│  • Section 4: 17-Government Scheme Subsidy Matrix & Cost Comparison                    │
│  • Section 5: ML Viability Appraisal & Lundberg TreeSHAP Waterfall Chart               │
│  • Section 6: Grounded 4-Quadrant SWOT & 8-Point Risk Mitigation Table with ₹ Buffers  │
│  • Section 7: Statutory Bank Submission Document Checklist & Compliance Matrix         │
│  • Official Sign-Off: Promoter Truth Declaration & Bank Branch Endorsement Block       │
│  • Multi-Format Export: Printable Formatted HTML, Markdown Memo, JSON                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Platform Features

* **⚡ Sub-2-Second End-to-End Execution**: Calculates population projections, working capital buffers, debt service coverage, amenities scoring, XGBoost classification, TreeSHAP explainability, and compiles the complete 7-section DPR in $< 2\text{s}$.
* **🎙️ Multilingual Voice & AI Chat Assistant**: Speak naturally in **Hindi, Marathi, Tamil, Telugu, Kannada, or English** via the dashboard voice chatbot. Audio is transcribed via Groq Whisper v3 and answered via Groq LLaMA 3.3 70B with synchronized regional audio output.
* **🌐 Mother-Tongue DPR Translation**: Full statutory Detailed Project Reports can be instantly translated, viewed, and printed in 6 native languages while preserving table alignments, currency symbols, and official banking formatting.
* **🤖 Lundberg TreeSHAP Explainability**: Replaces heuristic rules with exact mathematical game-theoretic Shapley values calculated by `shap.TreeExplainer` over 10 dimensions.
* **🏛️ 17 Central & State Schemes Integrated**: Evaluates eligibility and ranks programs across PMEGP, PMFME, MUDRA (Shishu/Kishore/Tarun/Tarun Plus), Stand-Up India, PM Vishwakarma, DAY-NRLM, AHIDF, CGTMSE, Margin Money Scheme, CLCSS, PM-EGMS, NSFDC, NBCFDC, NHFDC, and NMDFC.
* **🔐 Production Security & IDOR Protection**: Firebase Authentication + Neon PostgreSQL with strict row-level ownership checks (`user_id == current_user.uid`) preventing unauthorized cross-tenant data access.
* **📊 Dual Multi-Business Management**: Manage multiple enterprises, track appraisal statuses (Draft, In Analysis, Bank Ready, Flagged Risk), and isolate scenario histories.

---

## 📁 Repository Directory Structure

```
SIH2026/
├── backend/
│   ├── app/
│   │   ├── core/                    # Deterministic financial math, ML inference & AI
│   │   │   ├── amenities_client.py   # Data.gov.in 613 village amenities client
│   │   │   ├── audio_chat_service.py # Groq Whisper + gTTS Multilingual Voice Service
│   │   │   ├── auth_dependency.py    # Firebase Bearer token verification & IDOR guard
│   │   │   ├── chat_service.py       # Contextual RAG Chatbot engine
│   │   │   ├── dpr_generator.py      # Statutory 7-Section Bank DPR compiler & HTML renderer
│   │   │   ├── executive_synthesizer.py # Single-call LLM narrative synthesizer
│   │   │   ├── feature_extractor.py  # 10-D Feature Vector extractor (x0..x9)
│   │   │   ├── financial_calculator.py# EMI, amortization, DSCR & 17-scheme ranker
│   │   │   ├── inference.py          # XGBoost classifier & Lundberg TreeSHAP explainer
│   │   │   ├── market_analyzer.py    # Census CAGR population & TAM engine
│   │   │   ├── pricing_engine.py     # CPI inflation floor & pricing recommendations
│   │   │   ├── risk_analyzer.py      # 8-Point quantified risk matrix & rupee buffers
│   │   │   ├── swot_analyzer.py      # Grounded 4-quadrant SWOT matrix
│   │   │   └── translation_service.py# Google Cloud Translation & regional dictionary
│   │   ├── data/                    # Ground-truth JSONs, models & SQLite persistence
│   │   │   ├── district_resources.json
│   │   │   ├── government_schemes.json # 17 statutory schemes
│   │   │   ├── growth_rates.json
│   │   │   ├── model_metadata.json
│   │   │   └── viability_xgb.joblib  # Trained supervised XGBoost model
│   │   ├── models/                  # Pydantic request & response schemas
│   │   │   └── schemas.py
│   │   ├── routers/                 # REST API endpoints
│   │   │   ├── auth.py              # User registration, sessions & profile
│   │   │   ├── chat.py              # Text & Audio Chatbot API
│   │   │   ├── data_sources.py      # Open data catalogs & scheme endpoints
│   │   │   ├── feasibility.py       # 4-tier feasibility & DPR endpoints
│   │   │   ├── financial.py         # Standalone loan & DSCR calculator
│   │   │   ├── locations.py         # LGD 36 States/UTs, districts & blocks
│   │   │   ├── projects.py          # Authenticated project CRUD & analysis
│   │   │   └── translation.py       # Live text & batch translation API
│   │   ├── config.py                # Pydantic BaseSettings
│   │   ├── database.py              # Neon PostgreSQL async pool & SQLite fallback
│   │   └── main.py                  # FastAPI application factory & middleware
│   └── Dockerfile                   # Production Python 3.11 Slim container
├── frontend/
│   ├── src/
│   │   ├── components/              # Reusable UI components & modals
│   │   │   ├── AudioChatbotModal.jsx# Multilingual voice assistant modal
│   │   │   ├── ChatbotModal.jsx     # Contextual RAG chat modal
│   │   │   ├── DprModal.jsx         # Quick-view DPR modal with print/download
│   │   │   ├── TranslatedText.jsx   # Live reactive translation component
│   │   │   └── Wizard/              # 7-Step Enterprise Feasibility Wizard
│   │   ├── context/                 # React Context Providers
│   │   │   ├── AuthContext.jsx      # Firebase auth & profile state
│   │   │   ├── LanguageContext.jsx  # 6-Language translation state & cache
│   │   │   └── ProjectContext.jsx   # Multi-project selection & persistence
│   │   ├── pages/                   # Application route pages
│   │   │   ├── DashboardPage.jsx    # Unified dashboard & deep-dive modules
│   │   │   ├── FeasibilityPage.jsx  # 7-step wizard entry page
│   │   │   ├── LoginPage.jsx        # Email/password & Google OAuth login
│   │   │   ├── RegisterPage.jsx     # Entrepreneur onboarding
│   │   │   ├── report/              # 8 Dedicated dimension report pages
│   │   │   │   ├── BankDprPage.jsx  # Official DPR page with language selector
│   │   │   │   ├── FinancialsPage.jsx
│   │   │   │   ├── MarketPage.jsx
│   │   │   │   ├── OverviewPage.jsx
│   │   │   │   ├── RiskPage.jsx
│   │   │   │   ├── SchemesPage.jsx
│   │   │   │   ├── SwotPage.jsx
│   │   │   │   └── ViabilityPage.jsx
│   │   └── services/
│   │       ├── api.js               # Centralized Axios/fetch client
│   │       └── firebaseClient.js    # Firebase Client SDK initializer
│   ├── Dockerfile                   # Multi-stage Node 20 + Nginx Alpine
│   └── nginx.conf                   # High-performance SPA reverse proxy
├── notebooks/                       # Exploratory & validation Jupyter Notebooks
│   └── Audio_Chatbot_language_selector_edition.ipynb
├── tests/                           # Complete automated platform test harness
│   ├── test_audio_chat_service.py
│   ├── test_business_management.py
│   ├── test_chat_service.py
│   ├── test_modular_endpoints.py
│   ├── test_neon_persistence.py
│   ├── test_phase2.py
│   ├── test_phase3.py
│   ├── test_phase4.py
│   ├── test_phase5.py
│   ├── test_phase6.py
│   ├── test_phase7.py
│   └── test_translation_service.py
├── docs/                            # Implementation plans & system blueprints
├── docker-compose.yml               # Local & production multi-container setup
├── requirements.txt                 # Backend Python dependencies
├── run_tests.py                     # Master test suite runner (100% pass)
└── README.md
```

---

## 🏛️ 17 Integrated Government Schemes

Udyam Saathi mathematically benchmarks projects against 17 statutory Central & State MSME subsidy and credit programs:

| Scheme Code | Full Scheme Name | Administering Ministry / Nodal Agency | Max Project Cap | Subsidy / Credit Support |
|---|---|---|:---:|:---:|
| **PMEGP** | Prime Minister's Employment Generation Programme | Ministry of MSME / KVIC | ₹50 Lakhs | 15% – 35% Capital Grant |
| **PMFME** | PM Formalisation of Micro Food Processing Enterprises | Ministry of Food Processing (MoFPI) | ₹1 Crore | 35% Subsidy (Max ₹10 Lakhs) |
| **MUDRA Shishu** | Pradhan Mantri MUDRA Yojana (Shishu) | Department of Financial Services (DFS) | ₹50,000 | 100% Collateral-Free Debt |
| **MUDRA Kishore**| Pradhan Mantri MUDRA Yojana (Kishore) | Department of Financial Services (DFS) | ₹5 Lakhs | Collateral-Free Term Loan |
| **MUDRA Tarun** | Pradhan Mantri MUDRA Yojana (Tarun) | Department of Financial Services (DFS) | ₹10 Lakhs | Collateral-Free Working Capital |
| **MUDRA Tarun+**| Pradhan Mantri MUDRA Yojana (Tarun Plus) | Department of Financial Services (DFS) | ₹20 Lakhs | Enhanced Credit Line |
| **Stand-Up India**| Stand-Up India Scheme (SC / ST / Women) | SIDBI / DFS | ₹1 Crore | 15% Margin Money Support |
| **PM Vishwakarma**| PM Vishwakarma Kaushal Samman | Ministry of MSME | ₹3 Lakhs | 5% Subsidized Concessional Loan |
| **DAY-NRLM** | Deendayal Antyodaya Yojana (Women SHGs) | Ministry of Rural Development | ₹20 Lakhs | Interest Subvention down to 7% |
| **AHIDF** | Animal Husbandry Infrastructure Dev Fund | DAHD / NABARD | ₹50 Crores | 3% Interest Subvention + Credit Guarantee |
| **CGTMSE** | Credit Guarantee Fund Trust for Micro & Small Enterprises | SIDBI / Ministry of MSME | ₹5 Crores | Up to 85% Guarantee Coverage |
| **Margin Money** | State DIC Margin Money & Capital Subsidy Scheme | State Directorate of Industries | ₹25 Lakhs | 10% – 20% Equity Margin Grant |
| **CLCSS** | Credit Linked Capital Subsidy Scheme | Ministry of MSME | ₹1 Crore | 15% Upfront Capital Subsidy |
| **NSFDC** | National Scheduled Castes Finance & Dev Corp | Ministry of Social Justice & Empowerment | ₹50 Lakhs | Concessional 4% – 6% Lending |
| **NBCFDC** | National Backward Classes Finance & Dev Corp | Ministry of Social Justice & Empowerment | ₹15 Lakhs | Concessional 5% – 7% Lending |
| **NHFDC** | National Divyangjan Finance & Dev Corp | Ministry of Social Justice & Empowerment | ₹25 Lakhs | Concessional 4% – 5% Lending |
| **NMDFC** | National Minorities Development & Finance Corp | Ministry of Minority Affairs | ₹20 Lakhs | Concessional 5% – 6% Lending |

---

## 🐳 Quick Start with Docker

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed & running.
* Copy `.env.example` to `.env` and set your API keys:
```bash
cp .env.example .env
```

### Launch Complete Platform
```bash
docker-compose up --build
```

* **Frontend Dashboard**: [`http://localhost:3000`](http://localhost:3000)
* **Backend API & Swagger Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
* **Subsystem Health Telemetry**: [`http://localhost:8000/api/v2/health`](http://localhost:8000/api/v2/health)

---

## 💻 Local Development Setup

### 1. Backend (FastAPI + Python 3.11)
```bash
cd SIH2026

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch ASGI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend (React 18 + Vite)
```bash
cd frontend

# Install Node packages
npm install

# Start Vite dev server
npm run dev
```

---

## 🧪 Master Platform Test Suite

Udyam Saathi maintains a rigorous, zero-hallucination verification suite covering deterministic accounting balance, LGD demographic scaling, 17-scheme ranking, Lundberg TreeSHAP game-theoretic invariants, multi-lingual audio/text synthesis, and IDOR tenancy security:

```bash
# Run all 11 test suites (325/325 tests)
python run_tests.py
```

```
==========================================================================================
🏁 TEST EXECUTION SUMMARY:
==========================================================================================
Total Test Suites: 11
Suites Passed:     11 / 11 (100% Success Rate)
Suites Failed:     0
==========================================================================================
🎉 ALL 325 TESTS ACROSS ALL PHASES PASSED WITH 100% SUCCESS RATE!
```

---

## 👥 Contributors & Acknowledgements

* **Developed for Smart India Hackathon (SIH 2026)**
* **Problem Statement ID**: PS 26091 • AI Credit Appraisal & Feasibility System for MSMEs
* **Data Sources**: Census of India (2011), Ministry of MSME Udyam Portal, MoSPI Rural CPI Index, Open Government Data (data.gov.in) Mission Antyodaya OGD Platform.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
