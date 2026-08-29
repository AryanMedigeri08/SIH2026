# 🇮🇳 Udyam Saathi (उद्यम साथी) — Detailed User Flow & System Interaction Architecture

> **Smart India Hackathon 2026** • Step-by-Step User Journeys, System Execution State Machine, and Interaction Diagrams.

---

## 1. Master End-to-End User Flowchart

The following diagram illustrates the complete end-to-end journey of an entrepreneur or bank loan officer interacting with the Udyam Saathi platform:

```mermaid
graph TD
    %% Entry & Auth
    START(["👤 User Lands on Platform<br/>(udyam-saathi.gov.in / localhost)"]) --> LANG_SEL["Select Preferred Interface Language<br/>(22 Indic Languages Supported)"]
    LANG_SEL --> AUTH_CHECK{"Authenticated Session?"}
    
    AUTH_CHECK -->|No| AUTH_FLOW["Authentication Gate<br/>(Google Sign-In / Phone OTP / Firebase JWT)"]
    AUTH_FLOW --> SYNC_PROF["Sync User Profile & Multi-Business Store in PostgreSQL"]
    SYNC_PROF --> DASH_ENTRY["Enter Platform Workspace"]
    AUTH_CHECK -->|Yes| DASH_ENTRY

    %% Navigation Routing
    DASH_ENTRY --> USER_CHOICE{"User's Immediate Goal"}
    
    USER_CHOICE -->|Explore Benchmark Cases| PRESET_CASES["Click Preset Benchmark Scenarios<br/>(Dairy, Mustard Oil, Bio-Agro, Garment)"]
    USER_CHOICE -->|Evaluate New Enterprise| WIZARD_FLOW["Launch 7-Step Feasibility Wizard<br/>(Route: /wizard)"]
    USER_CHOICE -->|Instant Loan Simulation| CALC_FLOW["Launch Quick Calculator Modal<br/>(Sliders: Loan, Tenor, Margin, EMI)"]
    USER_CHOICE -->|Ask AI Voice/Chatbot| CHAT_FLOW["Activate AI Chatbot / Voice Agent<br/>(Alt + Space or Top Navbar)"]

    %% Wizard Pipeline
    WIZARD_FLOW --> WIZ_S1["Step 1: Enterprise Profile & Sector"]
    WIZ_S1 --> WIZ_S2["Step 2: Location & Catchment Radius"]
    WIZ_S2 --> WIZ_S3["Step 3: Project Outlay & Capital Split"]
    WIZ_S3 --> WIZ_S4["Step 4: Promoter Equity & Social Category"]
    WIZ_S4 --> WIZ_S5["Step 5: Capacity, Pricing & Revenue"]
    WIZ_S5 --> WIZ_S6["Step 6: Regulatory Licenses & Clearances"]
    WIZ_S6 --> WIZ_S7["Step 7: Language Preference & Review"]
    WIZ_S7 --> WIZ_SUBMIT["Submit Feasibility Form"]

    %% Backend Computation Execution
    WIZ_SUBMIT --> SYS_LOADER["Staged Real-Time Computation Loader<br/>(Animated Progress Steps)"]
    SYS_LOADER --> ML_EXEC["1. 10-D Supervised XGBoost + Lundberg TreeSHAP"]
    SYS_LOADER --> SCHEME_EXEC["2. Multi-Scheme Subsidy Optimizer (PMEGP/Mudra/PMFME)"]
    SYS_LOADER --> FIN_EXEC["3. 5-Yr Cash Flow, DSCR (1.78x) & EMI Amortization"]
    SYS_LOADER --> AI_EXEC["4. Groq English-First Reasoning Synthesis"]
    SYS_LOADER --> TRANS_EXEC["5. Google Cloud Translation to User's Indic Dialect"]

    %% Dashboard Exploration
    ML_EXEC & SCHEME_EXEC & FIN_EXEC & AI_EXEC & TRANS_EXEC --> DASH_MAIN["Render 7-Section Institutional Dashboard<br/>(Multi-Page Routed Architecture)"]
    PRESET_CASES --> DASH_MAIN

    DASH_MAIN --> TAB_NAV{"Explore Dashboard Tabs"}
    TAB_NAV --> TAB_OVERVIEW["📊 1. Overview Synthesis<br/>(Executive summary & Bankability)"]
    TAB_NAV --> TAB_VIABILITY["🧠 2. ML Viability & TreeSHAP<br/>(Radar charts, Log-odds feature drivers)"]
    TAB_NAV --> TAB_MARKET["📍 3. Market Demand & Clusters<br/>(Catchment TAM, Saturation & Unit floor)"]
    TAB_NAV --> TAB_SCHEMES["🏛️ 4. Scheme Optimizer<br/>(PMEGP, Mudra, PMFME, CGTMSE subsidies)"]
    TAB_NAV --> TAB_FINANCIALS["📈 5. Financials & Cash Flow<br/>(5-Yr P&L, DSCR solvency, EMI schedules)"]
    TAB_NAV --> TAB_RISK["⚠️ 6. Risk Assessment Matrix<br/>(MoSPI CPI inflation, Weather, Mitigations)"]
    TAB_NAV --> TAB_SWOT["🎯 7. SWOT Analysis Matrix<br/>(Strengths, Weaknesses, Opportunities, Threats)"]
    TAB_NAV --> TAB_DPR["📑 8. Official Bank DPR Package<br/>(7-Section CMA report & PDF Download)"]

    %% Chatbot Interaction
    CHAT_FLOW --> CHAT_INTERACT["Persistent Floating Chatbot Window<br/>(Automatically detects active tab telemetry)"]
    CHAT_INTERACT --> VOICE_CONV["22-Language Indic Voice Agent<br/>(Speaks/Listens in user's native dialect)"]
    
    %% Bank DPR Action
    TAB_DPR --> DPR_DOWNLOAD["Generate Official 7-Section Bank DPR PDF"]
    DPR_DOWNLOAD --> BANK_SUBMIT(["🏦 Submit to Bank Loan Officer / PMEGP Portal"])
```

