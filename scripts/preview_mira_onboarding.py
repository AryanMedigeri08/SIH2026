"""Isolated UI smoke fixture. No live database, location, LLM or speech requests.

Run: venv/Scripts/python.exe scripts/preview_mira_onboarding.py
Uses synthetic locations clearly labelled Test, an in-memory DB, and the real
onboarding/API/financial code. Never use this fixture server as a deployment.
"""
import os
import sqlite3
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.main import app
from app.config import settings
from app.database import db_manager
from app.routers import onboarding as api
from app.core import onboarding as engine
from app.core.chat_service import ChatService

for key in list(os.environ):
    if key.startswith(("GROQ_", "SARVAM_", "BHASHINI_", "DATA_GOV_", "AMENITIES_")):
        os.environ.pop(key, None)
for key in type(settings).model_fields:
    if key.endswith("API_KEY") or "GROQ" in key or "BHASHINI" in key:
        if "KEY" in key or "USER_ID" in key:
            setattr(settings, key, None if key not in ("GROQ_API_KEY", "DATA_GOV_IN_API_KEY") else "")
settings.DATABASE_URL = ""
settings.ALLOW_TEST_AUTH = True
ChatService._get_api_key = lambda self: None


@asynccontextmanager
async def lifespan(_):
    db_manager.pool = None
    db_manager.sqlite = sqlite3.connect(":memory:", check_same_thread=False)
    db_manager.sqlite.row_factory = sqlite3.Row
    db_manager.sqlite.executescript('''PRAGMA foreign_keys=ON;
        CREATE TABLE users(firebase_uid TEXT PRIMARY KEY,email TEXT,name TEXT,gender TEXT,promoter_category TEXT,auth_provider TEXT,phone TEXT,additional_business_details TEXT,language TEXT,created_at TEXT,updated_at TEXT,last_login_at TEXT);
        CREATE TABLE onboarding_sessions(user_id TEXT PRIMARY KEY REFERENCES users(firebase_uid) ON DELETE CASCADE,revision INTEGER,payload TEXT);
        CREATE TABLE revoked_sessions(token_hash TEXT PRIMARY KEY,user_id TEXT,revoked_at TEXT);
        CREATE TABLE projects(project_id TEXT PRIMARY KEY,user_id TEXT,payload TEXT,created_at TEXT,updated_at TEXT);
        CREATE TABLE feasibility_reports(report_id TEXT PRIMARY KEY,user_id TEXT,payload TEXT,created_at TEXT);
    ''')
    yield
    db_manager.sqlite.close()


class FixtureLocation:
    def __init__(self, _):
        pass
    async def options(self, level, parent=None, search=""):
        parent = parent or 0
        return {
            "states": [{"state_code": 27, "state_name": "Maharashtra"}, {"state_code": 29, "state_name": "Karnataka"}],
            "districts": [{"district_code": 490 if parent == 27 else 540, "district_name": "Pune" if parent == 27 else "Mysuru", "state_code": parent}],
            "blocks": [{"development_block_code": parent * 10, "development_block_name": "Test development block", "district_code": parent}],
            "villages": [{"village_code": parent * 10, "village_name": "Test village (synthetic fixture)"}],
        }[level]
    async def select(self, selection):
        if selection.block_code != selection.district_code * 10 or selection.village_code != selection.block_code * 10:
            raise ValueError("Invalid test hierarchy")
        return {"state_code": selection.state_code, "district_code": selection.district_code, "block_code": selection.block_code,
                "village_code": selection.village_code, "state_name": "Maharashtra" if selection.state_code == 27 else "Karnataka",
                "district_name": "Pune" if selection.state_code == 27 else "Mysuru", "block_name": "Test development block",
                "village_name": "Test village (synthetic fixture)", "is_rural": True, "area_source": "SYNTHETIC_TEST_FIXTURE",
                "latitude": None, "longitude": None}
    async def detect(self, _):
        raise ValueError("GPS disabled in the isolated test fixture. Choose the synthetic business location below.")


async def region(state):
    return {"evidence": {"confidence": "INSUFFICIENT_DATA", "plain_language_summary": "Synthetic UI fixture — no real regional suitability conclusion.",
                         "data_quality_limitations": ["Test data only"]}, "location": state["location"]}


api.OnboardingLocation = FixtureLocation
engine.regional_assessment = region
engine.find_district_odop = lambda *_: None
app.router.lifespan_context = lifespan

async def disabled_speech(**kwargs):
    from fastapi import HTTPException
    raise HTTPException(503, "Live speech providers are disabled in this isolated preview. Type your answer to continue.")

for route in app.routes:
    if getattr(route, "path", "") in ("/api/v2/chat/stt", "/api/v2/chat/tts", "/api/v2/chat/audio", "/api/v2/chat/voice", "/api/v2/chat/voice-agent"):
        route.dependant.call = disabled_speech

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
