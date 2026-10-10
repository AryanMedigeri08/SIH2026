"""Onboarding microphone uploads must match the speech-to-text API contract."""

import sys
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "backend", ROOT / "backend" / "app" / "core"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.routers import chat as chat_router


def _transcribe(name, content, language, purpose=None):
    class InMemoryUpload:
        filename = name

        async def read(self):
            return content

    upload = InMemoryUpload()
    return asyncio.run(chat_router.transcribe_audio_file(file=upload, language=language, purpose=purpose))


def test_onboarding_recording_is_transcribed_from_file_field(monkeypatch):
    captured = {}

    def fake_transcribe(*, audio_bytes, filename, language):
        captured.update(audio_bytes=audio_bytes, filename=filename, language=language)
        return {"transcript": "paneer ki dukan", "language": "hi"}

    monkeypatch.setattr(chat_router.audio_chat_service, "transcribe_audio", fake_transcribe)
    result = _transcribe("onboarding-recording.webm", b"voice-bytes", "hi")
    assert result["transcript"] == "paneer ki dukan"
    assert captured == {
        "audio_bytes": b"voice-bytes",
        "filename": "onboarding-recording.webm",
        "language": "hi",
    }


def test_onboarding_wav_uses_selected_language_and_bhashini_asr_before_groq(monkeypatch):
    asr = AsyncMock(return_value="मुझे सिलाई का काम शुरू करना है")
    monkeypatch.setattr(chat_router.bhashini_client, "transcribe", asr)
    monkeypatch.setattr(chat_router.audio_chat_service, "transcribe_audio", lambda **_: (_ for _ in ()).throw(AssertionError("Groq must not run")))
    result = _transcribe("onboarding-recording.wav", b"wav-bytes", "hi", "onboarding")
    assert result["provider"] == "bhashini"
    asr.assert_awaited_once_with(b"wav-bytes", language_code="hi", audio_format="wav")


def test_onboarding_falls_back_to_groq_if_bhashini_is_unavailable(monkeypatch):
    monkeypatch.setattr(chat_router.bhashini_client, "transcribe", AsyncMock(side_effect=RuntimeError("offline")))
    monkeypatch.setattr(chat_router.audio_chat_service, "transcribe_audio", lambda **_: {"transcript": "tailoring", "language": "en"})
    result = _transcribe("onboarding-recording.wav", b"wav-bytes", "en", "onboarding")
    assert result["provider"] == "groq_whisper"
