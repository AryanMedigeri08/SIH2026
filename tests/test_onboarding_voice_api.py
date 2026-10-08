"""Onboarding microphone uploads must match the speech-to-text API contract."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / "backend"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from backend.app.main import app
from backend.app.routers import chat as chat_router


def test_onboarding_recording_is_transcribed_from_file_field(monkeypatch):
    captured = {}

    def fake_transcribe(*, audio_bytes, filename, language):
        captured.update(audio_bytes=audio_bytes, filename=filename, language=language)
        return {"transcript": "paneer ki dukan", "language": "hi"}

    monkeypatch.setattr(chat_router.audio_chat_service, "transcribe_audio", fake_transcribe)
    with TestClient(app) as client:
        response = client.post(
            "/api/v2/chat/stt",
            files={"file": ("onboarding-recording.webm", b"voice-bytes", "audio/webm")},
            data={"language": "hi"},
        )

    assert response.status_code == 200
    assert response.json()["transcript"] == "paneer ki dukan"
    assert captured == {
        "audio_bytes": b"voice-bytes",
        "filename": "onboarding-recording.webm",
        "language": "hi",
    }
