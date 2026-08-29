"""
audio_chat_service.py — Multilingual Voice & Audio Conversational Agent for Udyam Saathi.
Pipeline:
  1. Microphone Audio -> Groq Whisper Large v3 (Forced Target Language) -> User Transcription
  2. Grounded MSME Context + History -> Groq LLM (Enforced Target Language) -> Voice-Optimized Response
  3. Response Text -> gTTS (Natural Neural Speech) -> Base64 Audio Stream
"""

from __future__ import annotations
import os
import io
import re
import time
import base64
import logging
from typing import Optional, Any, Dict, List
from gtts import gTTS

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from app.config import settings
    from app.core.chat_service import chat_service, LANGUAGE_NAMES
except ImportError:
    from backend.app.config import settings
    from backend.app.core.chat_service import chat_service, LANGUAGE_NAMES

logger = logging.getLogger("udyam_saathi.audio_chat")

# ISO 639-1 language code mapping for Whisper STT and gTTS
VOICE_LANGUAGE_MAP: dict[str, dict[str, str]] = {
    "en": {"code": "en", "name": "English", "gtts": "en", "native": "English"},
    "hi": {"code": "hi", "name": "Hindi", "gtts": "hi", "native": "हिन्दी"},
    "mr": {"code": "mr", "name": "Marathi", "gtts": "mr", "native": "मराठी"},
    "te": {"code": "te", "name": "Telugu", "gtts": "te", "native": "తెలుగు"},
    "ta": {"code": "ta", "name": "Tamil", "gtts": "ta", "native": "தமிழ்"},
    "kn": {"code": "kn", "name": "Kannada", "gtts": "kn", "native": "ಕನ್ನಡ"},
}


