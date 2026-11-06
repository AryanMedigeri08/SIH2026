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
from app.core.translation_service import TranslationService
async def no_external_translation(self, text, target_language='hi', source_language='en', **_):
    return {'translated_text':text,'provider':'identity'}
TranslationService.translate_text = no_external_translation


@asynccontextmanager
async def lifespan(_):
    db_manager.pool = None
    db_manager.sqlite = sqlite3.connect(":memory:", check_same_thread=False)
    db_manager.sqlite.row_factory = sqlite3.Row
    db_manager.sqlite.executescript('''PRAGMA foreign_keys=ON;
        CREATE TABLE users(firebase_uid TEXT PRIMARY KEY,email TEXT,name TEXT,gender TEXT,promoter_category TEXT,auth_provider TEXT,phone TEXT,additional_business_details TEXT,language TEXT,created_at TEXT,updated_at TEXT,last_login_at TEXT);
        CREATE TABLE onboarding_sessions(user_id TEXT PRIMARY KEY REFERENCES users(firebase_uid) ON DELETE CASCADE,revision INTEGER,payload TEXT);
        CREATE TABLE revoked_sessions(token_hash TEXT PRIMARY KEY,user_id TEXT,revoked_at TEXT);
        CREATE TABLE evaluator_sessions(token_hash TEXT PRIMARY KEY,user_id TEXT,expires_at REAL);
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
        result = {"state_code": selection.state_code, "district_code": selection.district_code, "block_code": selection.block_code,
                "village_code": selection.village_code, "state_name": "Maharashtra" if selection.state_code == 27 else "Karnataka",
                "district_name": "Pune" if selection.state_code == 27 else "Mysuru", "block_name": "Test development block",
                "village_name": "Test village (synthetic fixture)", "is_rural": selection.state_code==27, "area_source": "SYNTHETIC_TEST_FIXTURE",
                "latitude": None, "longitude": None}
        from app.core.area_classification import classify_area
        result['area_classification'] = classify_area(result,[{'total_population':7000,'main_workers':2000,
            'main_cultivators':500,'main_agri_labourers':100}],{'available':True,'source':'SYNTHETIC_TEST_FIXTURE',
            'indicators':{'road':True,'banking':True,'internet':True,'market_or_storage':False,'power_hours':20}})
        result['area_classification']['source']='SYNTHETIC_TEST_FIXTURE'
        result['area_classification']['local_body_type']='Synthetic fixture — not live village evidence'
        return result
    async def detect(self, _):
        raise ValueError("GPS disabled in the isolated test fixture. Choose the synthetic business location below.")


async def region(state):
    return {"evidence": {"confidence": "INSUFFICIENT_DATA", "plain_language_summary": "Synthetic UI fixture — no real regional suitability conclusion.",
                         "data_quality_limitations": ["Test data only"]}, "location": state["location"]}


api.OnboardingLocation = FixtureLocation
engine.regional_assessment = region
engine.find_district_odop = lambda *_: None

# Optional isolated visual fixture; never touches real account or location data.
if '--area-demo' in sys.argv:
    original_upsert = db_manager.upsert_user
    async def area_demo_user(*args, **kwargs):
        profile = await original_upsert(*args, **kwargs)
        if kwargs.get('auth_provider') == 'evaluator' and not await db_manager.get_onboarding(profile['firebase_uid']):
            profile = await db_manager.update_user(profile['firebase_uid'], {'name':'Synthetic demo user','gender':'Female',
                'promoter_category':'obc','phone':'+919999999999','email':'demo@example.com'})
            from app.models.onboarding import new_session, LocationSelection
            state = new_session(profile)
            state['experience'] = 'adaptive'
            state['location'] = await FixtureLocation(None).select(LocationSelection(revision=0,state_code=27,district_code=490,block_code=4900,village_code=49000))
            await engine.advance(state)
            await db_manager.save_onboarding(profile['firebase_uid'],state)
        return profile
    db_manager.upsert_user = area_demo_user

# The imported voice onboarding uses the existing public location dropdown API.
async def fixture_states(**_):
    return [{"state_code": 27, "state_name": "Maharashtra", "state_or_ut": "State"},
            {"state_code": 29, "state_name": "Karnataka", "state_or_ut": "State"}]

async def fixture_districts(**kwargs):
    is_maharashtra = kwargs.get("state_name") == "Maharashtra" or kwargs.get("state_code") == 27
    return [{"district_code": 490 if is_maharashtra else 540,
             "district_name": "Pune" if is_maharashtra else "Mysuru", "state_code": 27 if is_maharashtra else 29}]

async def fixture_blocks(**_):
    return [{"development_block_code": 4900, "development_block_name": "Test development block", "district_code": 490}]

async def fixture_villages(**_):
    return [{"village_code": 49000, "village_name": "Test village (synthetic fixture)", "district_code": 490}]

db_manager.get_states = fixture_states
db_manager.get_districts = fixture_districts
db_manager.get_blocks = fixture_blocks
db_manager.get_villages = fixture_villages
app.router.lifespan_context = lifespan

@app.middleware("http")
async def disabled_speech(request, call_next):
    # Intercept before routing, including FastAPI's nested included routers.
    if request.url.path in ("/api/v2/chat/stt", "/api/v2/chat/tts", "/api/v2/chat/audio", "/api/v2/chat/voice", "/api/v2/chat/voice-agent"):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"detail": "Live speech providers are disabled in this isolated preview. Type your answer to continue."})
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
