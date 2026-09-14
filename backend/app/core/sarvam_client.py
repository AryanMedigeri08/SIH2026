"""
sarvam_client.py — Async HTTP client for Sarvam AI Saaras ASR and Bulbul TTS.

Primary speech layer for Udyam Saathi Voice Agent V2, covering all 22
official Indian languages natively.  Falls back gracefully to Whisper+gTTS
via the cascade controller in audio_chat_service.py.

Endpoints:
  - Saaras ASR (speech-to-text): auto-detects source language
  - Bulbul v3 TTS (text-to-speech): synthesizes in detected language
"""

from __future__ import annotations
import asyncio
import base64
import logging
import time
from typing import Optional

import httpx
from pydantic import BaseModel, Field

try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

logger = logging.getLogger("udyam_saathi.sarvam")


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class SarvamASRResult(BaseModel):
    """Structured result from Sarvam Saaras speech-to-text."""
    transcript: str = Field(default="", description="Transcribed text from audio")
    detected_language_code: str = Field(
        default="hi-IN",
        description="BCP-47 language code auto-detected by Sarvam (e.g. hi-IN, ta-IN)",
    )
    latency_s: float = Field(default=0.0, description="Round-trip latency in seconds")


class SarvamTTSResult(BaseModel):
    """Structured result from Sarvam Bulbul text-to-speech."""
    audio_bytes: bytes = Field(default=b"", description="Raw synthesized audio bytes")
    latency_s: float = Field(default=0.0, description="Round-trip latency in seconds")


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class SarvamUnavailableError(Exception):
    """Raised when Sarvam API is unreachable, times out, or returns a non-2xx
    response.  Caught by the cascade controller to trigger fallback to
    Whisper+gTTS."""
    pass


# ---------------------------------------------------------------------------
# Sarvam AI Client
# ---------------------------------------------------------------------------

# Maximum text length for TTS synthesis (cost and UX lever)
_TTS_MAX_CHARS = 300


def _get_timeout_seconds() -> float:
    """Cascade timeout from settings, converted to seconds."""
    ms = int(getattr(settings, "VOICE_CASCADE_TIMEOUT_MS", 4000))
    return ms / 1000.0


def _get_api_key() -> str:
    key = getattr(settings, "SARVAM_API_KEY", "") or ""
    return key.strip()


def _get_asr_endpoint() -> str:
    return getattr(
        settings,
        "SARVAM_ASR_ENDPOINT",
        "https://api.sarvam.ai/speech-to-text",
    )


def _get_tts_endpoint() -> str:
    return getattr(
        settings,
        "SARVAM_TTS_ENDPOINT",
        "https://api.sarvam.ai/text-to-speech",
    )


