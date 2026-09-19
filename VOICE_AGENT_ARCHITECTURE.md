# Udyam Saathi — Voice Agent ("POOJA") Complete Architecture & Implementation Manual

> **Purpose of this document**:  
> This file is the single, authoritative reference for the entire Voice Conversational Agent ("POOJA") in Udyam Saathi. When switching AI models or sessions, read this file to understand the voice pipeline without needing to inspect multiple files across the repository.

---

## 1. Executive Summary & Core Invariants

* **Agent Name**: **POOJA** (Proactive Online/Offline Judiciary & Appraisal Voice Co-Pilot)
* **Problem Solved**: Rural and semi-urban entrepreneurs often face low digital literacy, complex banking terminology, and language barriers when applying for institutional credit.
* **Core Function**: A voice-first, dialect-aware conversational co-pilot that:
  1. Listens to speech in **22 Scheduled Indian Languages**.
  2. Identifies spoken dialects in under 300ms.
  3. Transcribes using official sovereign speech models.
  4. Dispatches actionable UI mutations via structured tool-calling.
  5. Synthesizes voice responses using native Indic speech with zero math hallucination.

### Key Architectural Invariants
1. **Sovereign-First with Resilient Fallback**: Primary speech operations are handled by **Digital India BHASHINI** and **Sarvam AI**. If any government service is unreachable, it seamlessly fails over to **Groq Whisper Large v3** and **gTTS** without crashing the user session.
2. **Zero Financial Recalculation Invariant**: The LLM is **never** allowed to calculate financial formulas, interest rates, or DSCR ratios. All math is computed upstream in deterministic Python and injected as immutable grounding data.
3. **Direct TTS Fallback (No Double LLM)**: If primary TTS fails, fallback TTS (gTTS) synthesizes the *already generated* response directly without re-invoking the LLM, preventing double latency and token costs.
4. **Unified Voice Context**: Both voice entry points (the floating Siri-like Voice Orb and the Chat Mic) share the exact same message history, tool dispatching, and state machine in `ChatContext.jsx`.

---

## 2. Complete End-to-End Pipeline Architecture

```
                                  [ User Microphone ]
                                           │
                        WebM / WAV Audio Stream (Opus/PCM)
                                           │
                                           ▼
                     POST /api/chat/voice-agent (FastAPI)
                                           │
    ┌──────────────────────────────────────┴──────────────────────────────────────┐
    ▼                                                                             ▼
[PRIMARY SOVEREIGN TIER]                                              [RESILIENT FALLBACK TIER]
    │                                                                             │
 1. Language Identification (LID)                                                 │
    • Sarvam Saaras STT (`unknown`)                                               │
    • Discards transcript immediately;                                            │
      extracts 2-letter ISO code (hi, mr, etc.)                                   │
    • Fails? (Timeout/429) ───────────────────────────────────────────────────────┤
    │ Success                                                                     │
    ▼                                                                             │
 2. Speech-to-Text (ASR)                                                          │
    • Digital India BHASHINI (ULCA)                                               │
    • Transcribes in detected dialect                                             │
    • Fails? (Unsupported / 5xx) ─────────────────────────────────────────────────┤
    │ Success                                                                     │
    │                                                                  1. Whisper STT (Groq Cloud)
    │                                                                     • Whisper Large v3
    │                                                                     • Transcribes with language tag
    │                                                                     │
    │                                                                  2. Fallback Language Check
    │                                                                     • Supported (en, hi, mr, bn, etc.)?
    │                                                                     • If NO: Returns deterministic
    │                                                                       bilingual notice (Skips LLM!)
    └──────────────────────────────────────┬──────────────────────────────────────┘
                                           │
                                           ▼
                     3. GROUNDED REASONING & TOOL CALLING
                        • Engine: Groq GPT OSS 20B
                        • Ingests Active Screen Context (DSCR, Cost, Location)
                        • Evaluates ACTION_REGISTRY_SCHEMA (Tool Calling)
                        • Speech Sanitizer: Strips markdown, tables, asterisks, URLs
                                           │
    ┌──────────────────────────────────────┴──────────────────────────────────────┐
    ▼                                                                             ▼
 4a. Primary TTS (BHASHINI)                                           4b. Fallback TTS (gTTS)
     • Bhashini ULCA TTS                                                  • Google Text-to-Speech
     • Native Indic audio stream (WAV base64)                             • Direct MP3 stream
     • Fails? (Rate limit / 5xx) ─────────────────────────────────────────► (Zero LLM Re-Run!)
     │ Success                                                            │
     ▼                                                                    ▼
 `tier_used: "bhashini"`                                             `tier_used: "bhashini_asr_gtts_tts"`
                                                                      or `tier_used: "fallback"`
    └──────────────────────────────────────┬──────────────────────────────────────┘
                                           │
                                           ▼
                 JSON Response + Audio Base64 Data URL + Tool Call
                                           │
                                           ▼
                   Frontend `ChatContext.jsx` & Audio Player
                   • Dispatches UI Tool Call (e.g., Navigate, Switch Lang)
                   • Plays audio through HTML5 Audio (`voiceAgentAudioRef`)
                   • Updates Animated Orb (IDLE -> LISTENING -> THINKING -> SPEAKING)
```

