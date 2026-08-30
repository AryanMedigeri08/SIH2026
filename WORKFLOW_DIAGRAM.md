# 📊 Udyam Saathi (उद्यम साथी): System Workflow & Architecture Diagrams

---

## 1. End-to-End User Journey & Processing Workflow

```mermaid
flowchart TD
    classDef intake fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef deterministic fill:#ecfdf5,stroke:#059669,stroke-width:2px,color:#047857;
    classDef machineLearning fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#b45309;
    classDef presentation fill:#f5f3ff,stroke:#7c3aed,stroke-width:2px,color:#6d28d9;
    classDef voiceChat fill:#fff1f2,stroke:#e11d48,stroke-width:2px,color:#be123c;

    subgraph Intake ["1. Input & Feasibility Wizard"]
        A["👤 User / Entrepreneur"] --> B["📝 7-Step Feasibility Appraisal Wizard"]
        B -->|Captures| C["Location Hierarchy (State, District, Village)<br/>Sector & Business Category<br/>Project Cost & Annual Turnover<br/>Promoter Category & Margin Capital"]
    end

    subgraph Tier1 ["2. Tier 1: Deterministic Computational Core"]
        C --> D["🏛️ 17 Government Scheme Matrix"]
        D -->|Optimizes| E["Top Scheme Grant Selection<br/>(PMEGP, PMFME, Mudra, Stand-Up, etc.)"]
        C --> F["🧮 Financial Sizing Engine"]
        F --> G["Capital Reconciliation<br/>(Outlay = Margin + Subsidy + Net Loan)"]
        F --> H["Amortization & Moratorium Schedule<br/>(Monthly EMI, Interest Liability)"]
        F --> I["Debt Service Coverage Ratio (DSCR)<br/>(RBI Benchmark Stress Testing >= 1.33)"]
    end

    subgraph Tier2 ["3. Tier 2: Geospatial Data & ML Viability Engine"]
        C --> J["🌐 Data.gov.in Village Amenities API<br/>(Mission Antyodaya 613 Catalog)"]
        J --> K["Site Infrastructure Score (0-10)<br/>(Power, Road, Banking, CSC, Mandi)"]
        C --> L["👥 Census 2011 Catchment Projection<br/>P(2026) = P0 * (1 + r)^n"]
        L --> M["Total Addressable Market (TAM)<br/>Competitor Density & MSME Saturation"]
        
        E & G & H & I & K & M --> N["📊 10-Dimensional Feature Vector (x0...x9)"]
        N --> O["🤖 Supervised XGBoost Viability Classifier"]
        O --> P["TreeSHAP Attribution Engine (C++)<br/>(Solvency Lifts & Caution Drags)"]
    end

    subgraph Tier3 ["4. Dashboard, Report & Multilingual Audio Advisor"]
        E & G & H & I & P --> Q["🖥️ 8-Tab Multilingual Dashboard<br/>(English, Hindi, Marathi, Telugu, Tamil, Kannada)"]
        Q --> R["📄 IBA-Compliant 7-Section Bank DPR<br/>(Downloadable PDF / Print-Ready)"]
        
        Q <--> S["🎙️ Interactive Voice & Chat AI Advisor"]
        S -->|Dynamic VAD| T["Groq Whisper Large v3 STT"]
        T -->|Context Grounded| U["Groq LLM Reasoning Engine"]
        U -->|Speech Synthesis| V["In-Memory gTTS Audio Playback"]
        V --> Q
    end

    class A,B,C intake;
    class D,E,F,G,H,I deterministic;
    class J,K,L,M,N,O,P machineLearning;
    class Q,R presentation;
    class S,T,U,V voiceChat;
```

---

