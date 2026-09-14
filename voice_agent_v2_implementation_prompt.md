# 🎙️ Udyam Saathi — Voice Agent V2 Implementation Prompt

> **For**: Coding agent with write access to the Udyam Saathi repository.
> **Context**: This is a consolidated, confirmed-direction implementation spec. Do not re-litigate architectural choices below — they were decided in a prior architecture review. Implement fully; no partial implementations that leave the existing voice pipeline in a broken intermediate state.

---

## 0. What changed and why (context for the implementing agent)

The current voice pipeline (`Groq Whisper Large v3` STT → `Groq Llama 3.3 70B` LLM → `gTTS` TTS) has two problems being fixed here:

1. **Language coverage**: Whisper's reliable Indic-language accuracy covers a subset of India's 22 official languages. We are adding **Sarvam AI** (Saaras for ASR, Bulbul v3 for TTS) as the **primary** speech layer, which natively covers all 22.
2. **Groq model availability**: `llama-3.3-70b-versatile` was moved to enterprise-only pricing on Groq (Aug 26, 2026) and is no longer purchasable via self-serve API. **Replace all self-serve Groq LLM calls with `openai/gpt-oss-120b`** (Groq's current flagship self-serve model, supports native tool-calling). Verify this against your live Groq account/dashboard before assuming it's still accurate — Groq's self-serve lineup can change again.

The existing Whisper+gTTS pipeline is **kept, unchanged, as the fallback tier** — no rework needed there beyond wiring it into the new cascade controller.

This spec also adds a **third capability**: voice-driven UI control (tab navigation, dashboard language switching) via LLM tool-calling, layered onto the existing single-call synthesis architecture — this does NOT add a second LLM call.

---

## 1. Architectural Invariants (unchanged from platform-wide rules)

- Zero LLM involvement in financial math — this spec touches none of that; Tier 1/Tier 2 (deterministic financial core, XGBoost) are untouched.
- Still exactly **one LLM call per conversational turn** (now with a `tools` parameter attached — this does not become two calls).
- Zero-crash guarantee: every external dependency (Sarvam ASR, Sarvam TTS, Groq) must degrade gracefully, never throw an unhandled exception to the user.
- Pydantic v2 `model_dump(mode="json")` for all JSONB persistence — unchanged.

---

## 2. New Environment Variables

```bash
SARVAM_API_KEY=<subscription key from Sarvam AI dashboard>
SARVAM_ASR_ENDPOINT=https://api.sarvam.ai/speech-to-text
SARVAM_TTS_ENDPOINT=https://api.sarvam.ai/text-to-speech
GROQ_LLM_MODEL=openai/gpt-oss-120b   # replaces llama-3.3-70b-versatile
VOICE_CASCADE_TIMEOUT_MS=4000        # max wait before falling back from Sarvam to Whisper+gTTS
VOICE_FALLBACK_SUPPORTED_LANGS=en,hi,mr,bn,gu,ta,te,kn,pa,ur
```

Add all of these to `.env.example` and to whatever secrets manager the deployment uses. **Never commit real values** (per existing audit note on committed DB credentials — do not repeat that mistake here).

---

## 3. Backend Changes

### 3.1 New file: `backend/app/core/sarvam_client.py`

Responsibilities:
- `async def transcribe(audio_bytes: bytes, audio_format: str) -> SarvamASRResult`
  - Calls Sarvam Saaras STT endpoint (simple request/response mode — NOT the WebSocket streaming API for this iteration).
  - **Do not pass a source language hint.** Let Sarvam auto-detect. Response must surface `detected_language_code` (BCP-47 style, e.g. `hi-IN`, `ta-IN`) and `transcript`.
  - Timeout at `VOICE_CASCADE_TIMEOUT_MS`; raise a typed `SarvamUnavailableError` on timeout, non-2xx, or malformed response — do not let raw HTTP exceptions propagate.
- `async def synthesize(text: str, language_code: str) -> bytes` (returns audio bytes, base64-encode at the router layer, matching current `audio_chat_service.py` conventions)
  - Calls Sarvam Bulbul v3/v4 TTS endpoint with the **same detected language code** from the ASR step (round-trip consistency — never translate or default the reply to a different language than the user spoke, except in the explicit degraded-mode case in 3.3).
  - Cap outbound text length defensively (~300 characters / ~80 words) before synthesis — this is both a UX improvement (nobody wants a 150-word spoken answer) and the dominant cost lever, since TTS is priced per character.
  - Same timeout/error-wrapping pattern as above.

Write proper Pydantic models for `SarvamASRResult` and any TTS response wrapper. Include retries with exponential backoff (max 1 retry) for transient 5xx only — not for auth failures (fail fast on 401/403 and surface a clear log line, since that's a config problem, not a transient one).

### 3.2 Modify: `backend/app/core/audio_chat_service.py`

Implement the **cascade controller**:

```
async def process_voice_turn(audio_bytes, screen_context) -> VoiceTurnResult:
    try:
        asr_result = await sarvam_client.transcribe(audio_bytes, ...)
        detected_lang = asr_result.detected_language_code
        used_tier = "sarvam"
    except SarvamUnavailableError:
        whisper_result = await groq_whisper_transcribe(audio_bytes)  # existing function, unchanged
        detected_lang = whisper_result.detected_language_code
        used_tier = "fallback"

        if normalize_lang(detected_lang) not in settings.VOICE_FALLBACK_SUPPORTED_LANGS:
            return build_degraded_language_notice_response()  # see 3.3 below — short-circuits, skips LLM call entirely
    
    llm_response = await chat_service.generate_grounded_reply(
        transcript=asr_result.transcript or whisper_result.transcript,
        language=detected_lang,
        screen_context=screen_context,
        tools=ACTION_REGISTRY_SCHEMA,   # see section 4
    )

    if used_tier == "sarvam":
        audio_out = await sarvam_client.synthesize(llm_response.text, detected_lang)
    else:
        audio_out = await gtts_synthesize(llm_response.text, normalize_lang(detected_lang))  # existing function, unchanged

    return VoiceTurnResult(
        transcript=..., reply_text=llm_response.text, audio_base64=..., 
        detected_language=detected_lang, tier_used=used_tier, 
        tool_call=llm_response.tool_call,  # None if plain answer
    )
```

Key requirements:
- `used_tier` MUST be included in the API response and logged — you need this telemetry to know how often the fallback is actually engaged (this is also a legitimate SIH jury talking point: "here's our real fallback-engagement rate").
- The degraded-language-notice path (3.3) must **skip the LLM call entirely** — don't waste a Groq call on a request you already know you can't properly answer.

### 3.3 New function: `build_degraded_language_notice_response()`

Returns a fixed (non-LLM-generated, fully deterministic) response:
- Text: bilingual English + Hindi notice listing the exact contents of `VOICE_FALLBACK_SUPPORTED_LANGS`, translated to friendly language names, e.g.:
  > "Voice support for this language isn't available right now. I can currently help you in: English, Hindi, Marathi, Bengali, Gujarati, Tamil, Telugu, Kannada, Punjabi, Urdu. Please try one of these, or type your question. / अभी इस भाषा में आवाज़ सहायता उपलब्ध नहीं है। मैं फिलहाल इन भाषाओं में मदद कर सकता हूँ: अंग्रेज़ी, हिंदी, मराठी, बंगाली, गुजराती, तमिल, तेलुगु, कन्नड़, पंजाबी, उर्दू। कृपया इनमें से कोई एक आज़माएँ, या टाइप करके पूछें।"
- Audio: synthesize the **Hindi portion** via gTTS (`hi`), since Hindi is the highest-likelihood shared language across your target users when the input language is unrecognized.
- `tool_call: None` always for this path.
- Log this event under a distinct counter (e.g. `voice_degraded_language_notice_total`) separate from generic fallback engagement — you want to know specifically how often real users hit a language gap, not just how often Sarvam was down.

### 3.4 New file: `backend/app/core/action_registry.py`

Single source of truth for voice-triggerable UI actions, shared between the Groq tool-calling schema and (via the API response) the frontend dispatcher.

```python
ACTION_REGISTRY_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to_tab",
            "description": "Switch the user's dashboard view to a different section/tab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tab": {
                        "type": "string",
                        "enum": ["business_plan", "govt_schemes", "dashboard", "dpr", "risk_analysis"]
                    }
                },
                "required": ["tab"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "change_language",
            "description": "Change the dashboard's displayed UI language (text/labels), independent of the voice agent's spoken language which is auto-detected per turn.",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {"type": "string", "enum": ["en", "hi", "mr", "ta", "te", "kn"]}
                },
                "required": ["language"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_analysis",
            "description": "Re-run the feasibility analysis pipeline for the current project.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_dpr",
            "description": "Trigger the bank-ready DPR export/download flow.",
            "parameters": {"type": "object", "properties": {"format": {"type": "string", "enum": ["pdf"]}}}
        }
    }
]
```

**Critical note**: `change_language`'s enum is deliberately limited to the dashboard's existing supported UI languages (whatever `LanguageContext.jsx` currently supports for text/labels) — this is NOT the same list as the voice agent's 22-language auto-detected speech capability. Do not conflate these two. The voice agent hears/speaks far more languages than the dashboard can render text in.

### 3.5 Modify: `backend/app/core/chat_service.py`

- Accept `tools=ACTION_REGISTRY_SCHEMA` in the Groq API call.
- Update the system prompt to explicitly state: (a) the current tab/screen the user is on (already partially done via existing telemetry grounding), (b) that the model should call `navigate_to_tab` when the user expresses navigation intent in ANY detected language, not just English phrasing — the model reasons over transcript meaning, so this should work out-of-the-box, but add 2-3 explicit examples in the system prompt covering Hindi/Marathi phrasing to reduce ambiguity.
- Parse `response.choices[0].message.tool_calls` — if present, extract `name` + `arguments` (JSON) and attach to the returned `llm_response.tool_call`. If the model returns both accompanying text AND a tool call, keep both (text becomes the spoken confirmation).
- If Groq returns a tool call for `navigate_to_tab` or `change_language`, the accompanying spoken confirmation text should be generated by the model itself in the same call (prompt it to always include a short natural-language confirmation alongside any tool call) — do not hardcode confirmation strings in the backend, since they need to be in the detected language.

### 3.6 Modify: `backend/app/routers/chat.py`

- `POST /api/v2/chat/audio` response model gains two new fields: `detected_language: str`, `tier_used: Literal["sarvam", "fallback"]`, `tool_call: Optional[ToolCallModel]`.
- No new endpoints needed — this is all additive to the existing contract.

---

## 4. Frontend Changes

### 4.1 Modify: `ChatContext.jsx`

Add an action dispatcher:

```js
const actionDispatchers = {
  navigate_to_tab: ({ tab }) => router.push(tabRoutes[tab]),      // adapt to actual routing (Vite React Router per current codebase, NOT Next.js — see repo-truth note below)
  change_language: ({ language }) => setLanguage(language),        // existing LanguageContext setter
  run_analysis: () => triggerAnalysisRun(),                        // existing analysis trigger, if present, else stub with TODO
  export_dpr: ({ format }) => triggerDprExport(format),            // existing export flow
};

function handleVoiceTurnResponse(response) {
  if (response.tool_call) {
    actionDispatchers[response.tool_call.name]?.(response.tool_call.arguments);
  }
  // regardless of tool_call presence, always play the spoken confirmation/answer
  playAudio(response.audio_base64);
}
```

> **Repo-truth reminder**: per prior audit, the actual frontend is **Vite + React**, not Next.js, despite what older docs claim. Use whatever routing library is actually installed (check `package.json` — likely `react-router-dom`) — do not assume `next/router`.

### 4.2 Modify: `api.js` (`chatApi.sendVoiceAudio`)

- Remove any manual language parameter from the request payload — the backend now always auto-detects. If a `language` param currently exists in this call, delete it; do not deprecate silently, actually remove it so no stale value can be sent by mistake.
- Add handling for the new response fields (`detected_language`, `tier_used`, `tool_call`) in the response type/interface.

### 4.3 No changes needed to `useVoiceRecorder.js` or `useWakeWord.js`

These are unaffected by this spec — wake-word detection and audio capture are unchanged. Do not touch them.

---

## 5. Explicitly Out of Scope for This Implementation Pass

- Sarvam WebSocket streaming ASR (deferred — simple request/response only, for this iteration).
- Self-hosted AI4Bharat models (deferred — current fallback remains Groq Whisper + gTTS).
- Bhashini integration (not being built; mentioned only as a possible future/pitch-narrative addition).
- Any change to Tier 1 (deterministic financial engine) or Tier 2 (XGBoost) — untouched by this spec.

Do not scope-creep into any of the above.

---

## 6. Mandatory Testing Gate (required before this task is reported complete)

1. **Build output**: full backend build/typecheck output, full frontend build output (no errors/warnings introduced).
2. **Endpoint table**: confirm `POST /api/v2/chat/audio` request/response shape matches section 3.6, tested with at least:
   - A Sarvam-available happy path in at least 3 different languages (e.g. Hindi, Tamil, Marathi) — confirm `tier_used: "sarvam"` and correct language round-trip (input language == output language).
   - A forced-Sarvam-failure path (mock/kill the Sarvam client) confirming graceful fallback to Whisper+gTTS with `tier_used: "fallback"`.
   - A forced-Sarvam-failure + unsupported-language path confirming the degraded-language-notice response fires and skips the LLM call (assert via mock call-count that `chat_service.generate_grounded_reply` was NOT invoked in this case).
   - At least one voice command per action type (`navigate_to_tab`, `change_language`, `run_analysis`, `export_dpr`) confirming the correct tool call is returned and the frontend dispatcher fires the right handler.
3. **Full test harness output** (`run_tests.py` or equivalent) — zero regressions in existing voice pipeline tests.
4. **Commit to current branch** with a clear commit message referencing this spec.

Do not report this task complete without all four items in this section actually executed and their output included in the completion report.