---

## 2. Phase-by-Phase User Interaction & System Response

### 🔹 Phase 1: Landing, Localization & Authentication

```mermaid
sequenceDiagram
    autonumber
    actor User as "Entrepreneur / Loan Officer"
    participant UI as "React SPA (Landing Page)"
    participant LangCtx as "LanguageContext (i18n)"
    participant AuthCtx as "AuthContext & Firebase"
    participant API as "FastAPI Gateway (/api/v2)"
    participant DB as "PostgreSQL Database"

    User->>UI: 1. Opens Udyam Saathi Landing Page
    UI->>LangCtx: 2. Reads browser locale / stored language preference
    LangCtx-->>UI: Renders UI in selected Indic language (e.g. Hindi / Marathi / Tamil)
    User->>UI: 3. Clicks "Login" / "Register" or "Get Started"
    UI->>AuthCtx: 4. Initiates Firebase Authentication popup (Google / Phone OTP / Email)
    AuthCtx-->>User: Authenticates credentials & issues secure JWT Token
    AuthCtx->>API: 5. POST /api/v2/auth/session (Bearer Token)
    API->>DB: 6. Upsert user profile & fetch user's saved enterprise list
    DB-->>API: Returns user businesses & active appraisal ID
    API-->>AuthCtx: 200 OK (User Profile + Saved Businesses)
    AuthCtx-->>UI: Transitions to Authenticated Workspace Dashboard
```

---

### 🔹 Phase 2: 7-Step Feasibility Assessment Wizard

The 7-Step Wizard collects domain parameters required for the **10-Dimensional Machine Learning Viability Classifier**, **MoSPI CPI inflation reconciliation**, and **Statutory Bank DPR Package**:

| Step | Form Screen | User Inputs | Real-Time Validation & Helpers |
| :---: | :--- | :--- | :--- |
| **1** | **Enterprise Profile** | Enterprise Name, Sector (Agro, Manufacturing, Services, Retail), Business Activity, Organization Type (Proprietorship, Partnership, Pvt Ltd). | Auto-suggests relevant NIC-2008 4-digit activity codes. |
| **2** | **Location & Catchment** | State, District, Block, Village/Town, Infrastructure Readiness Rating (Roads, Power, Water, Haat access). | Dynamic cascading dropdowns based on Census 2011 district master catalog. |
| **3** | **Project Outlay** | Land & Civil Works, Plant & Machinery, Working Capital Liquid Reserve, Contingency Buffer. | Live auto-sum of **Total Project Outlay** (Capex + Opex). |
| **4** | **Promoter Profile** | Social Category (General, OBC, SC/ST, Women, Ex-Servicemen), Rural vs Urban flag, Promoter Equity Margin %. | Calculates minimum required promoter equity (e.g. 5% for Special Category under PMEGP). |
| **5** | **Capacity & Pricing** | Operating Capacity (units/month), Expected Raw Material Cost per unit, Proposed Selling Price per unit. | Computes estimated annual gross turnover and unit contribution margin. |
| **6** | **Statutory & Compliance** | Existing Licenses: Udyam Registration, GSTIN, FSSAI, Pollution Control Board (CTE/CTO), Fire NOC. | Informs user which statutory clearances are mandatory for bank disbursement. |
| **7** | **Language & Review** | Preferred appraisal language (English, Hindi, Marathi, Tamil, Telugu, Kannada, etc.), Summary Review. | Comprehensive pre-flight check before initiating AI/ML inference. |

```mermaid
graph LR
    subgraph WizardSteps ["7-Step Feasibility Wizard Pipeline"]
        S1["Step 1: Enterprise Profile"] --> S2["Step 2: Location & Amenities"]
        S2 --> S3["Step 3: Capital Outlay"]
        S3 --> S4["Step 4: Promoter Equity"]
        S4 --> S5["Step 5: Capacity & Pricing"]
        S5 --> S6["Step 6: Compliance & Licenses"]
        S6 --> S7["Step 7: Review & Language"]
    end
    
    S7 --> SUBMIT{"Validate Form"}
    SUBMIT -->|Invalid| S1
    SUBMIT -->|Valid| LOAD["Trigger Staged Loader & Backend Execution"]
```

---

### 🔹 Phase 3: Staged Execution Loader & Computational Engine

When the user submits the assessment, Udyam Saathi displays an engaging staged progress loader while executing parallel micro-computations:

```mermaid
sequenceDiagram
    autonumber
    participant UI as "ReportGenerationLoader UI"
    participant Gateway as "FastAPI Gateway"
    participant XGBoost as "10-D XGBoost & TreeSHAP"
    participant SchemeEngine as "Scheme Eligibility Engine"
    participant CashFlow as "5-Year Financial Engine"
    participant GroqLLM as "Groq Cloud LLM"
    participant GoogleTranslate as "Google Cloud Translation API"
    participant SQLiteCache as "SQLite Disk Cache"

    UI->>Gateway: POST /api/v2/feasibility/assess
    Note over UI: Stage 1: "Calibrating 10-D XGBoost Viability Classifier..."
    Gateway->>XGBoost: Compute feature vector (DSCR, Infra, Density, Saturation, Weather)
    XGBoost-->>Gateway: Viability Verdict ('SUITABLE' 94%), Probabilities & SHAP values
    
    Note over UI: Stage 2: "Scanning National Subsidy Schemes (PMEGP, Mudra, PMFME)..."
    Gateway->>SchemeEngine: Evaluate social profile & outlay against national scheme rules
    SchemeEngine-->>Gateway: Matched schemes, capital subsidy grant (₹3.75L) & net loan

    Note over UI: Stage 3: "Simulating 5-Year Cash Flow, DSCR & Loan Amortization..."
    Gateway->>CashFlow: Build 60-month amortization schedule, DSCR (1.78x), Break-even volume
    CashFlow-->>Gateway: Comprehensive financial schedules & repayment tables

    Note over UI: Stage 4: "Synthesizing AI Executive Strategic Recommendations..."
    Gateway->>GroqLLM: Prompt Groq LLaMA 3.3 70B in English (English-First Invariant)
    GroqLLM-->>Gateway: Executive Synthesis, credit risks, and key strengths

    Note over UI: Stage 5: "Translating Appraisal to Selected Indic Language..."
    Gateway->>GoogleTranslate: Translate narrative synthesis to user's dialect (e.g. Marathi)
    GoogleTranslate<-->>SQLiteCache: Check/Store in SQLite persistent disk cache
    GoogleTranslate-->>Gateway: Multilingual localized appraisal payload

    Gateway-->>UI: 200 OK (Full Feasibility Appraisal Object)
    Note over UI: Confetti Celebration & Redirect to /dashboard
```

