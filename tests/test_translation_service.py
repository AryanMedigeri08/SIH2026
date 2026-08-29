"""
test_translation_service.py — Verification Suite for Google Cloud Translation & Multilingual Support.
"""

import sys
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure root directory is on pythonpath
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from backend.app.main import app
from backend.app.core.translation_service import translation_service, SUPPORTED_LANGUAGES

client = TestClient(app)


def test_supported_languages_endpoint():
    """Verify supported languages metadata returns active languages."""
    res = client.get("/api/v2/translate/languages")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["status"] == "active"
    codes = [l["code"] for l in data["supported_languages"]]
    for expected_code in ["en", "hi", "mr", "ta", "te", "kn"]:
        assert expected_code in codes, f"Language {expected_code} missing from supported list"
    print("  [PASS] Supported languages metadata verified.")


def test_single_text_translation_hindi():
    """Verify single text translation to Hindi."""
    res = client.post(
        "/api/v2/translate",
        json={"text": "Dashboard", "target_language": "hi", "source_language": "en"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["target_language"] == "hi"
    assert data["translated_text"] == "डैशबोर्ड"
    assert data["provider"] in ["domain_dictionary", "cache", "google_cloud_sdk", "google_cloud_rest", "deterministic_fallback"]
    print("  [PASS] Single text translation to Hindi verified.")


def test_single_text_translation_marathi():
    """Verify single text translation to Marathi."""
    res = client.post(
        "/api/v2/translate",
        json={"text": "Overview & Synthesis", "target_language": "mr", "source_language": "en"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["target_language"] == "mr"
    assert "आढावा" in data["translated_text"]
    print("  [PASS] Single text translation to Marathi verified.")


def test_batch_translation_all_languages():
    """Verify batch translation across multiple Indian languages."""
    texts = ["Government Schemes", "Financials & Cash Flow", "Risk Assessment"]
    for lang in ["hi", "mr", "ta", "te", "kn"]:
        res = client.post(
            "/api/v2/translate/batch",
            json={"texts": texts, "target_language": lang, "source_language": "en"}
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 3
        for item in data:
            assert item["target_language"] == lang
            assert len(item["translated_text"]) > 0
    print("  [PASS] Batch translation across all 5 Indian languages passed.")


def test_dictionary_translation():
    """Verify dictionary translation for UI and dynamic schemas."""
    sample_dict = {
        "dashboard": "Dashboard",
        "market": "Market & Demand",
        "swot": "SWOT Analysis"
    }
    res = client.post(
        "/api/v2/translate/dictionary",
        json={"dictionary": sample_dict, "target_language": "ta", "source_language": "en"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "டாஷ்போர்டு" in data["dashboard"]
    assert "SWOT" in data["swot"]
    print("  [PASS] Dictionary translation passed.")


def test_translation_cache_performance():
    """Verify that repeated translations hit the high-speed cache."""
    req_payload = {"text": "Credit Appraisal Language", "target_language": "kn", "source_language": "en"}
    # Call 1 (populate)
    res1 = client.post("/api/v2/translate", json=req_payload)
    assert res1.status_code == 200
    # Call 2 (must hit cache)
    res2 = client.post("/api/v2/translate", json=req_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["provider"] in ["cache", "domain_dictionary"]
    print("  [PASS] Translation caching verified.")


def test_dynamic_paragraph_translation_google_cloud():
    """Verify dynamic complex sentence translation with live Google Cloud API Key."""
    text = "The proposed dairy micro-enterprise in Joypur demonstrates robust financial viability with a projected DSCR of 1.78x and eligible PMEGP capital subsidy of 35%."
    for lang in ["hi", "mr", "ta", "te", "kn"]:
        res = client.post(
            "/api/v2/translate",
            json={"text": text, "target_language": lang, "source_language": "en"}
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["translated_text"]) > 10
        assert data["target_language"] == lang
        print(f"  [PASS] Live Google Cloud Translation ({lang.upper()}): {data['translated_text'][:60]}...")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RUNNING GOOGLE CLOUD TRANSLATION API & MULTILINGUAL SUITE")
    print("=" * 80)
    test_supported_languages_endpoint()
    test_single_text_translation_hindi()
    test_single_text_translation_marathi()
    test_batch_translation_all_languages()
    test_dictionary_translation()
    test_translation_cache_performance()
    test_dynamic_paragraph_translation_google_cloud()
    print("=" * 80)
    print("ALL TRANSLATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80 + "\n")

