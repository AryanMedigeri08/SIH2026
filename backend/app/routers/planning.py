"""Evaluate before recommendation; selection persists the cached appraisal."""
import logging
import time
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.enterprise_planning import build_plans, business_choices, sessions
from app.models.planning import AcceptPlan, PlanningRequest
from app.core.planning_drafts import draft_store
from app.core.planning_selection import save_selected_plan
from app.models.schemas import ProjectModel

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
        return {"draft_id": draft_id, "expires_in_seconds": 1800,
                **{key: value for key, value in result.items() if not key.startswith("_")}}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Could not store planning preview")
        raise HTTPException(503, "Could not save this preview. Please compare plans again; no business was created.")
    finally:
        sessions.busy.discard(current_user.uid)


@router.post("/{draft_id}/accept", response_model=ProjectModel)
async def accept(draft_id: str, request: AcceptPlan, current_user: AuthenticatedUser = Depends(get_current_user)):
    try:
        draft = await draft_store.get(current_user.uid, draft_id)
        selection = sessions.accept(current_user.uid, draft_id, request, draft=draft)
        return await save_selected_plan(current_user.uid, draft_id, selection)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Could not load planning preview")
        raise HTTPException(503, "Could not finish saving this business. Retry this selection; your appraisal will be reused.")


@router.get('/{draft_id}')
async def saved_preview(draft_id: str, current_user: AuthenticatedUser = Depends(get_current_user)):
    draft = await draft_store.get(current_user.uid, draft_id)
    if draft.expires_at < time.time():
        raise HTTPException(410, 'This preview has expired. Please explicitly compare your plans again.')
    return {'draft_id': draft_id, 'expires_in_seconds': max(0, int(draft.expires_at - time.time())),
            **{key: value for key, value in draft.result.items() if not key.startswith('_')}}