---

### 🔹 Phase 4: 7-Section Institutional Dashboard Interaction

The generated report is partitioned into **7 distinct routed pages**, providing zero-clutter institutional navigation:

```mermaid
graph TD
    DASH["Multi-Page Routed Appraisal Dashboard"]
    
    DASH --> P1["📊 1. Overview Synthesis (/dashboard or /reports/:id)"]
    P1 --- D1["Executive summary, viability score meter, capital breakdown, subsidy pill, quick actions."]
    
    DASH --> P2["🧠 2. ML Viability & TreeSHAP (/viability)"]
    P2 --- D2["10-D radar chart, SHAP horizontal bar chart, positive contributors & negative risk drivers."]
    
    DASH --> P3["📍 3. Market Demand & Clusters (/market)"]
    P3 --- D3["Census 2026 catchment demand, MSME cluster density, competitor saturation, break-even unit price floor."]
    
    DASH --> P4["🏛️ 4. Government Scheme Optimizer (/schemes)"]
    P4 --- D4["PMEGP, Mudra, PMFME, CGTMSE comparison, grant %, promoter contribution, nodal agency steps."]
    
    DASH --> P5["📈 5. Financials & Cash Flow (/financials)"]
    P5 --- D5["5-Year P&L projections, monthly EMI repayment schedule, DSCR ratio (1.78x), break-even capacity %."]
    
    DASH --> P6["⚠️ 6. Risk Assessment Matrix (/risk)"]
    P6 --- D6["Composite risk score, CPI inflation risk, monsoon disruption risk, working capital buffer roadmap."]
    
    DASH --> P7["🎯 7. SWOT Analysis Matrix (/swot)"]
    P7 --- D7["Grounded Strengths, Weaknesses, Opportunities, and Threats tailored to district & sector."]
    
    DASH --> P8["📑 8. Official Bank DPR Package (/dpr)"]
    P8 --- D8["7-Section Bank DPR package, CMA annexures, statutory licensing checklist, PDF export."]
```

---

### 🔹 Phase 5: Persistent Movable Chatbot & Real-Time Screen-Aware Interaction

The floating Chatbot utility window follows the user seamlessly across all dashboard tabs:

```mermaid
sequenceDiagram
    autonumber
    actor User as "Entrepreneur"
    participant NavBtn as "Chatbot Nav Button (Navbar)"
    participant ChatWin as "FloatingChatWindow (React)"
    participant ChatCtx as "ChatContext.jsx"
    participant API as "FastAPI Gateway (/api/v2/chat)"
    participant Groq as "Groq Cloud LLaMA 3.3 70B"

    User->>NavBtn: 1. Clicks "Chatbot" button or presses [Alt + Space]
    NavBtn->>ChatWin: Triggers Origin-Directed Expansion Animation
    ChatWin-->>User: Floats smoothly on screen (Draggable, theme-aware)
    User->>User: Navigates to "/financials" tab in dashboard
    ChatCtx->>ChatWin: 2. Detects route change & extracts active screen data (DSCR: 1.78, EMI: ₹10,240)
    ChatWin-->>User: Updates sub-header: "Active Viewport: 5-Year Financials & Cash Flow"
    ChatWin-->>User: Displays quick action: "⚡ Summarize this Financials page"
    User->>ChatWin: 3. Clicks "⚡ Summarize this Financials page"
    ChatWin->>ChatCtx: Submits message with full active tab telemetry payload
    ChatCtx->>API: POST /api/v2/chat (messages, active_tab_data, language)
    API->>Groq: Evaluates prompt with live telemetry grounding
    Groq-->>API: Generates structured financial breakdown with key takeaways
    API-->>ChatWin: Returns response with latency metadata (1.1s)
    ChatWin-->>User: Renders rich formatted markdown response with copy button
    User->>ChatWin: 4. Clicks Minimize [-] button
    ChatWin->>NavBtn: Smooth vector collapse animation into Top Navbar button
```

