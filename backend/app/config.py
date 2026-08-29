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


class Settings(BaseSettings):
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

    class Config:
        case_sensitive = True


settings = Settings()
