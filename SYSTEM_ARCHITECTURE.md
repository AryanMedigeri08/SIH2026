# 🇮🇳 Udyam Saathi (उद्यम साथी) — Comprehensive System Architecture

> **Smart India Hackathon 2026** • National MSME Credit Feasibility, Bank DPR Appraisal & 22-Language Voice Advisory Platform.

---

## 1. Executive Architectural Overview

**Udyam Saathi** is an institutional-grade, multi-tier enterprise credit appraisal and advisory platform designed for Indian micro, small, and medium enterprises (MSMEs). It bridges the gap between rural/semi-urban entrepreneurs and scheduled commercial banks by automating credit risk assessment, multi-scheme subsidy optimization, bankable DPR generation, real-time screen-aware chatbot advisory, and a **22-Language Indic Multilingual Voice Agent**.

```mermaid
graph TB
    subgraph ClientTier ["1. CLIENT TIER (User Presentation Layer)"]
        UI_SPA["React 18 + Vite SPA<br/>(Tailwind CSS, Outfit / Noto Sans)"]
        UI_DASH["Institutional 7-Section Dashboard<br/>(Overview, Viability, Market, Schemes, Financials, Risk, SWOT, DPR)"]
        UI_CHAT["Persistent Movable Groq Chatbot<br/>(Screen-Aware & Origin-Directed Minimize)"]
        UI_VOICE["22-Language Voice Agent UI<br/>(Web Audio API & MediaRecorder)"]
    end

    subgraph GatewayTier ["2. API & SECURITY GATEWAY TIER"]
        FASTAPI["FastAPI High-Performance Async Gateway<br/>(Port 8000 / Cloud Run Dynamic Port)"]
        AUTH_SEC["Firebase Admin SDK & JWT Auth<br/>(Service Account Verification)"]
        CORS_LOG["Request Tracing & Structured Logging<br/>(REQ-UUID & Latency Metrics)"]
    end

    subgraph CoreEngineTier ["3. CORE REASONING & COMPUTATIONAL ENGINES"]
        ML_XGB["10-D Supervised XGBoost Classifier<br/>(viability_xgb.joblib)"]
        SHAP_EXP["Lundberg TreeSHAP Explainer<br/>(Marginal Game-Theoretic Attributions)"]
        SCHEME_OPT["Multi-Scheme Subsidy Optimizer<br/>(PMEGP, Mudra, PMFME, CGTMSE, Stand-Up India)"]
        FIN_DSCR["Credit Feasibility & Amortization Engine<br/>(DSCR, Net Term Loan, EMI, Break-Even Capacity)"]
        DPR_GEN["Bank-Grade 7-Section DPR Generator<br/>(CMA Data, Depreciation, Cash Flow Annexures)"]
    end

    subgraph AIAgentTier ["4. AI & MULTILINGUAL CONVERSATIONAL LAYER"]
        GROQ_LLM["Groq Cloud Ultra-Low Latency Inference<br/>(LLaMA 3.3 70B / GPT-OSS-20B via GROQ_CHAT_KEY)"]
        ENG_SYNTH["English-First Reasoning Synthesizer<br/>(Schema-Guaranteed AI Invariant)"]
        GCLOUD_TRANS["Google Cloud Translation API v2<br/>(22 Scheduled Indian Languages)"]
        VOICE_PIPELINE["22-Language Voice Agent Pipeline<br/>(Bhashini / Whisper ASR + NMT + Indic TTS)"]
    end

    subgraph CachingTier ["5. 4-TIER MULTI-LEVEL CACHING SYSTEM"]
        L1_CACHE["L1: Browser LocalStorage<br/>(Chat History, Window Pos, Theme)"]
        L2_CACHE["L2: Backend Memory SynthesisCache<br/>(MD5 Hashed Report Fingerprints)"]
        L3_CACHE["L3: Persistent SQLite Disk Cache<br/>(translation_cache.sqlite3)"]
        L4_CACHE["L4: PostgreSQL DB Profile Store<br/>(Multi-Business Persistent Records)"]
    end

    subgraph DataStorageTier ["6. DATA STORAGE & REFERENCE CATALOGS"]
        PG_DB["PostgreSQL Database<br/>(Users, Businesses, Reports, DPR Archive)"]
        JSON_CAT["Curated Indic Data Catalogs<br/>(Districts, MoSPI CPI, Clusters, Benchmarks)"]
    end

    %% Wiring Flows
    UI_SPA --> FASTAPI
    UI_DASH --> FASTAPI
    UI_CHAT --> FASTAPI
    UI_VOICE --> FASTAPI

    FASTAPI --> AUTH_SEC
    FASTAPI --> CORS_LOG

    FASTAPI --> ML_XGB
    FASTAPI --> SHAP_EXP
    FASTAPI --> SCHEME_OPT
    FASTAPI --> FIN_DSCR
    FASTAPI --> DPR_GEN

    FASTAPI --> GROQ_LLM
    GROQ_LLM --> ENG_SYNTH
    ENG_SYNTH --> GCLOUD_TRANS
    ENG_SYNTH --> VOICE_PIPELINE

    GCLOUD_TRANS <--> L3_CACHE
    FASTAPI <--> L2_CACHE
    UI_SPA <--> L1_CACHE
    FASTAPI <--> PG_DB
    CORE_DIR <--> JSON_CAT
```

