"""
test_audio_chat_service.py — Unit Tests for Multilingual Audio Chatbot Engine.
Tests speech-to-text language enforcement, gTTS audio synthesis across 6 languages,
markdown audio stripping, and API voice endpoints.
"""

import os
import sys
import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure root paths are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from backend.app.main import app
from backend.app.core.audio_chat_service import (
    audio_chat_service,
    _clean_markdown_for_speech,
    VOICE_LANGUAGE_MAP,
)

client = TestClient(app)


def test_voice_languages_mapping():
    """Verify all 6 core Indic languages + English are mapped correctly."""
    required = ["en", "hi", "mr", "te", "ta", "kn"]
    for code in required:
        assert code in VOICE_LANGUAGE_MAP
        assert VOICE_LANGUAGE_MAP[code]["code"] == code
        assert "gtts" in VOICE_LANGUAGE_MAP[code]
        assert "name" in VOICE_LANGUAGE_MAP[code]


def test_clean_markdown_for_speech():
    """Verify markdown symbols, tables, bold, and code blocks are stripped for natural speech."""
    raw = """
    # Feasibility Summary
    Your **DSCR** is `1.45`.
    | Year | Revenue |
    |---|---|
    | Y1 | ₹10L |
    - Bullet item
    **Data Sources**: RBI Guidelines
    """
    cleaned = _clean_markdown_for_speech(raw)
    assert "#" not in cleaned
    assert "**" not in cleaned
    assert "|" not in cleaned
    assert "`" not in cleaned
    assert "DSCR is 1.45" in cleaned
    assert "Bullet item" in cleaned


def test_gtts_audio_synthesis_multi_language():
    """Verify in-memory gTTS audio generation across supported languages."""
    for lang in ["en", "hi", "mr", "te", "ta", "kn"]:
        res = audio_chat_service.text_to_speech("Namaste and Welcome to Udyam Saathi", language=lang)
        assert res is not None
        assert "audio_base64" in res
        assert res["audio_base64"].startswith("data:audio/mp3;base64,")
        assert res["language"] == lang
        assert res["latency_s"] >= 0.0


def test_tts_api_endpoint():
    """Test POST /api/v2/chat/tts endpoint."""
    response = client.post(
        "/api/v2/chat/tts",
        json={"text": "Udyam Saathi Loan Feasibility Check", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "audio_base64" in data
    assert data["audio_base64"].startswith("data:audio/mp3;base64,")
    assert data["language"] == "en"


def test_chat_health_endpoint_audio_info():
    """Test GET /api/v2/chat/health reports STT, LLM and audio models."""
    response = client.get("/api/v2/chat/health")
    assert response.status_code == 200
    data = response.json()
    assert "stt_model" in data
    assert "llm_model" in data
    assert "supported_voice_languages" in data
    assert "en" in data["supported_voice_languages"]
    assert "te" in data["supported_voice_languages"]
