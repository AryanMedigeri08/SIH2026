"""
test_chat_service.py — Test Suite for Groq Chatbot Service & REST Endpoints.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from backend.app.main import app
from backend.app.core.chat_service import chat_service

client = TestClient(app)


def test_chat_health():
    """Verify chatbot health endpoint."""
    resp = client.get("/api/v2/chat/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "provider" in data


def test_chat_service_direct():
    """Verify ChatService directly with sample conversation."""
    sample_context = {
        "enterprise_name": "Kaveri Bio Agro Mills",
        "sector": "agro_processing",
        "business_category": "manufacturing",
        "location": "Mysuru, Karnataka",
        "project_cost": 1500000.0,
        "promoter_margin": 150000.0,
        "top_scheme_name": "PMEGP",
        "subsidy_amount": 375000.0,
        "effective_loan": 975000.0,
        "monthly_emi": 18200.0,
        "dscr": 2.14,
        "dscr_verdict": "VIABLE",
        "ml_verdict": "SUITABLE",
        "ml_confidence_pct": 98.4,
    }
    messages = [
        {"role": "user", "content": "What is my DSCR ratio and is my bank loan safe?"}
    ]
    res = chat_service.generate_chat_response(messages, context=sample_context, language="en")
    assert "message" in res
    assert res["message"]["role"] == "assistant"
    assert len(res["message"]["content"]) > 10
    assert "model" in res
    assert "latency_ms" in res


def test_chat_api_endpoint():
    """Verify POST /api/v2/chat endpoint with multi-turn conversation."""
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, how can Udyam Saathi help me get PMEGP subsidy?"}
        ],
        "context": {
            "enterprise_name": "Purulia Mustard Oil Mill",
            "project_cost": 800000.0,
            "top_scheme_name": "PMEGP",
            "subsidy_amount": 280000.0,
        },
        "language": "en",
    }
    resp = client.post("/api/v2/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"]["role"] == "assistant"
    assert len(data["message"]["content"]) > 0


if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING CHATBOT SERVICE TEST SUITE")
    print("=" * 80)
    test_chat_health()
    print("  [PASS] GET /api/v2/chat/health passed.")
    test_chat_service_direct()
    print("  [PASS] Direct ChatService generation with context passed.")
    test_chat_api_endpoint()
    print("  [PASS] POST /api/v2/chat endpoint passed.")
    print("=" * 80)
    print("ALL CHATBOT BACKEND TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)