---

## 2. End-to-End Data & Feasibility Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Entrepreneur as "Entrepreneur / Loan Officer"
    participant ReactUI as "React Frontend (UI/UX)"
    participant Gateway as "FastAPI Gateway (/api/v2)"
    participant ML as "XGBoost & TreeSHAP"
    participant Scheme as "Scheme Optimizer"
    participant Financial as "Financial Engine (DSCR/EMI)"
    participant GroqAI as "Groq Cloud LLM"
    participant Translation as "Google Cloud Translation / Bhashini"
    participant VoiceAgent as "22-Language Voice Pipeline"
    participant DB as "PostgreSQL & SQLite Cache"

    Entrepreneur->>ReactUI: 1. Submits 7-Step Feasibility Form (or Voice Input)
    ReactUI->>Gateway: POST /api/v2/feasibility/assess
    Gateway->>ML: 2. Compute 10-D Feature Vector
    ML-->>Gateway: Viability Score (94%), Probability & SHAP Values
    Gateway->>Scheme: 3. Evaluate Eligibility against 5 National Schemes
    Scheme-->>Gateway: Recommended Scheme (PMEGP: ₹3.75L Grant)
    Gateway->>Financial: 4. Compute 5-Yr Cash Flow, DSCR (1.78x) & EMI (₹10,240)
    Financial-->>Gateway: Financial Schedule & Break-Even Metric
    Gateway->>GroqAI: 5. Prompt Groq LLM in English (English-First Invariant)
    GroqAI-->>Gateway: Executive English Synthesis & Risk Breakdown
    Gateway->>Translation: 6. Translate to User's Indic Language (e.g. Hindi/Tamil)
    Translation<-->>DB: Query/Store in Persistent SQLite Translation Cache
    Translation-->>Gateway: Translated Multilingual Assessment Payload
    Gateway->>DB: 7. Persist Assessment & Multi-Business Record
    Gateway-->>ReactUI: Return Comprehensive Appraisal Response
    ReactUI-->>Entrepreneur: 8. Render Interactive Dashboard, Charts & Audio DPR
    opt Multilingual Voice Interaction
        Entrepreneur->>VoiceAgent: Speaks Query in Native Indic Language (e.g. Marathi / Kannada)
        VoiceAgent->>Gateway: Transcribe ASR -> Translate -> Query Chatbot -> Synthesize Indic TTS Audio
        VoiceAgent-->>Entrepreneur: Plays Natural Voice Response in User's Dialect
    end
```

---

## 3. 22-Language Multilingual Voice Agent Pipeline

Udyam Saathi incorporates a conversational **Voice Agent** supporting **all 22 Eighth Schedule Constitutional Languages of India**:

| Zone | Supported Scheduled Languages |
| :--- | :--- |
| **Northern** | Hindi (हिन्दी), Punjabi (ਪੰਜਾਬੀ), Kashmiri (کٲشُر), Dogri (डोगरी), Urdu (اردو) |
| **Western** | Marathi (मराठी), Gujarati (ગુજરાતી), Konkani (कोंकणी), Sindhi (سنڌي) |
| **Southern** | Tamil (தமிழ்), Telugu (తెలుగు), Kannada (ಕನ್ನಡ), Malayalam (മലയാളം) |
| **Eastern** | Bengali (বাংলা), Odia (ଓଡ଼ିଆ), Assamese (অসমীয়া), Maithili (मैथिली) |
| **Central / Tribal** | Sanskrit (संस्कृतम्), Santali (ᱥᱟᱱᱛᱟᱲᱤ), Bodo (बड़ो), Nepali (नेपाली), Manipuri/Meitei (মৈতৈলোন্) |

```mermaid
graph LR
    subgraph AudioIn ["1. VOICE CAPTURE"]
        MIC["User Mic Input<br/>(16kHz PCM / WebM)"] --> REC["Browser MediaRecorder / Web Audio API"]
    end

    subgraph ASRTier ["2. AUTOMATIC SPEECH RECOGNITION (ASR)"]
        REC --> ASR_ROUTE{"Speech Engine Route"}
        ASR_ROUTE -->|Indic Direct| BHASHINI_ASR["Bhashini Indic ASR<br/>(AI4Bharat Conformer / IndicWav2Vec)"]
        ASR_ROUTE -->|Cloud Fallback| GCLOUD_STT["Google Cloud Speech-to-Text v2"]
    end

    subgraph EnglishReasoningPivot ["3. ENGLISH REASONING PIVOT (AI Invariant)"]
        BHASHINI_ASR --> NMT_IN["Indic to English NMT Pivot"]
        GCLOUD_STT --> NMT_IN
        NMT_IN --> CHAT_CORE["Udyam Saathi Context-Aware LLM<br/>(Groq LLaMA 3.3 70B / Rule Engine)"]
    end

    subgraph IndicNMT ["4. NEURAL MACHINE TRANSLATION (NMT)"]
        CHAT_CORE --> NMT_OUT["English to 22 Indic Languages<br/>(Google Cloud Translation API v2 + Bhashini NMT)"]
        NMT_OUT <--> SQLITE_CACHE["Persistent Disk SQLite Cache<br/>(translation_cache.sqlite3)"]
    end

    subgraph TTSTier ["5. INDIC TEXT-TO-SPEECH (TTS)"]
        NMT_OUT --> TTS_ENGINE{"Indic TTS Engine"}
        TTS_ENGINE -->|Natural Voice| BHASHINI_TTS["Bhashini Indic TTS<br/>(FastSpeech2 / VITS Indic Voices)"]
        TTS_ENGINE -->|Cloud Polyglot| GCLOUD_TTS["Google Cloud Neural2 TTS"]
    end

    subgraph AudioOut ["6. AUDIO PLAYBACK"]
        BHASHINI_TTS --> STREAM["Web Audio API Stream Player"]
        GCLOUD_TTS --> STREAM
        STREAM --> SPEAKER["User Earphones / Speaker Output"]
    end
