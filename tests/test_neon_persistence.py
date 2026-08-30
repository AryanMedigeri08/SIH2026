"""Opt-in integration test for the configured Neon/PostgreSQL database.

Run only with DATABASE_URL configured.  It writes scoped fixtures, verifies a
fresh read after clearing process memory, and removes only its own users (with
their cascading projects/reports) in ``finally``.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
import asyncpg

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
for path in (str(BACKEND), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.database import DatabaseManager
from app.config import settings


USER_ID = "integration_neon_persistence_user"
OTHER_USER_ID = "integration_neon_isolation_user"


async def verify_neon_persistence() -> None:
    if not settings.DATABASE_URL or "user:password" in settings.DATABASE_URL:
        print("[SKIP] DATABASE_URL not configured for live Neon integration test.")
        return

    manager = DatabaseManager()
    try:
        manager.pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=1, max_size=1, timeout=8)
    except Exception as e:
        print(f"[SKIP] Could not connect to Neon database ({e}); skipping live integration test.")
        return

    try:
        profile = await manager.upsert_user(USER_ID, "neon.persistence@example.com", "Neon Persistence User", phone="9999999999", language="hi")
        assert profile["language"] == "hi"

        await manager.update_user(USER_ID, {"language": "ta"})
        manager.in_memory_users.clear()
        assert (await manager.get_user(USER_ID))["language"] == "ta"

        base = {
            "user_id": USER_ID,
            "business_category": "manufacturing",
            "investment_amount": 500000,
            "annual_turnover_estimate": 760000,
            "state_name": "West Bengal",
            "district_name": "Bankura",
            "block_name": "Joypur",
            "village_name": "Joypur",
            "promoter_name": "Neon Persistence User",
            "promoter_category": "general",
            "gender": "Unspecified",
            "is_rural": True,
            "tenure_years": 5,
            "moratorium_months": 6,
            "language": "ta",
            "status": "draft",
        }
        one = await manager.create_project({**base, "project_id": "neon_project_one", "business_name": "Neon Enterprise One", "sector": "dairy"})
        two = await manager.create_project({**base, "project_id": "neon_project_two", "business_name": "Neon Enterprise Two", "sector": "food_processing"})
        assert one["project_id"] != two["project_id"]

        manager.in_memory_projects.clear()
        restored = await manager.list_projects(USER_ID)
        assert {project["business_name"] for project in restored} == {"Neon Enterprise One", "Neon Enterprise Two"}
        assert {project["sector"] for project in restored} == {"dairy", "food_processing"}

        analysis = {"report": {"report_id": "neon-report", "summary": "persisted"}, "dpr": {"title": "persisted"}}
        await manager.update_project_analysis("neon_project_one", analysis)
        manager.in_memory_projects.clear()
        assert (await manager.get_project("neon_project_one"))["analysis_result"]["report"]["report_id"] == "neon-report"

        await manager.save_feasibility_report("neon-report", analysis, USER_ID)
        manager.in_memory_reports.clear()
        assert (await manager.get_feasibility_report("neon-report", USER_ID))["report"]["summary"] == "persisted"
        assert await manager.get_feasibility_report("neon-report", OTHER_USER_ID) is None
        print("PASS: Neon user, two enterprises, analysis/report ownership, and language preference persist after memory reset.")
    finally:
        # This cascades only fixtures owned by these test users; no schema or
        # unrelated application data is touched.
        await manager.delete_user(USER_ID)
        await manager.delete_user(OTHER_USER_ID)
        await manager.close()


if __name__ == "__main__":
    asyncio.run(verify_neon_persistence())