async def transcribe(audio_bytes: bytes, audio_format: str = "wav") -> SarvamASRResult:
    """
    Transcribes audio using Sarvam Saaras ASR (simple request/response mode).

    Does NOT pass a source language hint — lets Sarvam auto-detect.
    Raises SarvamUnavailableError on timeout, non-2xx, auth failure, or
    malformed response.

    Parameters
    ----------
    audio_bytes : bytes
        Raw audio data (wav, webm, mp3, etc.)
    audio_format : str
        Audio container format hint (default "wav").

    Returns
    -------
    SarvamASRResult
        Contains transcript and detected_language_code.
    """
    api_key = _get_api_key()
    if not api_key:
        raise SarvamUnavailableError("SARVAM_API_KEY is not configured")

    endpoint = _get_asr_endpoint()
    timeout_s = _get_timeout_seconds()

    # Sarvam Saaras expects audio as base64 in a JSON payload
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    payload = {
        "audio": audio_b64,
        "audio_format": audio_format,
    }

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": api_key,
    }

    start = time.perf_counter()
    last_error: Optional[Exception] = None

    # Retry loop: max 1 retry for transient 5xx only
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)

            latency = round(time.perf_counter() - start, 3)

            # Fail fast on auth errors (config problem, not transient)
            if resp.status_code in (401, 403):
                logger.error(
                    "Sarvam ASR auth failure (HTTP %d). Check SARVAM_API_KEY.",
                    resp.status_code,
                )
                raise SarvamUnavailableError(
                    f"Sarvam ASR authentication failed (HTTP {resp.status_code})"
                )

            # Retry on 5xx
            if resp.status_code >= 500:
                last_error = SarvamUnavailableError(
                    f"Sarvam ASR returned HTTP {resp.status_code}"
                )
                if attempt == 0:
                    wait = 0.5  # exponential backoff base
                    logger.warning(
                        "Sarvam ASR 5xx (HTTP %d), retrying in %.1fs...",
                        resp.status_code,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    start = time.perf_counter()  # reset for retry latency
                    continue
                raise last_error

            # Any other non-2xx
            if not resp.is_success:
                raise SarvamUnavailableError(
                    f"Sarvam ASR returned HTTP {resp.status_code}: {resp.text[:200]}"
                )

            # Parse response
            try:
                data = resp.json()
            except Exception as e:
                raise SarvamUnavailableError(
                    f"Sarvam ASR returned malformed JSON: {e}"
                )

            transcript = data.get("transcript", "")
            lang_code = data.get("language_code", data.get("detected_language_code", "hi-IN"))

            logger.info(
                "Sarvam ASR success: lang=%s, chars=%d, latency=%.3fs",
                lang_code,
                len(transcript),
                latency,
            )

            return SarvamASRResult(
                transcript=transcript,
                detected_language_code=lang_code,
                latency_s=latency,
            )

        except SarvamUnavailableError:
            raise
        except httpx.TimeoutException:
            raise SarvamUnavailableError(
                f"Sarvam ASR timed out after {timeout_s}s"
            )
        except Exception as e:
            raise SarvamUnavailableError(f"Sarvam ASR request failed: {e}")

    # Should not reach here, but just in case
    raise last_error or SarvamUnavailableError("Sarvam ASR failed after retries")


async def synthesize(text: str, language_code: str) -> bytes:
    """
    Synthesizes text to speech using Sarvam Bulbul TTS.

    Caps outbound text at ~300 characters for cost control and UX.
    Returns raw audio bytes (base64-encoding happens at the router layer).

    Parameters
    ----------
    text : str
        Text to synthesize.
    language_code : str
        BCP-47 language code from the ASR step (round-trip consistency).

    Returns
    -------
    bytes
        Raw audio bytes (WAV/MP3 depending on Sarvam response).

    Raises
    ------
    SarvamUnavailableError
        On timeout, non-2xx, auth failure, or malformed response.
    """
    api_key = _get_api_key()
    if not api_key:
        raise SarvamUnavailableError("SARVAM_API_KEY is not configured")

    endpoint = _get_tts_endpoint()
    timeout_s = _get_timeout_seconds()

    # Defensive text length cap (~300 chars)
    capped_text = text[:_TTS_MAX_CHARS] if len(text) > _TTS_MAX_CHARS else text

    payload = {
        "text": capped_text,
        "language_code": language_code,
        "model": "bulbul:v2",
        "audio_format": "mp3",
        "speech_sample_rate": 22050,
    }

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": api_key,
    }

    start = time.perf_counter()
    last_error: Optional[Exception] = None

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)

            latency = round(time.perf_counter() - start, 3)

            if resp.status_code in (401, 403):
                logger.error(
                    "Sarvam TTS auth failure (HTTP %d). Check SARVAM_API_KEY.",
                    resp.status_code,
                )
                raise SarvamUnavailableError(
                    f"Sarvam TTS authentication failed (HTTP {resp.status_code})"
                )

            if resp.status_code >= 500:
                last_error = SarvamUnavailableError(
                    f"Sarvam TTS returned HTTP {resp.status_code}"
                )
                if attempt == 0:
                    wait = 0.5
                    logger.warning(
                        "Sarvam TTS 5xx (HTTP %d), retrying in %.1fs...",
                        resp.status_code,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    start = time.perf_counter()
                    continue
                raise last_error

            if not resp.is_success:
                raise SarvamUnavailableError(
                    f"Sarvam TTS returned HTTP {resp.status_code}: {resp.text[:200]}"
                )

            # Sarvam TTS returns base64-encoded audio in JSON
            try:
                data = resp.json()
            except Exception as e:
                raise SarvamUnavailableError(
                    f"Sarvam TTS returned malformed JSON: {e}"
                )

            audio_b64 = data.get("audio", data.get("audio_content", ""))
            if not audio_b64:
                raise SarvamUnavailableError("Sarvam TTS response missing audio data")

            audio_bytes = base64.b64decode(audio_b64)

            logger.info(
                "Sarvam TTS success: lang=%s, audio_bytes=%d, latency=%.3fs",
                language_code,
                len(audio_bytes),
                latency,
            )

            return audio_bytes

        except SarvamUnavailableError:
            raise
        except httpx.TimeoutException:
            raise SarvamUnavailableError(
                f"Sarvam TTS timed out after {timeout_s}s"
            )
        except Exception as e:
            raise SarvamUnavailableError(f"Sarvam TTS request failed: {e}")

    raise last_error or SarvamUnavailableError("Sarvam TTS failed after retries")