```

### Voice Agent Pipeline Execution Flow:
1. **Audio Capture**: Captures 16kHz PCM audio from mobile/desktop browser via Web Audio API.
2. **ASR (Speech-to-Text)**: Automatically detects spoken language from 22 Indic dialects and transcribes speech to native script.
3. **English Pivot Translation**: Translates native text into English to eliminate LLM reasoning hallucinations and ensure strict adherence to financial formulas (DSCR, CMA, MoSPI CPI).
4. **Context-Grounded LLM Reasoning**: Groq AI processes the request using real-time dashboard telemetry (active tab, loan figures, schemes).
5. **NMT Output Translation**: Translates the verified English response into the user's selected language using Google Cloud Translation API with 4-tier caching.
6. **Indic TTS Synthesis**: Synthesizes natural-sounding speech in the target language and streams high-fidelity audio back to the user.

---

## 4. 4-Tier Multi-Level Caching Subsystem

To minimize external API costs, eliminate redundant network calls, and ensure sub-100ms response times, Udyam Saathi implements a **4-Tier Hierarchical Caching Architecture**:

```mermaid
graph TD
    REQ["Incoming User / Translation Request"] --> L1{"Tier 1: Browser localStorage"}
    
    L1 -->|Hit (Instant)| L1_HIT["Return Cached UI State / History<br/>Latency: < 1ms"]
    L1 -->|Miss| L2{"Tier 2: Backend Memory Cache<br/>(SynthesisCache)"}
    
    L2 -->|Hit (Memory)| L2_HIT["Return RAM Synthesis Payload<br/>Latency: < 5ms"]
    L2 -->|Miss| L3{"Tier 3: Persistent SQLite Disk Cache<br/>(translation_cache.sqlite3)"}
    
    L3 -->|Hit (Disk SQL)| L3_HIT["Return Cached Indic Translation<br/>Latency: < 15ms"]
    L3 -->|Miss| EXT["Tier 4: External API Computation<br/>(Groq Cloud / Google Cloud Translation / PostgreSQL DB)"]
    
    EXT --> L3_WRITE["Write to Persistent SQLite Disk Cache"]
    L3_WRITE --> L2_WRITE["Store in In-Memory Synthesis RAM"]
    L2_WRITE --> L1_WRITE["Save to Browser localStorage"]
    L1_WRITE --> RESP["Deliver Fresh Response to User"]
