"""
chat.py — REST API Router for Persistent Groq Chatbot, Audio Voice Agent & Enterprise Advisor.
"""

from __future__ import annotations
import time
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Literal
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field

try:
    from app.core.chat_service import chat_service
    from app.core.audio_chat_service import audio_chat_service, normalize_lang
    from app.core.bhashini_client import bhashini_client
    from app.core import sarvam_client
    from app.config import settings
except ImportError:
    from backend.app.core.chat_service import chat_service
    from backend.app.core.audio_chat_service import audio_chat_service, normalize_lang
    from backend.app.core.bhashini_client import bhashini_client
    from backend.app.core import sarvam_client
    from backend.app.config import settings

logger = logging.getLogger("udyam_saathi.api.chat")

router = APIRouter()


class ChatMessagePayload(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message text content")


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessagePayload] = Field(..., min_length=1, description="List of chat messages in conversation")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Active enterprise and report telemetry context")
    language: Optional[str] = Field(default="en", description="Target response language code (en, hi, mr, ta, te, kn)")
    is_voice_turn: bool = Field(default=False, description="Use Voice Agent system prompt and response formatting")


class ToolCallModel(BaseModel):
    """UI action returned by the LLM tool-calling layer."""
    name: str = Field(..., description="Action name (navigate_to_tab, change_language, run_analysis, export_dpr)")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Action arguments")


class ChatCompletionResponse(BaseModel):
    message: Dict[str, str]
    reply: str
    model: str
    sources: List[str] = Field(default_factory=list, description="Verified data sources used for response")
    is_fallback: bool
    latency_ms: float
    tool_call: Optional[ToolCallModel] = Field(default=None, description="UI action trigger from tool-calling, if any")
    timestamp: Optional[str] = None


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize to speech")
    language: Optional[str] = Field(default="en", description="Target language code (en, hi, mr, ta, te, kn)")


class TtsResponse(BaseModel):
    audio_base64: str
    language: str
    language_name: str
    latency_s: float
    tier_used: Optional[str] = Field(default="bhashini", description="TTS engine tier used ('bhashini' or 'gtts')")


class VoiceChatResponse(BaseModel):
    user_transcript: str
    reply: str
    language: str
    language_name: str
    detected_language: str = Field(default="en", description="Auto-detected BCP-47 language code from ASR")
    tier_used: str = Field(default="fallback", description="Speech tier used: 'bhashini', 'bhashini_asr_gtts_tts', or 'fallback'")
    sources: List[str] = Field(default_factory=list)
    audio_base64: str
    is_fallback: bool
    model: str
    tool_call: Optional[ToolCallModel] = Field(default=None, description="Voice-triggered UI action, if any")
    stt_latency_s: float
    llm_latency_s: float
    tts_latency_s: float
    total_latency_s: float
    timestamp: Optional[str] = None


@router.post(
    "",
    response_model=ChatCompletionResponse,
    summary="Send message to Groq AI Advisor with active enterprise grounding",
)
@router.post(
    "/",
    response_model=ChatCompletionResponse,
    include_in_schema=False,
)
async def create_chat_completion(payload: ChatCompletionRequest):
    """
    Submits user messages to Groq Cloud LLM with active enterprise telemetry grounding and guardrail screening.
    """
    try:
        raw_messages = [{"role": m.role, "content": m.content} for m in payload.messages]
        last_user_msg = raw_messages[-1]["content"] if raw_messages else ""
        logger.info("💬 [TEXT CHAT] Query: \"%s\" (lang=%s)", last_user_msg[:60], payload.language or "en")
        
        if payload.is_voice_turn:
            llm_result = chat_service.generate_voice_reply(
                transcript=last_user_msg,
                detected_language=payload.language or "en",
                screen_context=payload.context,
                tools=audio_chat_service.ACTION_REGISTRY_SCHEMA,
                conversation_history=raw_messages[:-1] if len(raw_messages) > 1 else None
            )
            result = {
                "message": {"role": "assistant", "content": llm_result.text},
                "model": llm_result.model,
                "sources": llm_result.sources,
                "is_fallback": llm_result.is_fallback,
                "latency_ms": llm_result.latency_ms,
                "tool_call": llm_result.tool_call,
            }
        else:
            result = chat_service.generate_chat_response(
                messages=raw_messages,
                context=payload.context,
                language=payload.language or "en",
            )
        
        content = result.get("message", {}).get("content", "")
        result["reply"] = content
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        if "sources" not in result:
            result["sources"] = []
        
        tool_call = result.get("tool_call")
        tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None) if tool_call else None
        tool_str = f" | Action: {tool_name}" if tool_name else ""
        latency_ms = result.get("latency_ms", 0)
        logger.info("🧠 [GROQ LLM] Response generated (%d chars) | ⏱️ %dms%s", len(content), int(latency_ms), tool_str)
        
        return result
    except Exception as e:
        logger.error("Chat completion error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot failed to process message: {str(e)}",
        )


