"""
test_voice_agent_v3.py — Comprehensive Test Suite for Voice Agent V3.

Supersedes V2 test suite. Validates the V3 architecture:
  1. Gate 1: Empirical response field check for Sarvam detection (extract_language_code_from_response).
  2. Gate 2: Bhashini language coverage check against 22 languages and gap list determination.
  3. Gate 3: End-to-end happy path across 3 Indic languages (Hindi, Tamil, Marathi) with tier_used: "bhashini".
  4. Gate 4: Forced Bhashini TTS failure -> fallback to gTTS directly without re-invoking LLM (tier_used: "bhashini_asr_gtts_tts", LLM call count == 1).
  5. Gate 5: Forced Sarvam detection failure -> full fallback to Whisper+gTTS (tier_used: "fallback").
  6. Gate 6: Forced Bhashini language gap -> increments bhashini_language_gap telemetry and executes fallback turn.
  7. Gate 7: Zero regressions across API endpoints (/api/v2/chat/audio, /api/v2/chat/health).
"""

from __future__ import annotations
import io
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

# Ensure root paths are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from backend.app.main import app
from backend.app.config import settings
from backend.app.core.action_registry import ACTION_REGISTRY_SCHEMA, ACTION_NAMES
from backend.app.core import sarvam_client
from backend.app.core.sarvam_client import (
    extract_language_code_from_response,
    SarvamDetectionError,
    SarvamUnavailableError,
)
from backend.app.core import bhashini_client
from backend.app.core.bhashini_client import (
    BhashiniClient,
    BhashiniLanguageUnsupportedError,
    BhashiniUnavailableError,
    normalize_bhashini_lang,
)
from backend.app.core import audio_chat_service as acs_mod
from backend.app.core.audio_chat_service import (
    audio_chat_service,
    build_degraded_language_notice_response,
    normalize_lang,
    _telemetry,
)
from backend.app.core.chat_service import LLMReplyResult

client = TestClient(app)


# ---------------------------------------------------------------------------
# Gate 1: Empirical Response Field Check for Sarvam Detection
# ---------------------------------------------------------------------------

def test_gate1_sarvam_extract_language_code_conventions():
    """
    Verify extract_language_code_from_response accurately handles all known
    and defensive field conventions, while discarding any transcript field.
    """
    # 1. Standard documented field
    assert extract_language_code_from_response({"language_code": "hi-IN", "transcript": "नमस्ते"}) == "hi-IN"
    
    # 2. Alternative field: source_language_code
    assert extract_language_code_from_response({"source_language_code": "ta-IN", "transcript": "வணக்கம்"}) == "ta-IN"
    
    # 3. Alternative field: detected_language_code
    assert extract_language_code_from_response({"detected_language_code": "mr-IN", "transcript": "नमस्कार"}) == "mr-IN"
    
    # 4. Alternative field: detected_language
    assert extract_language_code_from_response({"detected_language": "te-IN", "text": "హలో"}) == "te-IN"
    
    # 5. Fallback field: language
    assert extract_language_code_from_response({"language": "kn-IN", "transcript": "ನಮಸ್ಕಾರ"}) == "kn-IN"

    # 6. Malformed, empty, or missing values
    assert extract_language_code_from_response({}) is None
    assert extract_language_code_from_response({"transcript": "no language here"}) is None
    assert extract_language_code_from_response({"language_code": "   "}) is None
    assert extract_language_code_from_response(None) is None
    assert extract_language_code_from_response("invalid-string") is None