```

---

## 5. Screen-Aware Floating Chatbot Architecture

```mermaid
graph TB
    subgraph ViewportTracking ["1. VIEWPORT & ROUTE TRACKING"]
        NAV["React Router Navigation<br/>(/viability, /market, /schemes, /financials, /risk, /swot, /dpr)"]
        CTX_EXTRACT["ChatContext.jsx Telemetry Extractor<br/>(Extracts Live Screen Data & Metrics)"]
        NAV --> CTX_EXTRACT
    end

    subgraph ChatWindow ["2. MOVABLE FLOATING WINDOW"]
        WIN["FloatingChatWindow.jsx<br/>(Draggable Header, Viewport Bounds Clamped)"]
        MIN_ANIM["Targeted Minimize Vector Animation<br/>(Transforms directly into Nav Button)"]
        THEME_CTRL["In-Chat Theme Switcher<br/>(Sovereign Light, Midnight Navy, Emerald Mint)"]
        QUICK_CHIPS["Contextual Quick Inquiries<br/>(Summarize Screen, Explain TreeSHAP, Audit DSCR)"]
        
        CTX_EXTRACT --> WIN
        WIN --> THEME_CTRL
        WIN --> QUICK_CHIPS
        WIN --> MIN_ANIM
    end

    subgraph TopNavIntegration ["3. TOP NAVIGATION INTEGRATION"]
        NAV_BTN["ChatbotNavButton.jsx<br/>(Immediately Left of Live Telemetry)"]
        MIN_ANIM -.->|Collapse / Expand Delta| NAV_BTN
    end

    subgraph BackendChatService ["4. BACKEND CONTEXT INJECTION"]
        CHAT_ROUTER["POST /api/v2/chat<br/>(ChatRouter in chat.py)"]
        CHAT_SVC["ChatService in chat_service.py<br/>(Grounded Domain Prompt + Tab Telemetry)"]
        GROQ_CLIENT["Groq Cloud Client (GROQ_CHAT_KEY)<br/>(LLaMA 3.3 70B / GPT-OSS-20B)"]
        FALLBACK["Deterministic Rule-Based Fallback Engine"]
        
        WIN --> CHAT_ROUTER
        CHAT_ROUTER --> CHAT_SVC
        CHAT_SVC -->|Online| GROQ_CLIENT
        CHAT_SVC -->|Offline / Rate-Limit| FALLBACK
    end
```

---

## 6. Security, Deployment & DevOps Topology

```mermaid
graph TB
    subgraph ContainerTopology ["CONTAINER & CLOUD TOPOLOGY"]
        subgraph CloudRun ["Google Cloud Run / Serverless Container"]
            DOCKER_BE["Backend Container (Python 3.11 Slim)<br/>FastAPI + XGBoost + Uvicorn ($PORT Dynamic Binding)"]
            SQLITE_VOL["Persistent Local SQLite Volume<br/>(/app/backend/app/data/translation_cache.sqlite3)"]
            DOCKER_BE <--> SQLITE_VOL
        end

        subgraph CloudRunFE ["Frontend Container (Nginx Alpine)"]
            DOCKER_FE["Frontend Container (Nginx Alpine)<br/>Production Static Bundle ($PORT Dynamic Binding)"]
        end

        subgraph ManagedCloud ["Managed Cloud Subsystems"]
            POSTGRES["PostgreSQL Managed Database<br/>(Neon / Supabase / Cloud SQL)"]
            FIREBASE["Firebase Authentication Subsystem<br/>(Google Identity Platform)"]
            GROQ_API["Groq Cloud AI LLM Infrastructure"]
            GCLOUD_API["Google Cloud Translation / Speech API"]
            BHASHINI_API["National Bhashini AI Mission APIs"]
        end
    end

    DOCKER_FE -->|Proxy API Requests| DOCKER_BE
    DOCKER_BE --> POSTGRES
    DOCKER_BE --> FIREBASE
    DOCKER_BE --> GROQ_API
    DOCKER_BE --> GCLOUD_API
    DOCKER_BE --> BHASHINI_API
```

---

## 7. Technology Stack Summary

| Layer | Technologies & Frameworks |
| :--- | :--- |
| **Frontend UI/UX** | React 18, Vite 5, Vanilla Tailwind CSS (Sovereign Theme Tokens), Lucide React, Canvas Confetti, Web Audio API |
| **Backend API** | FastAPI, Python 3.11, Uvicorn, Pydantic v2, HTTPX Async Client, Python-Jose |
| **Machine Learning** | XGBoost 2.0+, Lundberg TreeSHAP, Scikit-Learn, Joblib, NumPy, Pandas |
| **AI & Conversational** | Groq Cloud SDK (`GROQ_CHAT_KEY`), LLaMA 3.3 70B, GPT-OSS-20B, Deterministic Rule Fallback |
| **Multilingual & Voice** | Google Cloud Translation API v2, National Bhashini Mission APIs (ASR, NMT, Indic TTS), 22 Scheduled Indian Languages |
| **Persistence & Cache** | PostgreSQL, SQLite3 (`translation_cache.sqlite3`), In-Memory RAM Cache, Browser `localStorage` |
| **Authentication** | Firebase Admin SDK, Firebase Auth JWT Token Interceptor, Argon2 / Passlib |
| **DevOps & Containers** | Docker Multi-Stage Builds, Docker Compose, Google Cloud Run, Cloud Build, Nginx |

---
*Udyam Saathi (उद्यम साथी) • Smart India Hackathon 2026 • AI-Powered National MSME Credit Feasibility & Bank DPR Portal*