@router.post(
    "/audio",
    response_model=VoiceChatResponse,
    summary="V3 Cascade Voice Turn: Sarvam Detect -> Bhashini ASR -> Groq LLM -> Bhashini TTS",
)
@router.post(
    "/voice",
    response_model=VoiceChatResponse,
    include_in_schema=False,
)
@router.post(
    "/voice-agent",
    response_model=VoiceChatResponse,
    include_in_schema=False,
)
async def process_voice_audio(
    file: UploadFile = File(..., description="Recorded audio file from microphone (webm/wav/mp3)"),
    language: Optional[str] = Form(None, description="(Deprecated) Language hint — backend now auto-detects"),
    context: Optional[str] = Form(None, description="JSON-serialized enterprise context"),
    history: Optional[str] = Form(None, description="JSON-serialized previous chat message history"),
):
    """
    V3 Voice Pipeline:
    Receives voice audio, runs the cascade controller (Sarvam detect -> Bhashini ASR -> Groq LLM -> Bhashini TTS / gTTS fallback),
    reasons with Groq LLM (with tool-calling for UI actions), and generates spoken response.
    
    Language is auto-detected — the `language` parameter is deprecated and ignored.
    """
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio recording received. Please record again.",
            )

        logger.info(
            "🎙️  [VOICE ROUTER] Incoming audio recording: %s (%d bytes)",
            file.filename or "recording.webm",
            len(audio_bytes),
        )

        parsed_context = None
        if context:
            try:
                parsed_context = json.loads(context)
            except Exception:
                parsed_context = None

        parsed_history = []
        if history:
            try:
                parsed_history = json.loads(history)
            except Exception:
                parsed_history = []

        # Use V2 cascade controller (async)
        result = await audio_chat_service.process_voice_turn_v2(
            audio_bytes=audio_bytes,
            filename=file.filename or "recording.webm",
            context=parsed_context,
            history=parsed_history,
        )
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Audio voice turn error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice processing failed: {str(e)}",
        )


@router.post(
    "/tts",
    response_model=TtsResponse,
    summary="Generate speech audio using Bhashini TTS (primary) with gTTS fallback",
)
async def generate_speech(payload: TtsRequest):
    """
    Converts text message to high-quality spoken audio in user's active language.
    Attempts Bhashini TTS first for native Indic voices, falls back to gTTS.
    """
    try:
        logger.info("🔊 [TTS ROUTER] Request: \"%s\" (lang=%s)", payload.text[:50], payload.language)
        result = await audio_chat_service.text_to_speech_v2(
            text=payload.text,
            language=payload.language or "en",
        )
        return result
    except Exception as e:
        logger.error("TTS generation error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text-to-speech failed: {str(e)}",
        )


