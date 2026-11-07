"""Authenticated previews; all persistent creation still uses the existing wizard."""
import logging
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.enterprise_planning import build_plans, business_choices, sessions
from app.models.planning import AcceptPlan, PlanningRequest
from app.core.planning_drafts import draft_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/planning", tags=["Enterprise planning"])


@router.get("/businesses")
async def list_businesses(current_user: AuthenticatedUser = Depends(get_current_user)):
    return business_choices()


@router.post("/evaluate")
async def evaluate(request: PlanningRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    sessions.start(current_user.uid)
    try:
        result = await build_plans(request)
        draft_id = await draft_store.save(current_user.uid, request, result)
        return {"draft_id": draft_id, "expires_in_seconds": 1800, **result}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Could not store planning preview")
        raise HTTPException(503, "Could not save this preview. Please compare plans again; no business was created.")
    finally:
        sessions.busy.discard(current_user.uid)


@router.post("/{draft_id}/accept")
async def accept(draft_id: str, request: AcceptPlan, current_user: AuthenticatedUser = Depends(get_current_user)):
    try:
        draft = await draft_store.get(current_user.uid, draft_id)
        return sessions.accept(current_user.uid, draft_id, request, draft=draft)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Could not load planning preview")
        raise HTTPException(503, "Could not load this preview. Please retry; no business was created.")
