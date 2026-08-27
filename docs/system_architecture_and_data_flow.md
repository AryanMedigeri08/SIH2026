# 📐 System Architecture & Data Flow Specification

This document provides complete end-to-end technical diagrams, database entity models, and API contract specifications for the **Udyam Saathi** platform.

---

## 1. High-Level System Architecture Diagram

```mermaid
graph TB
    subgraph ClientLayer["Frontend Application (Next.js 15 App Router)"]
        UI_Home["Landing & Hero Page"]
        UI_Wizard["6-Step Enterprise Feasibility Wizard"]
        UI_Dash["Interactive Dashboard & Analytics"]
        UI_DPR["Bank DPR Viewer & PDF Exporter"]
        UI_Map["Leaflet / Google Maps Geographic View"]
        UI_Auth["Firebase Authentication Modal"]
    end

    subgraph APIGateway["FastAPI Backend Gateway (uvicorn :8000)"]
        Router_Auth["Auth Middleware & Firebase Token Verification"]
        Router_Location["/api/v2/locations (LGD Hierarchy)"]
        Router_Feasibility["/api/v2/feasibility (Analysis & DPR)"]
        Router_Projects["/api/v2/projects (Persistence)"]
        Router_Financial["/api/v2/financial (Standalone Calculators)"]
    end

    subgraph DeterministicTier["Tier 1: Deterministic Mathematical Core (< 25ms)"]
        Calc_Financial["Financial Calculator (EMI, Moratorium, Subsidy, DSCR)"]
        Calc_Scheme["Multi-Scheme Benefit Ranking (10+ Schemes)"]
        Calc_Market["Market Demand & TAM Estimator"]
        Calc_SWOT["Grounded SWOT Matrix Engine"]
        Calc_Risk["8-Point Quantified Risk & Mitigation Engine"]
        Calc_Pricing["CPI-Adjusted Pricing Engine"]
    end

    subgraph MLTier["Tier 2: Supervised Machine Learning Pipeline (< 10ms)"]
        FE["10-D Feature Extractor (feature_extractor.py)"]
        XGB["XGBoost Viability Classifier (viability_xgb.joblib)"]
        Explain["Class Probability & Gain Explainability Engine"]
    end

    subgraph SynthesisTier["Tier 3: Unified AI Synthesis & Caching (< 500ms)"]
        SHA["SHA-256 In-Memory Cache (1-Hour TTL)"]
        Groq["Groq API Client (Llama 3.3 70B Versatile)"]
        Fallback["100% Deterministic Offline Fallback Narrative"]
        LangMap["6-Language Localization Engine"]
    end

    subgraph DataStorage["PostgreSQL Database (Neon with PostGIS)"]
        DB_LGD["LGD Tables (states, districts, subdistricts, blocks, villages)"]
        DB_Census["census_raw (2011 Primary Census Abstract)"]
        DB_MSME["msme_district (Udyam Enterprise Registry)"]
        DB_CPI["cpi_data (MoSPI Rural Consumer Price Index)"]
        DB_Weather["imd_weather_cache (Live Rainfall & Alerts)"]
        DB_Amenities["village_amenities_cache (Data.gov.in Registry)"]
        DB_Projects["projects & users (Project State & Analysis JSONB)"]
    end

    %% Client to Gateway
    ClientLayer -->|REST / JSON| APIGateway

    %% Gateway to Services
    Router_Location --> DB_LGD
    Router_Feasibility --> DeterministicTier
    DeterministicTier --> MLTier
    MLTier --> SynthesisTier
    Router_Projects --> DB_Projects

    %% Deterministic to Database
    DeterministicTier --> DB_Census
    DeterministicTier --> DB_MSME
    DeterministicTier --> DB_CPI
    DeterministicTier --> DB_Weather
    DeterministicTier --> DB_Amenities

    %% Synthesis Connections
    SynthesisTier --> SHA
    SynthesisTier --> Groq
    SynthesisTier --> Fallback
```

---

