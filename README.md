# 🇮🇳 Udyam Saathi (उद्यम साथी)
### *AI-Powered Micro & Small Enterprise Feasibility, Credit Appraisal & Bank DPR Engine*
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
[![Groq Cloud](https://img.shields.io/badge/Groq%20Cloud-LLM%20Synthesis-F05A28.svg?logo=meta&logoColor=white)](https://groq.com/)
[![Tests](https://img.shields.io/badge/Platform%20Tests-325%2F325%20Passed%20(100%25)-10B981.svg)](https://github.com/)

---

## 📌 Executive Summary

**Udyam Saathi (उद्यम साथी)** is an enterprise-grade AI credit appraisal, geographic feasibility, and statutory bank memorandum platform designed to democratize formal bank lending for India's 63+ million micro and small entrepreneurs.

Unlike generic LLM wrappers that fabricate financial forecasts, Udyam Saathi implements a **4-Tier Zero-Hallucination Architecture** that strictly separates deterministic banking math from narrative generation. It integrates ground-truth Census demographics (660k+ villages), MSME registry data (788 districts), live MoSPI inflation indices, 613 district village amenities indicators from Data.gov.in, and a 10-dimensional supervised XGBoost model with **Lundberg TreeSHAP feature attributions** to generate **100% audit-compliant, bank-ready Detailed Project Reports (DPR)** in under 2 seconds.

---

## 🏛️ 4-Tier Zero-Hallucination Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              TIER 1: DETERMINISTIC MATH & LGD                          │
│  • Census 2011 Catchment Demographics (census_raw) + State CAGR Forward Projections    │
│  • Sector Demand TAM Estimation (Penetration × Frequency × Ticket Size)                │
│  • RBI Working Capital Outlay (Nayak Committee / Tandon Turnover Method)               │
│  • Statutory Scheme Ranking: PMEGP, PMFME, MUDRA (Shishu/Kishore/Tarun), Stand-Up, etc.│
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
│                      TIER 3: MULTI-LINGUAL AI EXECUTIVE SYNTHESIS                      │
│  • Groq Cloud LLM Single-Call Narrative Generator                                      │
│  • 6 Regional Languages Supported: English, Hindi, Marathi, Tamil, Telugu, Kannada     │
│  • Zero Financial Recalculation Invariant (LLM is strictly forbidden from hallucinations)│
│  • Supplementary Promoter Context sanitized & injected for narrative depth only        │
│  • SHA-256 Prompt Memory Caching (< 1ms instant replay)                                │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TIER 4: STATUTORY 7-SECTION BANK DPR                            │
│  • Section 1: Executive Summary & Enterprise Profile                                   │
│  • Section 2: Capital Outlay & Means of Finance Reconciliation (Zero Outlay Drift)    │
│  • Section 3: 5-Year Financial & Cash Flow Projections (60% -> 90% Capacity Scaling)   │
│  • Section 4: Market Catchment & Demographic Feasibility (TAM Analysis)                │
│  • Section 5: Grounded SWOT Matrix                                                     │
│  • Section 6: 8-Point Quantified Risk Analysis with Contingency Rupee Buffers          │
│  • Section 7: Statutory Bank Submission Checklist (FSSAI, Udyam, Caste/SHG Docs)      │
│  • Multi-Format Export: Printable Formatted HTML, Markdown Memo, JSON                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication & IDOR-Protected Project State

Udyam Saathi features enterprise user authentication and data isolation:

1. **Firebase Authentication (Client-Side SDK)**:
   - Password hashing and Google OAuth token issuance are handled securely by Firebase Client SDK.
   - Raw passwords never reach the backend API.
2. **Server-Side Token Verification & IDOR Protection**:
   - Every protected route requires `Authorization: Bearer <Firebase ID Token>`.
   - The FastAPI dependency `get_current_user` verifies cryptographic signatures and extracts claims.
   - Strict project ownership validation: attempts to view or analyze another user's project return `HTTP 403 Forbidden`.
3. **Hybrid Neon PostgreSQL Schema**:
   - `users`: Keyed by `firebase_uid`, stores name, email, gender, phone, and optional narrative context.
   - `projects`: Foreign-keyed to `users.firebase_uid` with cascade deletion and indexed queries.

---

## 🚀 Key Features

* **⚡ Sub-2-Second End-to-End Pipeline**: Executes demographic projection, financial amortization, 613 amenities parsing, ML viability classification, TreeSHAP explainability, AI synthesis, and 7-section DPR generation in $< 2\text{s}$.
* **🧭 Sidebar Navigation & 8 Routed Deep-Dive Dimensions**: Clean information architecture partitioned across 8 dedicated routes:
  1. **Overview & Synthesis** (`/` or `/reports/:reportId`)
  2. **ML Viability & SHAP** (`/viability`)
  3. **Local Market Demand** (`/market`)
  4. **Government Schemes** (`/schemes`)
  5. **Financials & Cashflow** (`/financials`)
  6. **Risk Assessment** (`/risk`)
  7. **SWOT Matrix** (`/swot`)
  8. **Official Bank DPR** (`/dpr`)
* **🤖 Lundberg TreeSHAP Explainability**: Replaces heuristic rules with real mathematical game-theoretic Shapley values calculated by `shap.TreeExplainer`.
* **🇮🇳 Multilingual AI Synthesis**: Generates bank appraisals in 6 official languages: English (`en`), Hindi (`hi`), Marathi (`mr`), Tamil (`ta`), Telugu (`te`), and Kannada (`kn`).
* **🏛️ 10 Central & State Schemes Integrated**: PMEGP, PMFME, MUDRA (Shishu/Kishore/Tarun/Tarun Plus), Stand-Up India, PM Vishwakarma, DAY-NRLM, and AHIDF with direct `.gov.in` portal links.
* **📦 Docker Containerization**: Multi-stage Nginx + Python 3.11 Slim container images orchestrated via Docker Compose.

---

## 🐳 Quick Start with Docker

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed & running.
* Copy `.env.example` to `.env` and provide your Groq API key:
```bash
cp .env.example .env
```

### Launch Containers
```bash
docker-compose up --build
```

* **Frontend Dashboard**: [`http://localhost:3000`](http://localhost:3000)
* **Backend API & Swagger Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
* **Backend Health Telemetry**: [`http://localhost:8000/api/v2/health`](http://localhost:8000/api/v2/health)

---

## 💻 Local Development Setup

### 1. Backend Setup (FastAPI)
```bash
# Navigate to repository root
cd SIH2026

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server with live reload
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup (Vite + React)
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```

---

## 🏛️ Integrated Government Schemes Catalog

Udyam Saathi evaluates enterprise parameters against 10 Central & State MSME credit-linked subsidy schemes with direct official portal links:

| Scheme ID | Full Scheme Name | Administering Body | Verified Official Portal |
|---|---|---|---|
| **PMEGP** | Prime Minister's Employment Generation Programme | Ministry of MSME / KVIC | [`https://pmegp.msme.gov.in/`](https://pmegp.msme.gov.in/) |
| **PMFME** | PM Formalisation of Micro Food Processing Enterprises | Ministry of Food Processing (MoFPI) | [`https://pmfme.mofpi.gov.in/`](https://pmfme.mofpi.gov.in/) |
| **MUDRA Shishu** | Pradhan Mantri MUDRA Yojana (Up to ₹50,000) | Department of Financial Services (DFS) | [`https://www.jansamarth.in/`](https://www.jansamarth.in/) |
| **MUDRA Kishore**| Pradhan Mantri MUDRA Yojana (₹50,000 to ₹5 Lakhs) | Department of Financial Services (DFS) | [`https://www.jansamarth.in/`](https://www.jansamarth.in/) |
| **MUDRA Tarun**  | Pradhan Mantri MUDRA Yojana (₹5 Lakhs to ₹10 Lakhs)| Department of Financial Services (DFS) | [`https://www.jansamarth.in/`](https://www.jansamarth.in/) |
| **MUDRA Tarun Plus**| Pradhan Mantri MUDRA Yojana (₹10 Lakhs to ₹20 Lakhs)| Department of Financial Services (DFS) | [`https://www.jansamarth.in/`](https://www.jansamarth.in/) |
| **Stand-Up India**| Stand-Up India Scheme for SC/ST and Women | SIDBI / DFS | [`https://www.standupmitra.in/`](https://www.standupmitra.in/) |
| **PM Vishwakarma**| PM Vishwakarma Kaushal Samman Yojana | Ministry of MSME | [`https://pmvishwakarma.gov.in/`](https://pmvishwakarma.gov.in/) |
| **DAY-NRLM** | Deendayal Antyodaya Yojana - National Rural Livelihoods | Ministry of Rural Development | [`https://nrlm.gov.in/`](https://nrlm.gov.in/) |
| **AHIDF** | Animal Husbandry Infrastructure Development Fund | DAHD / NABARD | [`https://ahidf.udyamimitra.in/`](https://ahidf.udyamimitra.in/) |

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

| Endpoint | Method | Auth | Description |
|---|:---:|:---:|---|
| `/api/v2/health` | `GET` | Public | Subsystem health telemetry (Database, XGBoost model, OGD API, Groq LLM). |
| `/api/v2/auth/register` | `POST` | Bearer | Create or update user profile row after Firebase client account creation. |
| `/api/v2/auth/session` | `POST` | Bearer | Sync session on login; updates `last_login_at` and creates profile if needed. |
| `/api/v2/auth/me` | `GET` | Bearer | Retrieve caller's profile and count of associated projects. |
| `/api/v2/auth/me` | `PATCH` | Bearer | Update profile fields (`name`, `gender`, `phone`, `additional_business_details`). |
| `/api/v2/auth/me` | `DELETE` | Bearer | Delete Postgres profile, cascade delete projects, and remove Firebase user. |
| `/api/v2/projects` | `POST` | Bearer | Create draft project record belonging to authenticated user. |
| `/api/v2/projects` | `GET` | Bearer | List projects owned by authenticated user. |
| `/api/v2/projects/{id}` | `GET` | Bearer | Retrieve project details with strict ownership verification (403 IDOR protected). |
| `/api/v2/projects/{id}/analyze` | `POST` | Bearer | Run feasibility analysis for project and persist full JSONB results. |
| `/api/v2/projects/{id}/dpr` | `GET` | Bearer | Retrieve project 7-section Bank DPR in `html`, `markdown`, or `json`. |
| `/api/v2/feasibility/generate` | `POST` | Public / Bearer | Complete 4-tier feasibility appraisal, TreeSHAP attributions, and credit memo. |
| `/api/v2/feasibility/{report_id}` | `GET` | Public | Retrieve stored feasibility report by unique report ID. |
| `/api/v2/financial/calculate` | `POST` | Public | Standalone deterministic loan amortization, DSCR, and working capital calculator. |
| `/api/v2/locations/states` | `GET` | Public | List all 36 Indian States and Union Territories from LGD database. |
| `/api/v2/locations/districts` | `GET` | Public | Query districts for a selected state (`?state_name=...`). |
| `/api/v2/locations/blocks` | `GET` | Public | Query development blocks for a selected district (`?district_name=...`). |
| `/api/v2/data-sources` | `GET` | Public | Ground-truth database lineage metadata and connected table schemas. |
| `/api/v2/data-sources/schemes` | `GET` | Public | Master catalog of 10 Central & State subsidy schemes with official URLs. |
| `/api/v2/data-sources/stats` | `GET` | Public | System record counts across Census, MSME registry, and Amenities tables. |

---

## 🧪 Master Automated Test Suite

Udyam Saathi includes comprehensive automated tests covering all mathematical, ML, LLM, API, authentication, and IDOR invariants:

```bash
# Run full regression test harness
python run_tests.py

# Run modular endpoint test suite
python test_modular_endpoints.py
```

---

## 👥 Contributors & Acknowledgements

* **Developed for Smart India Hackathon (SIH 2026)**
* **Problem Statement ID**: PS 26091 • AI Credit Appraisal & Feasibility System for MSMEs
* **Data Sources**: Census of India (2011), Ministry of MSME Udyam Portal, MoSPI Rural CPI Index, Open Government Data (data.gov.in) Mission Antyodaya OGD Platform.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
