"""
config.py — Backend application configuration and environment settings.
"""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


class Settings(BaseSettings):
    APP_NAME: str = "Udyam Saathi REST API"
    APP_VERSION: str = "2.0.0"
    API_V2_STR: str = "/api/v2"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Groq AI Model Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    # 613 Village Amenities API (Data.gov.in / Mission Antyodaya OGD API)
    DATA_GOV_IN_API_KEY: str = os.getenv("DATA_GOV_IN_API_KEY", os.getenv("AMENITIES_API_KEY", ""))
    AMENITIES_API_BASE_URL: str = os.getenv("AMENITIES_API_BASE_URL", "https://api.data.gov.in/resource")

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    # Data & Model paths
    DATA_DIR: Path = Path(__file__).resolve().parent / "data"
    SCHEMES_FILE: Path = Path(__file__).resolve().parent / "data" / "government_schemes.json"
    GROWTH_RATES_FILE: Path = Path(__file__).resolve().parent / "data" / "growth_rates.json"
    MODEL_FILE: Path = Path(__file__).resolve().parent / "data" / "viability_xgb.joblib"
    METADATA_FILE: Path = Path(__file__).resolve().parent / "data" / "model_metadata.json"

    class Config:
        case_sensitive = True


settings = Settings()