---

## 3. Backend Architecture & File Map

All backend code resides in `c:\SIH2026\backend\app\`:

### 3.1. `app/core/audio_chat_service.py` (Core Voice Engine)
* **Role**: Central orchestrator for all voice-related operations.
* **Key Functions**:
  * `process_voice_turn_v2(audio_bytes, filename, context, history)`:  
    The primary V3 cascade: Sarvam LID $\rightarrow$ Bhashini ASR $\rightarrow$ Groq LLM + Tool Call $\rightarrow$ Bhashini TTS (with gTTS fallback).
  * `run_fallback_turn(audio_bytes, filename, context, history, overall_start)`:  
    Executes Groq Whisper Large v3 $\rightarrow$ Groq LLM $\rightarrow$ gTTS.
  * `text_to_speech_v2(text, language)`:  
    Async TTS endpoint handler. Tries Bhashini TTS first; falls back to gTTS.
  * `_clean_markdown_for_speech(text)`:  
    Regex sanitizer removing tables (`|`), markdown symbols (`*`, `#`, `_`), links, and citations so the TTS voice sounds natural.
  * `build_degraded_language_notice_response()`:  
    Deterministic fallback when an unsupported language is heard, skipping the LLM to avoid token burn.
* **Telemetry Counters**:
  * `bhashini_total`, `bhashini_asr_gtts_tts_total`, `fallback_total`, `bhashini_language_gap`, `voice_degraded_language_notice_total`.

### 3.2. `app/core/bhashini_client.py` (Digital India Speech Client)
* **Role**: Async HTTP client for MeitY's ULCA (Unified Language Contribution API).
* **Key Methods**:
  * `transcribe(audio_bytes, language_code)`: Sends audio to Bhashini ASR pipeline.
  * `synthesize(text, language_code)`: Sends text to Bhashini TTS pipeline (max 300 chars per chunk).
  * `_get_pipeline_config(task_type, language_code)`: Discovers and caches dynamic inference endpoints and API keys per language with in-memory TTL.
  * `prewarm_cache(languages)`: Pre-fetches pipeline configurations on backend startup.
* **Custom Exceptions**:
  * `BhashiniLanguageUnsupportedError`, `BhashiniUnavailableError`.

### 3.3. `app/core/sarvam_client.py` (Indic Language Detection)
* **Role**: Calls Sarvam AI’s Saaras model exclusively for sub-300ms Language Identification (LID).
* **Key Methods**:
  * `detect_language(audio_bytes, audio_format)`: Sends audio with `language_code="unknown"`. Returns 2-letter ISO code (`hi`, `mr`, `ta`, etc.).
  * **Invariant**: The transcript returned by Sarvam is unconditionally discarded.
* **Custom Exceptions**:
  * `SarvamDetectionError`, `SarvamUnavailableError`.

### 3.4. `app/core/chat_service.py` (LLM Reasoning & Grounding)
* **Role**: Generates contextual responses with system prompts and tool schemas.
* **Key Methods**:
  * `generate_grounded_reply(transcript, language, screen_context, tools)`:  
    Uses Groq gpt oss 20b with `VOICE_TOOL_CALLING_PROMPT` and `ACTION_REGISTRY_SCHEMA`. Returns `LLMReplyResult` with text, sources, and `tool_call`.
  * `generate_chat_response(messages, context, language)`:  
    Multi-turn chat handler, also equipped with tool-calling capabilities.

### 3.5. `app/core/action_registry.py` (Voice-to-Action Tool Schemas)
* **Role**: Defines JSON Schema tools passed to Groq for voice-controlled UI actions.
* **Registered Tools**:
  * `NAVIGATE_TAB`: `{ "tab": "overview" | "viability" | "financials" | "schemes" | "risk" | "dpr" }`
  * `SWITCH_LANGUAGE`: `{ "language": "hi" | "en" | "mr" | "ta" | "te" | "kn" }`
  * `RECALCULATE_LOAN`: `{ "amount": number, "tenure": number }`
  * `OPEN_MODAL`: `{ "modal_name": "dpr" | "calculator" }`