# ---------------------------------------------------------------------------
# Gate 2: Bhashini Language Coverage Check & Gap Determination
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate2_bhashini_coverage_and_gap_handling():
    """
    Test Bhashini pipeline config resolution behavior across Indic languages.
    Unsupported languages must raise BhashiniLanguageUnsupportedError.
    """
    client_test = BhashiniClient()

    # Simulate discovery endpoint returning ASR pipeline covering 12 languages
    supported_12 = ["as", "bn", "en", "gu", "hi", "kn", "ml", "mr", "or", "pa", "ta", "te"]
    
    mock_pipeline_response = {
        "pipelineResponseConfig": [
            {
                "taskType": "asr",
                "config": [
                    {
                        "serviceId": f"ai4bharat/conformer-{lang}",
                        "language": {"sourceLanguage": lang},
                    }
                    for lang in supported_12
                ],
            }
        ],
        "pipelineInferenceAPIEndPoint": {
            "callbackUrl": "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
            "inferenceApiKey": {
                "name": "Authorization",
                "value": "mock_inference_key_xyz",
            },
        },
    }

    with patch.object(client_test, "_get_credentials", return_value=("mock_user", "mock_key")), \
         patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_pipeline_response
        mock_post.return_value = mock_resp

        # Test supported language (Hindi)
        cfg_hi = await client_test._get_config("asr", "hi")
        assert cfg_hi["serviceId"] == "ai4bharat/conformer-hi"
        assert cfg_hi["callback_url"] == "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
        assert cfg_hi["inference_key"] == "mock_inference_key_xyz"

        # Test another supported language (Tamil)
        cfg_ta = await client_test._get_config("asr", "ta")
        assert cfg_ta["serviceId"] == "ai4bharat/conformer-ta"

        # Test unsupported language in this pipeline (e.g. Santali 'sat' or Dogri 'doi')
        with pytest.raises(BhashiniLanguageUnsupportedError) as exc_info:
            await client_test._get_config("asr", "sat")
        assert "not supported" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Gate 3: End-to-End Happy Path in 3 Indic Languages (Hindi, Tamil, Marathi)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("lang_detect,norm_code,transcript,sample_reply", [
    ("hi-IN", "hi", "मुझे एमएसएमई योजनाएं दिखाओ", "यहाँ आपके लिए उपयुक्त एमएसएमई योजनाएं हैं।"),
    ("ta-IN", "ta", "திட்டங்களை காட்டு", "உங்களுக்கான அரசு திட்டங்கள் இங்கே உள்ளன."),
    ("mr-IN", "mr", "शासकीय योजना दाखवा", "येथे आपल्या व्यवसायासाठी शासकीय योजना आहेत."),
])
async def test_gate3_happy_path_3_languages(lang_detect, norm_code, transcript, sample_reply):
    """
    Test full happy path:
      1. Sarvam detect_language returns lang_detect.
      2. Bhashini transcribe returns transcript in detected language.
      3. Groq LLM generates reply.
      4. Bhashini synthesize returns audio bytes.
      Asserts tier_used: 'bhashini', telemetry increments bhashini_total.
    """
    fake_audio = b"\x00\x01\x02\x03" * 50
    initial_bhashini_total = _telemetry["bhashini_total"]

    mock_detect = AsyncMock(return_value=lang_detect)
    mock_transcribe = AsyncMock(return_value=transcript)
    mock_synthesize = AsyncMock(return_value=b"RIFF_WAV_HEADER_DATA_STREAM")
    mock_llm = MagicMock(return_value=LLMReplyResult(
        text=sample_reply,
        tool_call=None,
        model="openai/gpt-oss-20b",
        latency_ms=250.0,
        sources=["Schemes Engine"],
    ))

    with patch.object(acs_mod.sarvam_client, "detect_language", mock_detect), \
         patch.object(acs_mod.bhashini_client, "transcribe", mock_transcribe), \
         patch.object(acs_mod.bhashini_client, "synthesize", mock_synthesize), \
         patch.object(acs_mod.chat_service, "generate_grounded_reply", mock_llm):

        turn = await audio_chat_service.process_voice_turn_v2(
            audio_bytes=fake_audio,
            context={"currentTab": "schemes"},
        )

        assert turn["tier_used"] == "bhashini"
        assert turn["detected_language"] == lang_detect
        assert turn["language"] == norm_code
        assert turn["user_transcript"] == transcript
        assert turn["reply"] == sample_reply
        assert turn["audio_base64"].startswith("data:audio/wav;base64,")
        assert _telemetry["bhashini_total"] == initial_bhashini_total + 1

        mock_detect.assert_awaited_once_with(fake_audio, audio_format="wav")
        mock_transcribe.assert_awaited_once_with(fake_audio, language_code=lang_detect)
        mock_synthesize.assert_awaited_once()