@router.post(
    "/stt",
    summary="Transcribe audio to text using Sarvam LID + Bhashini ASR (primary) with Groq Whisper fallback",
)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """Transcribes audio file using Sarvam LID + Bhashini ASR (primary) with Groq Whisper fallback."""
    try:
        audio_bytes = await file.read()
        audio_fmt = file.filename.split(".")[-1].lower() if (file.filename and "." in file.filename) else "wav"
        if audio_fmt not in ("wav", "mp3", "webm", "ogg", "opus", "m4a", "flac"):
            audio_fmt = "wav"

        norm_lang = normalize_lang(language) if (language and language.strip()) else None

        # Primary: Sarvam LID (if language not passed) -> Bhashini ASR (for supported wav/mp3 audio)
        if not norm_lang:
            try:
                detected_lang = await sarvam_client.detect_language(audio_bytes, audio_format=audio_fmt)
                norm_lang = normalize_lang(detected_lang)
            except Exception as sarvam_err:
                logger.debug("Sarvam LID for /stt notice: %s", sarvam_err)

        if norm_lang and audio_fmt in ("wav", "mp3"):
            try:
                start_time = time.perf_counter()
                transcript = await bhashini_client.transcribe(
                    audio_bytes, language_code=norm_lang, audio_format=audio_fmt
                )
                if transcript and transcript.strip():
                    stt_latency = round(time.perf_counter() - start_time, 3)
                    lang_name = chat_service.LANGUAGE_NAMES.get(norm_lang, norm_lang.capitalize())
                    logger.info(
                        "[🇮🇳 BHASHINI ASR] Speech Transcribed (/stt %s): \"%s\" | ⏱️ %dms",
                        norm_lang,
                        transcript if len(transcript) <= 70 else transcript[:67] + "...",
                        int(stt_latency * 1000),
                    )
                    return {
                        "transcript": transcript,
                        "language": norm_lang,
                        "language_name": lang_name,
                        "detected_language_code": norm_lang,
                        "latency_s": stt_latency,
                        "provider": "bhashini",
                    }
            except Exception as bhashini_err:
                logger.warning("Bhashini ASR failed for /stt endpoint (%s), routing to Whisper fallback", bhashini_err)

        # Fallback: Groq Whisper Large v3 (with auto-detection if language is None)
        result = audio_chat_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "audio.webm",
            language=norm_lang,
        )
        result["provider"] = "groq_whisper"
        return result
    except Exception as e:
        logger.error("STT transcription error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(e)}",
        )


@router.get(
    "/health",
    summary="Check Chatbot & Audio Voice Engine status",
)
async def get_chat_health():
    """Returns active model, keys, audio provider status, Bhashini status, and telemetry."""
    try:
        from app.core.audio_chat_service import _telemetry
    except ImportError:
        from backend.app.core.audio_chat_service import _telemetry
    
    llm_client = audio_chat_service._get_llm_client()
    stt_client = audio_chat_service._get_stt_client()
    
    sarvam_configured = bool(getattr(settings, "SARVAM_API_KEY", None))
    bhashini_configured = bool(
        getattr(settings, "BHASHINI_API_KEY", None) and getattr(settings, "BHASHINI_USER_ID", None)
    )
    
    if bhashini_configured and sarvam_configured:
        voice_tier = "bhashini"
    elif bhashini_configured:
        voice_tier = "bhashini_direct"
    else:
        voice_tier = "fallback"

    return {
        "status": "ready" if (llm_client or stt_client) else "fallback_ready",
        "provider": "groq",
        "has_stt_key": bool(stt_client),
        "has_llm_key": bool(llm_client),
        "stt_model": audio_chat_service._stt_model,
        "llm_model": audio_chat_service._llm_model,
        "sarvam_configured": sarvam_configured,
        "bhashini_configured": bhashini_configured,
        "voice_tier": voice_tier,
        "supported_voice_languages": list(audio_chat_service.VOICE_LANGUAGE_MAP.keys()) if hasattr(audio_chat_service, 'VOICE_LANGUAGE_MAP') else ["en", "hi", "mr", "te", "ta", "kn"],
        "telemetry": _telemetry,
    }
