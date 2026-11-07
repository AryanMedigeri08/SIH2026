"""Local-only synthetic UI fixture. No production DB, provider, email or GPS calls.

Run: venv/Scripts/python.exe scripts/preview_enterprise_planner.py
Then run Vite on port 3001 and use the evaluator login. All records are ephemeral.
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "backend", ROOT / "backend/app/core"):
    sys.path.insert(0, str(folder))

from fastapi import FastAPI
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core import enterprise_planning as planner
from app.routers.planning import router
from app.routers.projects import router as projects_router
from tests.test_planning_financial_baseline import frozen_evidence

app = FastAPI()
app.include_router(router, prefix="/api/v2")
app.include_router(projects_router, prefix="/api/v2")
app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="synthetic-planner-preview")
profile = {"firebase_uid": "synthetic-planner-preview", "name": "Test Entrepreneur", "email": "preview@example.test",
           "gender": "Male", "auth_provider": "demo", "projects_count": 0, "preferred_language": "en"}


@app.post("/api/v2/auth/register")
@app.post("/api/v2/auth/session")
@app.get("/api/v2/auth/me")
async def auth():
    return profile


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
    with frozen_evidence(), patch.object(planner, "evaluate_region", AsyncMock(return_value=region)):
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