# ---------------------------------------------------------------------------
# Gate 4: Forced Bhashini TTS Failure -> gTTS Fallback Without Re-invoking LLM
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate4_forced_bhashini_tts_failure_exact_1_llm_call():
    """
    If Bhashini TTS fails, synthesize via gTTS directly without re-invoking Groq LLM.
    Asserts:
      - tier_used: 'bhashini_asr_gtts_tts'
      - telemetry 'bhashini_asr_gtts_tts_total' increments
      - LLM call count == 1 (INVARIANT: LLM is never called a second time)
    """
    fake_audio = b"\x00\x01\x02\x03" * 50
    initial_tts_fallback_total = _telemetry["bhashini_asr_gtts_tts_total"]

    mock_detect = AsyncMock(return_value="hi-IN")
    mock_transcribe = AsyncMock(return_value="लोन की जानकारी दें")
    mock_synthesize = AsyncMock(side_effect=BhashiniUnavailableError("Bhashini TTS 503 Service Unavailable"))
    mock_llm = MagicMock(return_value=LLMReplyResult(
        text="यहाँ मुद्रा ऋण की जानकारी है।",
        tool_call=None,
        model="openai/gpt-oss-20b",
        latency_ms=200.0,
        sources=[],
    ))
    mock_gtts = MagicMock(return_value={
        "audio_base64": "data:audio/mp3;base64,GTTS_FALLBACK_AUDIO_STREAM",
        "language": "hi",
        "language_name": "Hindi",
        "latency_s": 0.15,
    })

    with patch.object(acs_mod.sarvam_client, "detect_language", mock_detect), \
         patch.object(acs_mod.bhashini_client, "transcribe", mock_transcribe), \
         patch.object(acs_mod.bhashini_client, "synthesize", mock_synthesize), \
         patch.object(acs_mod.chat_service, "generate_grounded_reply", mock_llm), \
         patch.object(audio_chat_service, "text_to_speech", mock_gtts):

        turn = await audio_chat_service.process_voice_turn_v2(audio_bytes=fake_audio)

        assert turn["tier_used"] == "bhashini_asr_gtts_tts"
        assert turn["detected_language"] == "hi-IN"
        assert turn["reply"] == "यहाँ मुद्रा ऋण की जानकारी है।"
        assert turn["audio_base64"] == "data:audio/mp3;base64,GTTS_FALLBACK_AUDIO_STREAM"
        assert _telemetry["bhashini_asr_gtts_tts_total"] == initial_tts_fallback_total + 1

        # CRITICAL INVARIANT: Groq LLM was invoked EXACTLY ONCE
        mock_llm.assert_called_once()
        mock_gtts.assert_called_once()


# ---------------------------------------------------------------------------
# Gate 5: Forced Sarvam Detection Failure -> Full Fallback (Whisper + gTTS)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate5_forced_sarvam_detection_failure_fallback():
    """
    When Sarvam language detection fails (e.g. timeout, network error),
    controller routes to run_fallback_turn (Whisper STT + Groq LLM + gTTS).
    Asserts:
      - tier_used: 'fallback'
      - telemetry 'fallback_total' increments
    """
    fake_audio = b"\x00\x01\x02\x03" * 50
    initial_fallback_total = _telemetry["fallback_total"]

    mock_detect = AsyncMock(side_effect=SarvamDetectionError("Sarvam detection timed out after 4000ms"))
    mock_whisper = MagicMock(return_value={
        "transcript": "व्यवसाय ऋण कैसे मिलेगा",
        "language": "hi",
        "detected_language_code": "hi",
        "language_name": "Hindi",
        "latency_s": 0.45,
    })
    mock_llm = MagicMock(return_value=LLMReplyResult(
        text="व्यवसाय ऋण के लिए आप पीएमएमवाई में आवेदन कर सकते हैं।",
        tool_call=None,
        model="openai/gpt-oss-20b",
        latency_ms=280.0,
        sources=[],
    ))
    mock_gtts = MagicMock(return_value={
        "audio_base64": "data:audio/mp3;base64,FALLBACK_GTTS_AUDIO",
        "language": "hi",
        "language_name": "Hindi",
        "latency_s": 0.12,
    })

    with patch.object(acs_mod.sarvam_client, "detect_language", mock_detect), \
         patch.object(audio_chat_service, "transcribe_audio", mock_whisper), \
         patch.object(acs_mod.chat_service, "generate_grounded_reply", mock_llm), \
         patch.object(audio_chat_service, "text_to_speech", mock_gtts):

        turn = await audio_chat_service.process_voice_turn_v2(audio_bytes=fake_audio)

        assert turn["tier_used"] == "fallback"
        assert turn["user_transcript"] == "व्यवसाय ऋण कैसे मिलेगा"
        assert turn["reply"] == "व्यवसाय ऋण के लिए आप पीएमएमवाई में आवेदन कर सकते हैं।"
        assert turn["audio_base64"] == "data:audio/mp3;base64,FALLBACK_GTTS_AUDIO"
        assert _telemetry["fallback_total"] == initial_fallback_total + 1

        mock_whisper.assert_called_once()
        mock_llm.assert_called_once()
        mock_gtts.assert_called_once()