### 3.6. `app/routers/chat.py` (FastAPI Endpoints)
* **`POST /api/chat/voice-agent`**: Multipart audio upload endpoint (`file`, `context`, `history`). Calls `audio_chat_service.process_voice_agent_audio()`.
* **`POST /api/chat/tts`**: Accepts `{ "text": "...", "language": "hi" }`. Calls `text_to_speech_v2()`.
* **`POST /api/chat/message`**: Text-based chat endpoint with tool-calling support.
* **`GET /api/chat/languages`**: Returns list of supported languages and active engines.

---

## 4. Frontend Architecture & File Map

All frontend code resides in `c:\SIH2026\frontend\src\`:

### 4.1. `context/ChatContext.jsx` (Unified Voice State Machine)
* **State Variables**:
  * `voiceAgentState`: `'IDLE'` | `'LISTENING'` | `'THINKING'` | `'SPEAKING'`
  * `messages`: Array of chat messages (shared between Chat and Voice Agent).
  * `activeToolCall`: Latest tool call executed by the voice assistant.
* **Core Functions**:
  * `sendVoiceAgentAudio(audioBlob)`: Packages audio, sends to `/api/chat/voice-agent`, adds user message with `source: 'siri'`, handles audio playback, and calls `dispatchToolCall()`.
  * `sendVoiceAgentQuery(text)`: For wake-word text queries or typed voice input.
  * `dispatchToolCall(toolCall)`: Intercepts tool calls and executes them (e.g., changes tabs, updates language, opens DPR modal).

### 4.2. `hooks/useVoiceRecorder.js` (Microphone Hardware Hook)
* **Role**: Manages browser `MediaRecorder` and `AudioContext`.
* **Features**:
  * Captures audio in `audio/webm;codecs=opus` or `audio/wav`.
  * Real-time audio waveform volume monitoring (`volumeLevel`).
  * Max duration safeguards and error handling for microphone permissions.

### 4.3. `components/Chat/VoiceAgentWindow.jsx` (Siri-like Voice Widget)
* **Role**: The floating, interactive circular voice orb.
* **Features**:
  * Animated pulsing gradient orb reflecting state (`LISTENING` = orange glow, `THINKING` = indigo pulse, `SPEAKING` = cyan soundwave).
  * Vernacular language indicator badge (shows detected language).
  * Live audio visualizer canvas and quick-cancel controls.

### 4.4. `components/Chat/FloatingChatWindow.jsx` (Traditional Chat Interface)
* **Role**: Expanding slide-out drawer for text and voice chat.
* **Features**:
  * Mic button in the input bar that streams into the shared `ChatContext`.
  * Renders markdown responses, sources, and action confirmation badges.

---

## 5. Configuration & Environment Variables (`.env`)

```env
# Groq Cloud (LLM & Whisper Fallback)
GROQ_API_KEY=gsk_...
GROQ_MODEL=gptoss20b
GROQ_STT_MODEL=whisper-large-v3

# Digital India BHASHINI (MeitY ULCA)
BHASHINI_USER_ID=...
BHASHINI_API_KEY=...
BHASHINI_PIPELINE_ID=...
BHASHINI_INFERENCE_URL=https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline

# Sarvam AI (Language Detection LID)
SARVAM_API_KEY=...
SARVAM_MODEL=saaras:v3
SARVAM_STT_URL=https://api.sarvam.ai/speech-to-text

# Fallback Settings
VOICE_FALLBACK_SUPPORTED_LANGS=en,hi,mr,bn,gu,ta,te,kn,pa,ur
```

---

## 6. How to Test & Verify

### 6.1. Automated Unit Tests
Run backend tests using pytest:
```powershell
pytest tests/test_audio_chat_service.py -v
pytest tests/test_wake_word.py -v
```

### 6.2. Manual Verification Steps
1. **Voice Turn**: Click the floating Siri Orb, speak in Hindi: *"Mera loan amount 5 lakh hai, subsidy batao"*.
2. **Verify Tool Call**: Speak: *"Financials tab par jao"*. Observe UI switching to `/report/financials`.
3. **Verify Fallback**: Simulate network drop or disable Bhashini key. Confirm voice responds via Whisper + gTTS without throwing an error.

---
*Generated for SIH 2026 — Team Recursive Rebels.*
