"""
audio_chat_service.py — V2 Multilingual Voice & Audio Conversational Agent for Udyam Saathi.

Cascade Pipeline (V2 Architecture):
  PRIMARY (Sarvam AI):
    1. Microphone Audio -> Sarvam Saaras ASR (auto-detect language) -> User Transcription
    2. Grounded MSME Context + History -> Groq LLM (with tool-calling) -> Voice-Optimized Response
    3. Response Text -> Sarvam Bulbul TTS (same detected language) -> Base64 Audio Stream

  FALLBACK (Whisper + gTTS — activated when Sarvam is unavailable):
    1. Microphone Audio -> Groq Whisper Large v3 -> User Transcription
    2. Language support check -> If unsupported, return degraded-language-notice (skip LLM)
    3. Grounded MSME Context + History -> Groq LLM (with tool-calling) -> Voice-Optimized Response
    4. Response Text -> gTTS -> Base64 Audio Stream
"""

from __future__ import annotations
import os
import io
import re
import time
import base64
import asyncio
import logging
from typing import Optional, Any, Dict, List
from gtts import gTTS

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from app.config import settings
    from app.core.chat_service import chat_service, LANGUAGE_NAMES, LLMReplyResult
    from app.core import sarvam_client
    from app.core.sarvam_client import SarvamUnavailableError
    from app.core.action_registry import ACTION_REGISTRY_SCHEMA
except ImportError:
    from backend.app.config import settings
    from backend.app.core.chat_service import chat_service, LANGUAGE_NAMES, LLMReplyResult
    from backend.app.core import sarvam_client
    from backend.app.core.sarvam_client import SarvamUnavailableError
    from backend.app.core.action_registry import ACTION_REGISTRY_SCHEMA

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

# Friendly language names for degraded-language-notice
FALLBACK_LANG_FRIENDLY_NAMES = {
    "en": ("English", "अंग्रेज़ी"),
    "hi": ("Hindi", "हिंदी"),
    "mr": ("Marathi", "मराठी"),
    "bn": ("Bengali", "बंगाली"),
    "gu": ("Gujarati", "गुजराती"),
    "ta": ("Tamil", "तमिल"),
    "te": ("Telugu", "तेलुगु"),
    "kn": ("Kannada", "कन्नड़"),
    "pa": ("Punjabi", "पंजाबी"),
    "ur": ("Urdu", "उर्दू"),
}

# Telemetry counters (in-memory for now)
_telemetry = {
    "sarvam_tier_total": 0,
    "fallback_tier_total": 0,
    "voice_degraded_language_notice_total": 0,
}


def normalize_lang(lang_code: str) -> str:
    """Normalize BCP-47 language codes (e.g. 'hi-IN' -> 'hi', 'ta-IN' -> 'ta')."""
    if not lang_code:
        return "en"
    return lang_code.split("-")[0].lower()


def _get_fallback_supported_langs() -> set[str]:
    """Parse VOICE_FALLBACK_SUPPORTED_LANGS from settings into a set."""
    raw = getattr(settings, "VOICE_FALLBACK_SUPPORTED_LANGS", "en,hi,mr,bn,gu,ta,te,kn,pa,ur")
    return {lang.strip().lower() for lang in raw.split(",") if lang.strip()}


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


