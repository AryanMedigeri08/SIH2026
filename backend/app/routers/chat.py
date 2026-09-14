"""
chat.py — REST API Router for Persistent Groq Chatbot, Audio Voice Agent & Enterprise Advisor.
"""

from __future__ import annotations
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Literal
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field

try:
    from app.core.chat_service import chat_service
    from app.core.audio_chat_service import audio_chat_service
    from app.config import settings
except ImportError:
    from backend.app.core.chat_service import chat_service
    from backend.app.core.audio_chat_service import audio_chat_service
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


class ChatCompletionResponse(BaseModel):
    message: Dict[str, str]
    reply: str
    model: str
    sources: List[str] = Field(default_factory=list, description="Verified data sources used for response")
    is_fallback: bool
    latency_ms: float
    timestamp: Optional[str] = None


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize to speech")
    language: Optional[str] = Field(default="en", description="Target language code (en, hi, mr, ta, te, kn)")


class TtsResponse(BaseModel):
    audio_base64: str
    language: str
    language_name: str
    latency_s: float


class ToolCallModel(BaseModel):
    """Voice-triggered UI action returned by the LLM tool-calling layer."""
    name: str = Field(..., description="Action name (navigate_to_tab, change_language, run_analysis, export_dpr)")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Action arguments")


class VoiceChatResponse(BaseModel):
    user_transcript: str
    reply: str
    language: str
    language_name: str
    detected_language: str = Field(default="en", description="Auto-detected BCP-47 language code from ASR")
    tier_used: str = Field(default="fallback", description="Speech tier used: 'sarvam' or 'fallback'")
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
    summary="V2 Cascade Voice Turn: Sarvam AI (primary) → Whisper+gTTS (fallback) with tool-calling",
)
@router.post(
    "/voice",
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
    V2 Voice Pipeline:
    Receives voice audio, runs the cascade controller (Sarvam primary → Whisper fallback),
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
    summary="Generate speech audio for any text message in specified language",
)
async def generate_speech(payload: TtsRequest):
    """
    Converts text message to high-quality spoken audio in user's active language using gTTS.
    """
    try:
        result = audio_chat_service.text_to_speech(
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
    summary="Transcribe audio to text with forced language using Groq Whisper Large v3",
)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    language: str = Form("en"),
):
    """Transcribes audio file to text."""
    try:
        audio_bytes = await file.read()
        return audio_chat_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "audio.webm",
            language=language or "en",
        )
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
    """Returns active model, keys, audio provider status, and Sarvam tier availability."""
    from app.core.audio_chat_service import _telemetry
    
    llm_client = audio_chat_service._get_llm_client()
    stt_client = audio_chat_service._get_stt_client()
    
    sarvam_configured = bool(getattr(settings, "SARVAM_API_KEY", None))
    
    return {
        "status": "ready" if (llm_client or stt_client) else "fallback_ready",
        "provider": "groq",
        "has_stt_key": bool(stt_client),
        "has_llm_key": bool(llm_client),
        "stt_model": audio_chat_service._stt_model,
        "llm_model": audio_chat_service._llm_model,
        "sarvam_configured": sarvam_configured,
        "voice_tier": "sarvam" if sarvam_configured else "fallback",
        "supported_voice_languages": list(audio_chat_service.VOICE_LANGUAGE_MAP.keys()) if hasattr(audio_chat_service, 'VOICE_LANGUAGE_MAP') else ["en", "hi", "mr", "te", "ta", "kn"],
        "telemetry": _telemetry,
    }