## 2. Interactive Voice & Chatbot Telemetry Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Entrepreneur
    participant UI as 🖥️ Floating Chat UI (Web Audio API)
    participant VAD as 🔊 Dynamic Silence Detector
    participant API as ⚡ FastAPI Backend Router (/api/v2/chat)
    participant STT as 🎙️ Groq Whisper Large v3 (STT)
    participant ChatService as 🧠 Chatbot Reasoning Engine
    participant GroqLLM as 🤖 Groq LLM (gpt-oss-20b / llama-3.3)
    participant TTS as 🔊 gTTS Audio Engine

    User->>UI: Clicks Microphone & Speaks in Regional Language
    UI->>VAD: Stream microphone audio & monitor RMS volume
    VAD->>VAD: Detect speech onset & wait for 1.6s pause
    VAD-->>UI: Automatically stops recording on silence
    UI->>API: POST /api/v2/chat/audio (Audio Blob + Active Telemetry + Target Lang)
    
    API->>STT: Transcribe audio with forced language parameter
    STT-->>API: Accurate native transcript (e.g., Telugu / Hindi)
    
    API->>ChatService: Assemble prompt (System Rules + Active Screen Data + 10-D Metrics)
    ChatService->>GroqLLM: Generate decisive, data-grounded response
    GroqLLM-->>ChatService: Return localized response & verified data sources
    
    ChatService->>TTS: Synthesize cleaned speech text to in-memory MP3
    TTS-->>API: Base64 Audio Data URL (data:audio/mp3;base64,...)
    
    API-->>UI: JSON { transcript, reply, audio_base64, latencies }
    UI->>User: Display message bubble + Auto-play spoken voice audio
```

---

## 3. Dual-Engine Execution & Separation of Concerns

```mermaid
flowchart LR
    classDef math fill:#ecfdf5,stroke:#059669,stroke-width:2px,color:#047857;
    classDef xai fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#b45309;
    classDef genai fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#5b21b6;

    subgraph DeterministicEngine ["Deterministic Mathematical Core (Zero Hallucination)"]
        direction TB
        M1["Debt Amortization with Moratorium"]
        M2["17-Scheme Matching & Ranking Matrix"]
        M3["RBI Prudential DSCR Calculation"]
        M4["MoSPI CPI Inflation-Adjusted Pricing"]
    end

    subgraph ExplainableMLEngine ["Explainable Machine Learning Engine (XAI)"]
        direction TB
        X1["Mission Antyodaya 613 Infrastructure Score"]
        X2["Census 2011 Catchment Demographics"]
        X3["10-D Supervised XGBoost Classifier"]
        X4["Lundberg TreeSHAP Shapley Attribution"]
    end

    subgraph GenerativeAdvisor ["Generative AI & Audio Layer"]
        direction TB
        G1["Multilingual Speech-to-Text (Whisper)"]
        G2["Context-Grounded Advisory (Groq LLM)"]
        G3["Text-to-Speech Audio Synthesis (gTTS)"]
        G4["Executive Feasibility Narrative Synthesizer"]
    end

    DeterministicEngine -->|Injects Financial Grounding| ExplainableMLEngine
    DeterministicEngine -->|Injects Auditable Figures| GenerativeAdvisor
    ExplainableMLEngine -->|Injects Viability & SHAP Factors| GenerativeAdvisor

    class M1,M2,M3,M4 math;
    class X1,X2,X3,X4 xai;
    class G1,G2,G3,G4 genai;
```

---

## 4. Multi-Project State Lifecycle & Auto-Reset

```mermaid
stateDiagram-v2
    [*] --> ProjectA_Active: User selects/creates Project A
    
    state ProjectA_Active {
        [*] --> Chat_InitA: Generate Welcome grounded in Project A
        Chat_InitA --> ChattingA: User queries Project A parameters
        ChattingA --> ChattingA: Q&A turns stored in Project A memory
    }

    ProjectA_Active --> Project_Switch: User switches to Project B (or creates new enterprise)
    
    state Project_Switch {
        Stop_Audio: Stop ongoing voice playback
        Clear_TTS: Clear pending audio synthesis jobs
        Flush_Context: Wipe prior conversation history to prevent context bleed
    }

    Projecwt_Switch --> ProjectB_Active: Fingerprint transition (activeProjectKey)

    state ProjectB_Active {
        [*] --> Chat_InitB: Generate fresh Welcome grounded in Project B
        Chat_InitB --> ChattingB: Fresh Q&A turns strictly isolated to Project B
    }
```