def build_degraded_language_notice_response() -> dict[str, Any]:
    """
    Returns a fixed (non-LLM-generated, fully deterministic) response when
    the detected language is not supported by the fallback tier.
    
    Bilingual English + Hindi notice listing supported languages.
    Audio is synthesized from the Hindi portion via gTTS.
    This path SKIPS the LLM call entirely.
    """
    supported_langs = _get_fallback_supported_langs()
    
    # Build friendly language lists
    en_names = []
    hi_names = []
    for lang in sorted(supported_langs):
        names = FALLBACK_LANG_FRIENDLY_NAMES.get(lang)
        if names:
            en_names.append(names[0])
            hi_names.append(names[1])
    
    en_list = ", ".join(en_names)
    hi_list = ", ".join(hi_names)
    
    notice_text = (
        f"Voice support for this language isn't available right now. "
        f"I can currently help you in: {en_list}. "
        f"Please try one of these, or type your question. / "
        f"अभी इस भाषा में आवाज़ सहायता उपलब्ध नहीं है। "
        f"मैं फिलहाल इन भाषाओं में मदद कर सकता हूँ: {hi_list}। "
        f"कृपया इनमें से कोई एक आज़माएँ, या टाइप करके पूछें।"
    )
    
    # Synthesize Hindi portion via gTTS
    hindi_text = (
        f"अभी इस भाषा में आवाज़ सहायता उपलब्ध नहीं है। "
        f"मैं फिलहाल इन भाषाओं में मदद कर सकता हूँ: {hi_list}। "
        f"कृपया इनमें से कोई एक आज़माएँ, या टाइप करके पूछें।"
    )
    
    audio_base64 = ""
    try:
        tts = gTTS(text=hindi_text, lang="hi", slow=False)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        audio_bytes = buffer.getvalue()
        audio_base64 = f"data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode('utf-8')}"
    except Exception as e:
        logger.warning("gTTS synthesis failed for degraded-language-notice: %s", e)
    
    # Increment telemetry counter
    _telemetry["voice_degraded_language_notice_total"] += 1
    logger.info(
        "Degraded language notice served (total: %d)",
        _telemetry["voice_degraded_language_notice_total"],
    )
    
    return {
        "user_transcript": "(Unsupported language detected)",
        "reply": notice_text,
        "language": "hi",
        "language_name": "Hindi",
        "detected_language": "unknown",
        "tier_used": "fallback",
        "sources": [],
        "audio_base64": audio_base64,
        "is_fallback": True,
        "model": "degraded_language_notice",
        "tool_call": None,
        "stt_latency_s": 0.0,
        "llm_latency_s": 0.0,
        "tts_latency_s": 0.0,
        "total_latency_s": 0.0,
    }


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
                "detected_language_code": lang_meta["code"],
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

    async def process_voice_turn_v2(
        self,
        audio_bytes: bytes,
        filename: str = "recording.webm",
        context: Optional[dict[str, Any]] = None,
        history: Optional[List[dict[str, str]]] = None,
    ) -> dict[str, Any]:
        """
        V2 Cascade Voice Turn:
          1. Try Sarvam ASR (auto-detect language) → on failure, fall back to Whisper
          2. Check language support in fallback mode → degraded-language-notice if unsupported
          3. LLM grounded reply with tool-calling
          4. TTS in the same tier as STT (Sarvam Bulbul or gTTS)
        """
        overall_start = time.perf_counter()
        
        transcript = ""
        detected_lang = "en"
        used_tier = "sarvam"

        # ── Step 1: Speech-to-Text (Sarvam primary, Whisper fallback) ──
        try:
            asr_result = await sarvam_client.transcribe(audio_bytes, audio_format="wav")
            transcript = asr_result.transcript
            detected_lang = asr_result.detected_language_code
            used_tier = "sarvam"
            stt_latency = asr_result.latency_s
            logger.info(
                "Sarvam ASR success: lang=%s, transcript_len=%d",
                detected_lang,
                len(transcript),
            )
        except (SarvamUnavailableError, Exception) as e:
            logger.warning("Sarvam ASR unavailable (%s), falling back to Whisper+gTTS", e)
            used_tier = "fallback"
            
            # Whisper fallback — use 'en' as the forced language since we can't auto-detect
            # Whisper will transcribe in whatever language it hears, even with language hint
            try:
                whisper_result = self.transcribe_audio(audio_bytes, filename, "en")
                transcript = whisper_result["transcript"]
                detected_lang = whisper_result.get("detected_language_code", whisper_result.get("language", "en"))
                stt_latency = whisper_result["latency_s"]
            except Exception as whisper_err:
                logger.error("Whisper fallback also failed: %s", whisper_err)
                return {
                    "user_transcript": "(Speech recognition failed)",
                    "reply": "I'm sorry, I couldn't process your audio. Please try again or type your question.",
                    "language": "en",
                    "language_name": "English",
                    "detected_language": "en",
                    "tier_used": "fallback",
                    "sources": [],
                    "audio_base64": "",
                    "is_fallback": True,
                    "model": "stt_failure",
                    "tool_call": None,
                    "stt_latency_s": round(time.perf_counter() - overall_start, 3),
                    "llm_latency_s": 0.0,
                    "tts_latency_s": 0.0,
                    "total_latency_s": round(time.perf_counter() - overall_start, 3),
                }
            
            # Check if the detected language is supported by the fallback tier
            norm_lang = normalize_lang(detected_lang)
            supported = _get_fallback_supported_langs()
            if norm_lang not in supported:
                logger.info(
                    "Detected language '%s' not in fallback supported set %s — serving degraded notice",
                    norm_lang,
                    supported,
                )
                notice = build_degraded_language_notice_response()
                notice["user_transcript"] = transcript or "(Unsupported language detected)"
                notice["stt_latency_s"] = stt_latency
                notice["total_latency_s"] = round(time.perf_counter() - overall_start, 3)
                return notice
        
        if not transcript:
            transcript = "(No speech detected)"

        # ── Step 2: LLM Generation (with tool-calling) ──
        llm_start = time.perf_counter()
        
        llm_response: LLMReplyResult = chat_service.generate_grounded_reply(
            transcript=transcript,
            language=detected_lang,
            screen_context=context,
            tools=ACTION_REGISTRY_SCHEMA,
        )
        
        llm_latency = round(time.perf_counter() - llm_start, 3)
        bot_reply = llm_response.text
        sources = llm_response.sources
        is_fallback = llm_response.is_fallback
        model_used = llm_response.model
        tool_call = llm_response.tool_call

        # ── Step 3: Text-to-Speech (same tier as STT) ──
        tts_start = time.perf_counter()
        audio_base64 = ""
        
        # Clean the reply for speech
        speech_text = _clean_markdown_for_speech(bot_reply)
        if not speech_text:
            speech_text = bot_reply or "Response ready."
        
        if used_tier == "sarvam":
            try:
                tts_audio_bytes = await sarvam_client.synthesize(speech_text, detected_lang)
                b64 = base64.b64encode(tts_audio_bytes).decode("utf-8")
                audio_base64 = f"data:audio/mp3;base64,{b64}"
            except (SarvamUnavailableError, Exception) as e:
                logger.warning("Sarvam TTS failed (%s), falling back to gTTS", e)
                # Fall back to gTTS for TTS even if Sarvam was used for ASR
                norm = normalize_lang(detected_lang)
                tts_res = self.text_to_speech(bot_reply, norm)
                audio_base64 = tts_res.get("audio_base64", "")
        else:
            # Fallback tier: use gTTS
            norm = normalize_lang(detected_lang)
            tts_res = self.text_to_speech(bot_reply, norm)
            audio_base64 = tts_res.get("audio_base64", "")
        
        tts_latency = round(time.perf_counter() - tts_start, 3)
        total_latency = round(time.perf_counter() - overall_start, 3)

        # Telemetry counters
        _telemetry[f"{used_tier}_tier_total"] = _telemetry.get(f"{used_tier}_tier_total", 0) + 1
        
        norm_detected = normalize_lang(detected_lang)
        lang_name = LANGUAGE_NAMES.get(norm_detected, VOICE_LANGUAGE_MAP.get(norm_detected, {}).get("name", "Unknown"))

        return {
            "user_transcript": transcript,
            "reply": bot_reply,
            "language": norm_detected,
            "language_name": lang_name,
            "detected_language": detected_lang,
            "tier_used": used_tier,
            "sources": sources,
            "audio_base64": audio_base64,
            "is_fallback": is_fallback,
            "model": model_used,
            "tool_call": tool_call,
            "stt_latency_s": stt_latency,
            "llm_latency_s": llm_latency,
            "tts_latency_s": tts_latency,
            "total_latency_s": total_latency,
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
        Legacy V1 Voice Turn (kept for backward compatibility):
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
            "detected_language": lang_code,
            "tier_used": "fallback",
            "sources": sources,
            "audio_base64": audio_base64,
            "is_fallback": is_fallback,
            "model": model_used,
            "tool_call": None,
            "stt_latency_s": stt_latency,
            "llm_latency_s": llm_latency,
            "tts_latency_s": tts_latency,
            "total_latency_s": total_latency,
        }


audio_chat_service = AudioChatService()