# ---------------------------------------------------------------------------
# Gate 6: Forced Bhashini Language Gap -> Telemetry Increments & Fallback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate6_forced_bhashini_language_gap():
    """
    When Sarvam detects a language that Bhashini ASR does not support:
      - Bhashini ASR raises BhashiniLanguageUnsupportedError
      - Controller increments _telemetry['bhashini_language_gap']
      - Controller routes to run_fallback_turn
    """
    fake_audio = b"\x00\x01\x02\x03" * 50
    initial_gap_count = _telemetry["bhashini_language_gap"]
    initial_fallback_total = _telemetry["fallback_total"]

    # Sarvam detects a language code e.g. 'doi-IN' (Dogri)
    mock_detect = AsyncMock(return_value="doi-IN")
    mock_transcribe = AsyncMock(
        side_effect=BhashiniLanguageUnsupportedError("Language 'doi' is not supported by Bhashini ASR pipeline")
    )
    mock_whisper = MagicMock(return_value={
        "transcript": "Dogri speech transcribed by Whisper",
        "language": "hi",  # Whisper fallback detected/hinted
        "detected_language_code": "hi",
        "language_name": "Hindi",
        "latency_s": 0.4,
    })
    mock_llm = MagicMock(return_value=LLMReplyResult(
        text="Fallback reply generated.",
        tool_call=None,
        model="openai/gpt-oss-20b",
        latency_ms=180.0,
        sources=[],
    ))
    mock_gtts = MagicMock(return_value={
        "audio_base64": "data:audio/mp3;base64,GTTS_DATA",
        "language": "hi",
        "language_name": "Hindi",
        "latency_s": 0.1,
    })

    with patch.object(acs_mod.sarvam_client, "detect_language", mock_detect), \
         patch.object(acs_mod.bhashini_client, "transcribe", mock_transcribe), \
         patch.object(audio_chat_service, "transcribe_audio", mock_whisper), \
         patch.object(acs_mod.chat_service, "generate_grounded_reply", mock_llm), \
         patch.object(audio_chat_service, "text_to_speech", mock_gtts):

        turn = await audio_chat_service.process_voice_turn_v2(audio_bytes=fake_audio)

        # Assert telemetry was incremented for Bhashini language gap
        assert _telemetry["bhashini_language_gap"] == initial_gap_count + 1
        assert _telemetry["fallback_total"] == initial_fallback_total + 1
        assert turn["tier_used"] == "fallback"


# ---------------------------------------------------------------------------
# Gate 7: API Endpoints & Zero Regressions
# ---------------------------------------------------------------------------

def test_gate7_chat_health_endpoint():
    """
    Test GET /api/v2/chat/health reports Bhashini and Sarvam status,
    correct voice_tier, and full V3 telemetry counters.
    """
    response = client.get("/api/v2/chat/health")
    assert response.status_code == 200
    data = response.json()

    assert "sarvam_configured" in data
    assert "bhashini_configured" in data
    assert "voice_tier" in data
    assert "telemetry" in data

    telemetry = data["telemetry"]
    assert "bhashini_total" in telemetry
    assert "bhashini_asr_gtts_tts_total" in telemetry
    assert "fallback_total" in telemetry
    assert "bhashini_language_gap" in telemetry
    assert "voice_degraded_language_notice_total" in telemetry


@pytest.mark.asyncio
async def test_gate7_voice_chat_api_endpoint():
    """
    Test POST /api/v2/chat/audio end-to-end endpoint with mocked V3 services.
    Verifies response model structure adheres to VoiceChatResponse.
    """
    fake_audio_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00" + b"\x00" * 50

    mock_detect = AsyncMock(return_value="hi-IN")
    mock_transcribe = AsyncMock(return_value="डीपीआर कैसे डाउनलोड करें?")
    mock_synthesize = AsyncMock(return_value=b"SYNTHESIZED_WAV_BYTES")
    mock_llm = MagicMock(return_value=LLMReplyResult(
        text="डीपीआर डाउनलोड करने के लिए एक्सपोर्ट बटन दबाएं।",
        tool_call={"name": "export_dpr", "arguments": {"format": "pdf"}},
        model="openai/gpt-oss-20b",
        latency_ms=210.0,
        sources=["DPR Engine"],
    ))

    with patch.object(acs_mod.sarvam_client, "detect_language", mock_detect), \
         patch.object(acs_mod.bhashini_client, "transcribe", mock_transcribe), \
         patch.object(acs_mod.bhashini_client, "synthesize", mock_synthesize), \
         patch.object(acs_mod.chat_service, "generate_grounded_reply", mock_llm):

        files = {"file": ("test.wav", fake_audio_bytes, "audio/wav")}
        data = {
            "context": json.dumps({"currentTab": "dpr"}),
            "history": json.dumps([]),
        }

        response = client.post("/api/v2/chat/audio", files=files, data=data)
        assert response.status_code == 200
        res_json = response.json()

        assert res_json["tier_used"] == "bhashini"
        assert res_json["detected_language"] == "hi-IN"
        assert res_json["language"] == "hi"
        assert res_json["user_transcript"] == "डीपीआर कैसे डाउनलोड करें?"
        assert res_json["reply"] == "डीपीआर डाउनलोड करने के लिए एक्सपोर्ट बटन दबाएं।"
        assert res_json["tool_call"] == {"name": "export_dpr", "arguments": {"format": "pdf"}}
        assert res_json["audio_base64"].startswith("data:audio/wav;base64,")
        assert "timestamp" in res_json