---

### 🔹 Phase 6: 22-Language Indic Multilingual Voice Agent Interaction

For entrepreneurs who prefer talking in their regional mother tongue:

```mermaid
sequenceDiagram
    autonumber
    actor User as "Rural Entrepreneur"
    participant VoiceUI as "Voice Agent Mic Interface"
    participant WebAudio as "Browser Web Audio API"
    participant BhashiniASR as "Indic Speech Recognition (ASR)"
    participant PivotNMT as "Indic-to-English NMT Pivot"
    participant CoreAI as "Udyam Saathi Groq AI Engine"
    participant IndicNMT as "English-to-Indic NMT"
    participant IndicTTS as "Indic Text-to-Speech (TTS)"

    User->>VoiceUI: 1. Taps Mic button and speaks in native language (e.g. Marathi: "माझ्या डेअरी व्यवसायाला किती सबसिडी मिळेल?")
    VoiceUI->>WebAudio: Captures 16kHz audio stream via MediaRecorder
    WebAudio->>BhashiniASR: Streams voice audio payload
    BhashiniASR-->>PivotNMT: Transcribes Marathi speech to native text
    PivotNMT-->>CoreAI: Translates to verified English prompt: "How much subsidy will my dairy business get under PMEGP?"
    Note over CoreAI: Injects active dairy project telemetry (₹9.00L cost, 35% PMEGP grant)
    CoreAI-->>IndicNMT: Generates exact factual response in English: "Under PMEGP, your dairy enterprise is eligible for ₹3.15 Lakhs subsidy (35%)..."
    IndicNMT-->>IndicTTS: Translates verified response to Marathi: "PMEGP योजनेअंतर्गत, तुमच्या डेअरी प्रकल्पाला ₹३.१५ लाख (३५%) सबसिडी मिळेल..."
    IndicTTS-->>VoiceUI: Synthesizes natural Marathi speech audio stream
    VoiceUI-->>User: 2. Plays clear, natural voice response in user's earphones/speaker
```

---

### 🔹 Phase 7: Interactive Quick Calculator Simulation

For instant what-if scenario testing without altering the master business record:

```mermaid
graph TD
    CALC_OPEN["User Clicks 'Quick Calculator' in Sidebar / Modal"] --> CALC_SLIDERS["Interactive Parametric Sliders"]
    
    CALC_SLIDERS --> S_LOAN["1. Project Outlay & Loan Amount (₹1L – ₹1 Cr)"]
    CALC_SLIDERS --> S_RATE["2. Bank Interest Rate (7.0% – 14.0%)"]
    CALC_SLIDERS --> S_TENOR["3. Loan Repayment Tenor (3 – 10 Years)"]
    CALC_SLIDERS --> S_REV["4. Projected Monthly Revenue & Margin %"]

    S_LOAN & S_RATE & S_TENOR & S_REV --> INSTANT_MATH["Client-Side Real-Time Math Engine"]
    
    INSTANT_MATH --> OUT_EMI["📊 Scheduled Monthly EMI: ₹10,240/mo"]
    INSTANT_MATH --> OUT_DSCR["📈 Real-Time DSCR: 1.78x (Adequate Solvency)"]
    INSTANT_MATH --> OUT_BEP["⚖️ Break-Even Volume: 38.5% Capacity Utilization"]
    INSTANT_MATH --> OUT_GRANT["🏛️ Potential Subsidy Grant: ₹3,15,000"]

    OUT_EMI & OUT_DSCR & OUT_BEP & OUT_GRANT --> APPLY_PROJ{"Apply to Assessment?"}
    APPLY_PROJ -->|Yes| UPDATE_REP["Update Master Appraisal & Re-render Dashboard"]
    APPLY_PROJ -->|No| CLOSE_CALC["Close Modal / Continue Exploration"]
```

---

## 3. Multi-Business State Switching State Machine

Udyam Saathi allows an entrepreneur or consultant to evaluate and manage **multiple micro-enterprises** within the same authenticated account:

```mermaid
stateDiagram-v2
    [*] --> LoggedIn: User Signs In
    LoggedIn --> ActiveBusiness_1: Load Default Business (e.g. Joypur Fresh Dairy)
    
    state ActiveBusiness_1 {
        [*] --> ViewOverview_1
        ViewOverview_1 --> ViewViability_1
        ViewViability_1 --> ViewDPR_1
    }

    ActiveBusiness_1 --> BusinessSwitcher: Click Top Navbar Business Switcher
    
    state BusinessSwitcher {
        [*] --> ListAllBusinesses
        ListAllBusinesses --> SelectBusiness_2: Choose "Purulia Mustard Oil"
        ListAllBusinesses --> CreateNewBusiness: Click "+ New Enterprise"
    }

    SelectBusiness_2 --> ActiveBusiness_2: Switch Active State
    
    state ActiveBusiness_2 {
        [*] --> ViewOverview_2
        ViewOverview_2 --> ViewFinancials_2
        ViewFinancials_2 --> ViewSchemes_2
    }

    CreateNewBusiness --> WizardFlow: Launch 7-Step Feasibility Wizard
    WizardFlow --> ActiveBusiness_3: Generate & Save Business 3
```

---

## 4. Bank DPR Generation & Loan Application Decision Tree

```mermaid
graph TD
    DPR_START["User Navigates to Official Bank DPR Tab"] --> CHECK_COMPLETENESS{"Is Appraisal 100% Complete?"}
    
    CHECK_COMPLETENESS -->|Missing Crucial Info| WARN["Display Incomplete Items Alert<br/>(e.g. Add Promoter Equity / Land Lease)"]
    WARN --> EDIT_PARAMS["Click 'Edit Parameters' in Wizard"]
    EDIT_PARAMS --> DPR_START

    CHECK_COMPLETENESS -->|100% Ready| PREVIEW["Preview Official 7-Section Bank DPR"]
    
    PREVIEW --> S1["Section 1: Enterprise & Promoter Profile"]
    PREVIEW --> S2["Section 2: Technical Feasibility & Machinery Specifications"]
    PREVIEW --> S3["Section 3: Market Demand & Demographic TAM"]
    PREVIEW --> S4["Section 4: Means of Finance & Subsidy Allocation"]
    PREVIEW --> S5["Section 5: 5-Year Projected Cash Flows & P&L"]
    PREVIEW --> S6["Section 6: Debt Service Coverage Ratio (DSCR) & Break-Even"]
    PREVIEW --> S7["Section 7: Statutory Compliance & Annexures Checklist"]

    S1 & S2 & S3 & S4 & S5 & S6 & S7 --> PDF_EXPORT["Click 'Download Bank DPR PDF'"]
    PDF_EXPORT --> PDF_GEN["Generate Official Bankable Document with QR Verification"]
    
    PDF_GEN --> LOAN_SUBMIT{"Choose Loan Submission Channel"}
    LOAN_SUBMIT -->|PMEGP Portal| KVIC["Submit Online via KVIC / PMEGP e-Portal"]
    LOAN_SUBMIT -->|Mudra Loan| BANK_BRANCH["Submit to Local Commercial Bank Branch (SBI, PNB, Canara, BoB)"]
    LOAN_SUBMIT -->|PMFME Scheme| MOFPI["Submit via PMFME Nodal Agency Portal"]
```

---

## 5. Summary of Key Interaction Rules

1. **Zero-Crash Invariant**: If external network connections or API rate limits occur at any step, Udyam Saathi seamlessly defaults to calibrated **deterministic local heuristics and pre-trained XGBoost artifacts** without breaking the user experience.
2. **Language Persistence**: When a user switches language (e.g. from English to Hindi or Tamil), the entire application — including charts, tooltips, tables, chatbot responses, and voice synthesis — updates synchronously.
3. **Screen-Aware AI Grounding**: The AI Chatbot always knows the exact dashboard screen and metrics currently in the user's viewport, providing immediate context-aware explanations on demand.

---
*Udyam Saathi (उद्यम साथी) • Smart India Hackathon 2026 • AI-Powered National MSME Credit Feasibility & Bank DPR Portal*