## 2. End-to-End Execution Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Rural Entrepreneur
    participant FE as Next.js Frontend
    participant API as FastAPI Orchestrator
    participant LGD as Location Resolver (Postgres)
    participant Calc as Deterministic Financial & Scheme Engine
    participant DB as Pipeline Data (Census, MSME, CPI, Weather)
    participant ML as XGBoost ML Classifier (10-D)
    participant AI as Groq Synthesis (Llama 3.3 70B)
    participant DPR as Bank DPR Generator

    User->>FE: Enters Business Type, Investment (₹), Location & Category
    FE->>API: POST /api/v2/feasibility/generate (UserInput)
    
    API->>LGD: 1. Resolve LGD Location Hierarchy (async)
    LGD-->>API: Location Hierarchy (State, District, Block, Village)
    
    API->>Calc: 2. Run Financial Calculator & Multi-Scheme Optimizer
    Calc-->>API: Project Cost, EMI Schedule, DSCR, Top 5 Ranked Schemes
    
    API->>DB: 3. Fetch Pipeline Signals (Census 2011 + CAGR, MSME, CPI, IMD)
    DB-->>API: Demographics, Enterprise Counts, Inflation, Rainfall
    
    API->>Calc: 4. Compute Grounded SWOT, 8-Point Risk & Pricing Engine
    Calc-->>API: Quantified SWOT, Risk Mitigation Table, Price Brackets
    
    API->>ML: 5. Extract 10-D Feature Vector & Run XGBoost Predict
    ML-->>API: Viability Verdict [SUITABLE/CAUTION/RECONSIDER] + 99.0% Confidence
    
    API->>AI: 6. Check SHA-256 Cache -> Single Groq Call (if not cached)
    AI-->>API: Localized Executive Summary, 4 Recommendations, Bank Notes
    
    API->>DPR: 7. Format 7-Section Bank-Ready DPR Appraisal Package
    DPR-->>API: Complete DPR Structure
    
    API-->>FE: Assembled FeasibilityReport & Bank DPR JSON (< 1.5s)
    FE->>User: Displays Interactive Dashboard, Visual Charts & 1-Click PDF Download
```

---

## 3. Database Schema Models (Neon PostgreSQL)

```mermaid
erDiagram
    USERS ||--o{ PROJECTS : owns
    PROJECTS ||--o| FEASIBILITY_REPORTS : stores_jsonb
    
    STATES ||--o{ DISTRICTS : contains
    DISTRICTS ||--o{ BLOCKS : contains
    DISTRICTS ||--o{ SUBDISTRICTS : contains
    SUBDISTRICTS ||--o{ VILLAGES : contains
    
    VILLAGES ||--o| CENSUS_RAW : matches
    VILLAGES ||--o| VILLAGE_AMENITIES_CACHE : matches
    DISTRICTS ||--o{ MSME_DISTRICT : aggregates
    DISTRICTS ||--o{ IMD_WEATHER_CACHE : records
    STATES ||--o{ CPI_DATA : tracks

    USERS {
        string firebase_uid PK
        string email
        string name
        timestamp created_at
    }

    PROJECTS {
        string project_id PK
        string user_id FK
        string business_name
        string business_category
        float investment_amount
        string state_name
        string district_name
        string block_name
        string village_name
        jsonb analysis_result
        timestamp created_at
        timestamp updated_at
    }

    CENSUS_RAW {
        int matched_village_code PK
        int total_population
        int total_households
        int male_population
        int female_population
        int sc_population
        int st_population
        int literate_population
        int total_workers
    }

    MSME_DISTRICT {
        int lg_dt_code PK
        string state_name
        string district_name
        int micro
        int small
        int medium
        int total
    }

    CPI_DATA {
        string state
        string sector
        string division
        int year
        string month
        float index
        float inflation
    }

    IMD_WEATHER_CACHE {
        int district_code PK
        date date PK
        float rainfall_mm
        jsonb forecast_data
        timestamp fetched_at
    }
```

---

## 4. API Endpoints Contract (v2)

| Method | Endpoint | Description | Request Body / Params | Response Model |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v2/feasibility/generate` | Run full feasibility analysis | `UserInput` JSON | `FeasibilityReport` |
| **GET** | `/api/v2/feasibility/{report_id}` | Retrieve cached feasibility report | `report_id: str` | `FeasibilityReport` |
| **GET** | `/api/v2/feasibility/{report_id}/dpr` | Get official 7-section Bank DPR | `report_id: str` | `BankDPRDocument` |
| **POST** | `/api/v2/feasibility/dpr` | Direct UserInput to DPR | `UserInput` JSON | `BankDPRDocument` |
| **GET** | `/api/v2/projects` | List authenticated user's projects | Header: `Authorization: Bearer <token>` | `List[ProjectModel]` |
| **POST** | `/api/v2/projects` | Create a new draft project | `{business_type, investment_amount, ...}` | `ProjectModel` |
| **GET** | `/api/v2/projects/{project_id}` | Get saved project & analysis | `project_id: str` | `ProjectModel` |
| **POST** | `/api/v2/projects/{project_id}/analyze` | Run analysis and save to PostgreSQL | `project_id: str` | `ProjectModel` |
| **GET** | `/api/v2/projects/{project_id}/dpr` | Retrieve persistent Bank DPR | `project_id: str` | `BankDPRDocument` |
| **GET** | `/api/v2/locations/states` | List all Indian states from LGD | None | `List[StateInfo]` |
| **GET** | `/api/v2/locations/districts` | List districts for a state | `state_code: int` | `List[DistrictInfo]` |
| **GET** | `/api/v2/locations/blocks` | List blocks for a district | `district_code: int` | `List[BlockInfo]` |
| **GET** | `/api/v2/locations/villages` | List villages for a district/block | `district_code: int, block_code: int` | `List[VillageInfo]` |
