"""
sarvam_client.py — Sarvam AI Language Detection Client (Voice Agent V3).

Single Responsibility:
Calls Sarvam Saaras STT endpoint with `language_code="unknown"` exclusively
to detect the spoken Indic language code across all 22 scheduled Indian languages.

The transcript in Sarvam's response is UNCONDITIONALLY DISCARDED — it is
never persisted, logged, or passed downstream.  All downstream ASR and TTS
is handled 100% by Bhashini.

Endpoints:
  - Sarvam STT: https://api.sarvam.ai/speech-to-text
"""

from __future__ import annotations
import asyncio
import logging
import time
from typing import Optional, Any

import httpx

try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

logger = logging.getLogger("udyam_saathi.sarvam")


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

from dataclasses import dataclass


# Backward compatibility stubs
@dataclass
class SarvamASRResult:
    transcript: str = ""
    detected_language_code: str = "en"
    latency_s: float = 0.0


@dataclass
class SarvamTTSResult:
    audio_bytes: bytes = b""
    latency_s: float = 0.0


class SarvamDetectionError(Exception):
    """Raised when Sarvam language detection fails, times out, or returns
    an unparseable response.  Caught by audio_chat_service to trigger fallback."""
    pass


# Backward compatibility alias
SarvamUnavailableError = SarvamDetectionError


# ---------------------------------------------------------------------------
# Helper Configuration Functions
# ---------------------------------------------------------------------------

def _get_timeout_seconds() -> float:
    """Cascade timeout from settings, converted to seconds."""
    ms = int(getattr(settings, "VOICE_CASCADE_TIMEOUT_MS", 4000))
    return ms / 1000.0


def _get_api_key() -> str:
    key = getattr(settings, "SARVAM_API_KEY", "") or ""
    return key.strip()


def _get_stt_endpoint() -> str:
    return getattr(
        settings,
        "SARVAM_STT_ENDPOINT",
        getattr(settings, "SARVAM_ASR_ENDPOINT", "https://api.sarvam.ai/speech-to-text"),
    )


def extract_language_code_from_response(data: dict[str, Any]) -> Optional[str]:
    """
    Extracts the detected language code defensively across potential
    Sarvam API response field conventions:
      - `language_code` (standard documented field)
      - `source_language_code`
      - `detected_language_code`
      - `detected_language`
      - `language`
    """
    if not isinstance(data, dict):
        return None

    code = (
        data.get("language_code")
        or data.get("source_language_code")
        or data.get("detected_language_code")
        or data.get("detected_language")
        or data.get("language")
    )
    if code and isinstance(code, str) and code.strip():
        return code.strip()
    return None


# ---------------------------------------------------------------------------
# Primary V3 Detection Function
# ---------------------------------------------------------------------------

async def detect_language(audio_bytes: bytes, audio_format: str = "wav") -> str:
    """
    Calls Sarvam STT with language_code="unknown" purely to extract the
    detected source language across all 22 official Indian languages.

    The transcript in the response is DISCARDED unconditionally — never
    persisted, logged as content, or passed downstream.

    Parameters
    ----------
    audio_bytes : bytes
        Raw audio bytes from microphone or client.
    audio_format : str
        Audio format hint ('wav', 'webm', 'mp3', etc.).

    Returns
    -------
    str
        Detected language code (e.g. 'hi-IN', 'ta-IN', 'mr-IN', 'en-IN').

    Raises
    ------
    SarvamDetectionError
        On timeout, network error, 4xx/5xx, or missing credentials.
    """
    api_key = _get_api_key()
    if not api_key:
        raise SarvamDetectionError("SARVAM_API_KEY is not configured")

    if not audio_bytes:
        raise SarvamDetectionError("Empty audio recording provided for language detection")

    endpoint = _get_stt_endpoint()
    timeout_s = _get_timeout_seconds()

    headers = {
        "api-subscription-key": api_key,
    }

    # Prepare multipart/form-data request per Sarvam Speech-to-Text API specification
    mime_type = "audio/wav" if audio_format.lower() in ("wav", "wave") else f"audio/{audio_format.lower()}"
    files = {
        "file": (f"audio.{audio_format}", audio_bytes, mime_type),
    }
    data = {
        "model": "saaras:v1",
        "language_code": "unknown",  # triggers Sarvam 22-language auto-detection
    }

    start = time.perf_counter()
    last_error: Optional[Exception] = None

    # Retry loop: max 1 retry for transient 5xx only; fail-fast on 401/403
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    files=files,
                    data=data,
                )

            # Check status code
            if response.status_code in (401, 403):
                logger.error(
                    "Sarvam API auth failed (%d): check SARVAM_API_KEY in configuration",
                    response.status_code,
                )
                raise SarvamDetectionError(
                    f"Sarvam authentication failed with status {response.status_code}"
                )

            if response.status_code >= 500:
                last_error = SarvamDetectionError(
                    f"Sarvam server error {response.status_code}: {response.text[:200]}"
                )
                if attempt == 0:
                    logger.warning(
                        "Sarvam transient 5xx error (%d), retrying once...",
                        response.status_code,
                    )
                    await asyncio.sleep(0.5)
                    continue
                raise last_error

            if response.status_code != 200:
                raise SarvamDetectionError(
                    f"Sarvam STT failed with status {response.status_code}: {response.text[:200]}"
                )

            # Parse JSON response
            resp_data = response.json()
            detected_code = extract_language_code_from_response(resp_data)
            if not detected_code:
                logger.error(
                    "Sarvam STT response did not contain a recognizable language field: %s",
                    list(resp_data.keys()) if isinstance(resp_data, dict) else type(resp_data),
                )
                raise SarvamDetectionError(
                    "Sarvam STT response missing detected language code"
                )

            latency = round(time.perf_counter() - start, 3)
            confidence = resp_data.get("confidence") or resp_data.get("language_confidence")

            # Telemetry logging: Log language and confidence ONLY — NEVER log transcript
            logger.info(
                "Sarvam language detected: lang='%s', confidence=%s, latency=%.3fs (transcript discarded)",
                detected_code,
                confidence,
                latency,
            )

            return detected_code

        except httpx.TimeoutException:
            logger.warning("Sarvam STT timed out after %.1fs", timeout_s)
            raise SarvamDetectionError(f"Sarvam STT timed out after {timeout_s}s")
        except httpx.RequestError as e:
            logger.warning("Sarvam STT connection error: %s", e)
            last_error = SarvamDetectionError(f"Sarvam STT connection error: {e}")
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
            raise last_error
        except SarvamDetectionError:
            raise
        except Exception as e:
            logger.error("Unexpected error in Sarvam detect_language: %s", e, exc_info=True)
            raise SarvamDetectionError(f"Unexpected Sarvam detection error: {e}")

    raise last_error or SarvamDetectionError("Sarvam detection failed after retry")


# ---------------------------------------------------------------------------
# Compatibility Stubs (for any leftover references during migration)
# ---------------------------------------------------------------------------

class SarvamASRResult:
    def __init__(self, transcript="", detected_language_code="hi-IN", latency_s=0.0):
        self.transcript = transcript
        self.detected_language_code = detected_language_code
        self.latency_s = latency_s


async def transcribe(audio_bytes: bytes, audio_format: str = "wav") -> SarvamASRResult:
    """Deprecated: V3 uses detect_language() and discards transcript. Maintained for compat."""
    lang = await detect_language(audio_bytes, audio_format)
    return SarvamASRResult(transcript="", detected_language_code=lang)
