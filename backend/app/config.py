"""
config.py — Backend application configuration and environment settings.
"""

from __future__ import annotations
import os
import json
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


def _parse_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS")
    default_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    if not raw:
        return default_origins

    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                # Filter out wildcard "*" to avoid invalid CORS with allow_credentials=True
                return [str(o).strip() for o in parsed if str(o).strip() and str(o).strip() != "*"]
        except Exception:
            pass

    origins = [o.strip() for o in raw.split(",") if o.strip() and o.strip() != "*"]
    return origins if origins else default_origins


from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True, extra="ignore")

    APP_NAME: str = "Udyam Saathi REST API"
    APP_VERSION: str = "2.0.0"
    API_V2_STR: str = "/api/v2"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Firebase Admin Configuration (Server-Side Auth)
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", None)
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", None)
    FIREBASE_PROJECT_ID: Optional[str] = os.getenv("FIREBASE_PROJECT_ID", None)

    # Groq AI Model & Dedicated Chatbot Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_CHAT_KEY: Optional[str] = os.getenv("GROQ_CHAT_KEY", None)
    GROQ_API_KEY_STT: Optional[str] = os.getenv("GROQ_API_KEY_STT", None)
    GROQ_API_KEY_LLM: Optional[str] = os.getenv("GROQ_API_KEY_LLM", None)
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    GROQ_STT_MODEL: str = os.getenv("GROQ_STT_MODEL", "whisper-large-v3")
    GROQ_LLM_MODEL: str = os.getenv("GROQ_LLM_MODEL", "openai/gpt-oss-20b")

    # Sarvam AI — Language Detection Layer (V3: Detection-only, 22 Indic Languages)
    SARVAM_API_KEY: Optional[str] = os.getenv("SARVAM_API_KEY", None)
    SARVAM_STT_ENDPOINT: str = os.getenv("SARVAM_STT_ENDPOINT", os.getenv("SARVAM_ASR_ENDPOINT", "https://api.sarvam.ai/speech-to-text"))
    SARVAM_ASR_ENDPOINT: str = os.getenv("SARVAM_ASR_ENDPOINT", "https://api.sarvam.ai/speech-to-text")
    SARVAM_TTS_ENDPOINT: str = os.getenv("SARVAM_TTS_ENDPOINT", "https://api.sarvam.ai/text-to-speech")

    # Bhashini AI — Primary ASR / STT & TTS Layer (V3: 100% of speech transcription & synthesis)
    BHASHINI_USER_ID: Optional[str] = os.getenv("BHASHINI_USER_ID", None)
    BHASHINI_API_KEY: Optional[str] = os.getenv("BHASHINI_API_KEY", None)
    BHASHINI_CONFIG_ENDPOINT: str = os.getenv("BHASHINI_CONFIG_ENDPOINT", "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline")
    BHASHINI_PIPELINE_ID: str = os.getenv("BHASHINI_PIPELINE_ID", "64392f96daac500b55c543cd")
    BHASHINI_CONFIG_CACHE_TTL_SECONDS: int = int(os.getenv("BHASHINI_CONFIG_CACHE_TTL_SECONDS", "3600"))

    # Voice Cascade Controller
    VOICE_CASCADE_TIMEOUT_MS: int = int(os.getenv("VOICE_CASCADE_TIMEOUT_MS", "4000"))
    VOICE_FALLBACK_SUPPORTED_LANGS: str = os.getenv("VOICE_FALLBACK_SUPPORTED_LANGS", "en,hi,mr,bn,gu,ta,te,kn,pa,ur")

    # 613 Village Amenities API (Data.gov.in / Mission Antyodaya OGD API)
    DATA_GOV_IN_API_KEY: str = os.getenv("DATA_GOV_IN_API_KEY", os.getenv("AMENITIES_API_KEY", ""))
    AMENITIES_API_BASE_URL: str = os.getenv("AMENITIES_API_BASE_URL", "https://api.data.gov.in/resource")

    # CORS Explicit Allow-List (Driven by ALLOWED_ORIGINS)
    CORS_ORIGINS: list[str] = _parse_origins()

    # Data & Model paths
    DATA_DIR: Path = Path(__file__).resolve().parent / "data"
    SCHEMES_FILE: Path = Path(__file__).resolve().parent / "data" / "government_schemes.json"
    GROWTH_RATES_FILE: Path = Path(__file__).resolve().parent / "data" / "growth_rates.json"
    MODEL_FILE: Path = Path(__file__).resolve().parent / "data" / "viability_xgb.joblib"
    METADATA_FILE: Path = Path(__file__).resolve().parent / "data" / "model_metadata.json"


settings = Settings()


def validate_production_config() -> dict[str, Any]:
    """
    Safely validates presence of essential production files and environment configuration
    without exposing or logging any plaintext secrets. (Document 4, Phase 2).
    """
    status_report = {
        "status": "VALID",
        "missing_critical": [],
        "warnings": [],
        "modes": {},
    }

    # Verify critical data files
    if not settings.DATA_DIR.exists():
        status_report["missing_critical"].append("backend/app/data directory missing")
    if not settings.SCHEMES_FILE.exists():
        status_report["missing_critical"].append("government_schemes.json missing")
    if not settings.GROWTH_RATES_FILE.exists():
        status_report["missing_critical"].append("growth_rates.json missing")

    # Database status
    if settings.DATABASE_URL and settings.DATABASE_URL.strip():
        status_report["modes"]["database"] = "POSTGRESQL_NEON"
    else:
        status_report["modes"]["database"] = "LOCAL_SQLITE_DURABLE"
        status_report["warnings"].append("DATABASE_URL not set; using local durable SQLite storage")

    # LLM API status
    if settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip():
        status_report["modes"]["llm_synthesis"] = "GROQ_CLOUD_ACTIVE"
    else:
        status_report["modes"]["llm_synthesis"] = "DETERMINISTIC_RULE_FALLBACK"
        status_report["warnings"].append("GROQ_API_KEY not configured; rule-based synthesis active")

    # Data.gov.in status
    if settings.DATA_GOV_IN_API_KEY and settings.DATA_GOV_IN_API_KEY.strip():
        status_report["modes"]["amenities_api"] = "DATA_GOV_IN_ACTIVE"
    else:
        status_report["modes"]["amenities_api"] = "REGIONAL_BASELINE_FALLBACK"

    # ML Classifier binary
    if settings.MODEL_FILE.exists():
        status_report["modes"]["viability_classifier"] = "XGBOOST_SUPERVISED_ACTIVE"
    else:
        status_report["modes"]["viability_classifier"] = "DETERMINISTIC_RULES_ACTIVE"

    if status_report["missing_critical"]:
        status_report["status"] = "INVALID"

    return status_report