def _clean_markdown_for_speech(text: str) -> str:
    """
    Strips markdown formatting, tables, URLs, and asterisks to ensure
    the generated speech flows naturally through Text-to-Speech engines.
    """
    if not text:
        return ""
    
    cleaned = text
    # Remove code blocks
    cleaned = re.sub(r'```[\s\S]*?```', '', cleaned)
    # Remove inline code
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
    # Remove markdown links, keep text
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    # Remove bold/italic markers
    cleaned = re.sub(r'[*_~#]+', '', cleaned)
    # Remove full table lines
    cleaned = re.sub(r'^\s*\|.*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\|', ' ', cleaned)
    # Remove bullet markers
    cleaned = re.sub(r'^\s*[-+*]\s+', '', cleaned, flags=re.MULTILINE)
    # Remove data sources lines from voice audio to keep speech snappy
    cleaned = re.sub(r'\b(Data Sources|தரவு ஆதாரங்கள்|డేటా మూలాలు|ಡೇಟಾ ಮೂಲಗಳು|डेटा स्रोत):\s*.*$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    # Normalize multiple whitespace and newlines
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


class AudioChatService:
    def __init__(self):
        self._stt_model = getattr(settings, "GROQ_STT_MODEL", "whisper-large-v3")
        self._llm_model = getattr(settings, "GROQ_LLM_MODEL", getattr(settings, "GROQ_MODEL", "openai/gpt-oss-20b"))

    def _get_stt_client(self) -> Optional[Any]:
        """Initializes Groq client for Speech-to-Text using GROQ_API_KEY_STT or fallbacks."""
        if Groq is None:
            return None
        api_key = (
            getattr(settings, "GROQ_API_KEY_STT", None)
            or getattr(settings, "GROQ_CHAT_KEY", None)
            or getattr(settings, "GROQ_API_KEY", "")
        )
        if not api_key:
            return None
        return Groq(api_key=api_key)

    def _get_llm_client(self) -> Optional[Any]:
        """Initializes Groq client for LLM using GROQ_API_KEY_LLM or fallbacks."""
        if Groq is None:
            return None
        api_key = (
            getattr(settings, "GROQ_API_KEY_LLM", None)
            or getattr(settings, "GROQ_CHAT_KEY", None)
            or getattr(settings, "GROQ_API_KEY", "")
        )
        if not api_key:
            return None
        return Groq(api_key=api_key)

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "recording.webm",
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Transcribes audio using Groq Whisper Large v3 with forced language constraint.
        """
        lang_code = language.lower() if language else "en"
        lang_meta = VOICE_LANGUAGE_MAP.get(lang_code, VOICE_LANGUAGE_MAP["en"])
        
        stt_client = self._get_stt_client()
        if not stt_client:
            raise ValueError("Groq STT client is not configured. Please set GROQ_API_KEY_STT or GROQ_API_KEY.")

        start_time = time.perf_counter()
        try:
            # Transcribe with language constraint to prevent hallucinated language detection
            transcription = stt_client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model=self._stt_model,
                language=lang_meta["code"],
                response_format="json",
                temperature=0.0,
            )
            stt_latency = time.perf_counter() - start_time
            transcript = transcription.text.strip()
            
            return {
                "transcript": transcript,
                "language": lang_meta["code"],
                "language_name": lang_meta["name"],
                "latency_s": round(stt_latency, 3),
            }
        except Exception as e:
            logger.error("Groq Whisper STT failed: %s", e, exc_info=True)
            raise e

    def text_to_speech(self, text: str, language: str = "en") -> dict[str, Any]:
        """
        Synthesizes text into high-quality natural speech audio (MP3 base64).
        """
        lang_code = language.lower() if language else "en"
        lang_meta = VOICE_LANGUAGE_MAP.get(lang_code, VOICE_LANGUAGE_MAP["en"])
        gtts_code = lang_meta.get("gtts", "en")

        clean_text = _clean_markdown_for_speech(text)
        if not clean_text:
            clean_text = text or "Response ready."

        start_time = time.perf_counter()
        try:
            tts = gTTS(text=clean_text, lang=gtts_code, slow=False)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            audio_bytes = buffer.getvalue()
            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            data_url = f"data:audio/mp3;base64,{b64_audio}"
            tts_latency = time.perf_counter() - start_time

            return {
                "audio_base64": data_url,
                "language": lang_code,
                "language_name": lang_meta["name"],
                "latency_s": round(tts_latency, 3),
                "audio_bytes_len": len(audio_bytes),
            }
        except Exception as e:
            logger.error("gTTS synthesis failed: %s", e, exc_info=True)
            # Return empty audio gracefully without crashing chat flow
            return {
                "audio_base64": "",
                "language": lang_code,
                "language_name": lang_meta["name"],
                "latency_s": round(time.perf_counter() - start_time, 3),
                "error": str(e),
            }

    def process_voice_turn(
        self,
        audio_bytes: bytes,
        filename: str = "recording.webm",
        language: str = "en",
        context: Optional[dict[str, Any]] = None,
        history: Optional[List[dict[str, str]]] = None,
    ) -> dict[str, Any]:
        """
        Complete End-to-End Voice Turn:
        1. STT (Whisper Large v3) -> Transcript
        2. LLM (Groq / gpt-oss-20b) -> Conversational Grounded Reply
        3. TTS (gTTS) -> Audio base64
        """
        overall_start = time.perf_counter()
        lang_code = language.lower() if language else "en"
        lang_meta = VOICE_LANGUAGE_MAP.get(lang_code, VOICE_LANGUAGE_MAP["en"])

        # --- Step 1: Speech-to-Text ---
        stt_res = self.transcribe_audio(audio_bytes, filename, lang_code)
        user_transcript = stt_res["transcript"]
        stt_latency = stt_res["latency_s"]

        if not user_transcript:
            user_transcript = "(No speech detected)"

        # --- Step 2: LLM Generation ---
        llm_start = time.perf_counter()
        messages_payload = list(history or [])
        messages_payload.append({"role": "user", "content": user_transcript})

        chat_res = chat_service.generate_chat_response(
            messages=messages_payload,
            context=context,
            language=lang_code,
        )
        llm_latency = round(time.perf_counter() - llm_start, 3)
        bot_reply = chat_res.get("message", {}).get("content", "")
        sources = chat_res.get("sources", [])
        is_fallback = chat_res.get("is_fallback", False)
        model_used = chat_res.get("model", self._llm_model)

        # --- Step 3: Text-to-Speech ---
        tts_res = self.text_to_speech(bot_reply, lang_code)
        audio_base64 = tts_res.get("audio_base64", "")
        tts_latency = tts_res.get("latency_s", 0.0)

        total_latency = round(time.perf_counter() - overall_start, 3)

        return {
            "user_transcript": user_transcript,
            "reply": bot_reply,
            "language": lang_code,
            "language_name": lang_meta["name"],
            "sources": sources,
            "audio_base64": audio_base64,
            "is_fallback": is_fallback,
            "model": model_used,
            "stt_latency_s": stt_latency,
            "llm_latency_s": llm_latency,
            "tts_latency_s": tts_latency,
            "total_latency_s": total_latency,
        }


audio_chat_service = AudioChatService()
