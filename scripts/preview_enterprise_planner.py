"""Local-only synthetic UI fixture. No production DB, provider, email or GPS calls.

Run: venv/Scripts/python.exe scripts/preview_enterprise_planner.py
Then run Vite on port 3001 and use the evaluator login. All records are ephemeral.
"""
import sys
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "backend", ROOT / "backend/app/core"):
    sys.path.insert(0, str(folder))

from fastapi import FastAPI
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core import enterprise_planning as planner
from app.routers.planning import router
from app.routers.projects import router as projects_router
from app.routers.odop_hybrid import router as odop_hybrid_router
from app.core import odop_hybrid
from app.routers.onboarding import router as onboarding_router
from app.core import onboarding_location
from tests.test_planning_financial_baseline import frozen_evidence

app = FastAPI()
app.include_router(router, prefix="/api/v2")
app.include_router(projects_router, prefix="/api/v2")
app.include_router(odop_hybrid_router, prefix="/api/v2")
app.include_router(onboarding_router, prefix="/api/v2")
app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="synthetic-planner-preview")
profile = {"firebase_uid": "synthetic-planner-preview", "name": "Test Entrepreneur", "email": "preview@example.test",
           "gender": "Male", "promoter_category": "general", "auth_provider": "demo", "projects_count": 0, "preferred_language": "en"}

hybrid_completion = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
    "score": 85, "summary": "Synthetic preview: food-safe packaging can link the dairy idea to local pottery. Verify safety, costs and demand.",
    "hybrid_name": "Curd in locally made food-safe clay pots",
    "hybrid_description": "Make curd and source food-safe clay pots from local artisans. Test hygiene, breakage, price and customer demand before launch.",
    "reasons": ["Connects the original dairy activity to a local packaging supplier."],
    "practical_steps": ["Confirm food-safe pots and compare packaging costs."],
    "risks": ["Breakage and food safety need checks."], "missing_information": ["Verified customer demand"]
})))]))
hybrid_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=hybrid_completion)))


@app.get("/api/v2/preview/odop-calls")
async def odop_calls():
    return {"calls": hybrid_completion.call_count}


@app.post("/api/v2/auth/register")
@app.post("/api/v2/auth/session")
@app.get("/api/v2/auth/me")
@app.patch("/api/v2/auth/me")
async def auth():
    return profile


@app.post('/api/v2/chat/tts')
async def synthetic_tts():
    return {'audio_base64': '', 'language': 'en', 'latency_s': 0}


async def synthetic_options(level, **parents):
    return {'states': ['West Bengal'], 'districts': ['Bankura'], 'blocks': ['Test block'], 'villages': ['Test village']}[level]


@app.get("/api/v2/health")
async def health():
    return {"status": "synthetic_preview", "database_connected": False}


@app.get("/api/v2/locations/{level}")
async def locations(level: str):
    return {
        "states": [{"state_name": "West Bengal", "state_code": 19}],
        "districts": [{"district_name": "Bankura", "district_code": 312}],
        "blocks": [{"development_block_name": "Test block", "development_block_code": 101}],
        "villages": [{"village_name": "Test village", "village_code": 1001}],
        "odop": {"has_odop_record": False},
    }.get(level, [])


@app.get("/api/v2/financial/machinery-schedule")
async def machinery(project_cost: float = 1000000, sector: str = "dairy", enterprise_name: str = "Test enterprise", business_category: str = "manufacturing"):
    from machinery_engine import extract_contextual_machinery
    return extract_contextual_machinery(enterprise_name=enterprise_name, sector=sector,
        business_category=business_category, allocated_machinery_budget=project_cost * .55, use_ai=False).to_dict()


if __name__ == "__main__":
    import uvicorn
    region = {"recommendation": "INSUFFICIENT_DATA", "composite_score": 0, "confidence": "INSUFFICIENT_DATA",
              "evidence": {"missing_evidence": ["Synthetic fixture: customer demand and competition are not verified."]},
              "supply_metrics": {}, "demand_features": {}, "data_lineage": []}
    from app.routers import onboarding
    from app.core import onboarding_intent
    with frozen_evidence(), patch.object(planner, "evaluate_region", AsyncMock(return_value=region)), patch.object(planner, "_get_groq_client", return_value=None), patch.object(odop_hybrid, "_get_groq_client", return_value=hybrid_client), patch.object(onboarding_location, 'location_options', synthetic_options), patch.object(onboarding, 'location_options', synthetic_options), patch.object(onboarding_intent, '_get_groq_client', return_value=None):
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
