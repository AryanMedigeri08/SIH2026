"""Authenticated previews; all persistent creation still uses the existing wizard."""
from fastapi import APIRouter, Depends

from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.enterprise_planning import build_plans, business_choices, sessions
from app.models.planning import AcceptPlan, PlanningRequest

router = APIRouter(prefix="/planning", tags=["Enterprise planning"])


@router.get("/businesses")
async def list_businesses(current_user: AuthenticatedUser = Depends(get_current_user)):
    return business_choices()


@router.post("/evaluate")
async def evaluate(request: PlanningRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    sessions.start(current_user.uid)
    try:
        result = await build_plans(request)
        draft_id = sessions.save(current_user.uid, request, result)
        return {"draft_id": draft_id, "expires_in_seconds": 1800, **result}
    finally:
        sessions.busy.discard(current_user.uid)


@router.post("/{draft_id}/accept")
async def accept(draft_id: str, request: AcceptPlan, current_user: AuthenticatedUser = Depends(get_current_user)):
    return sessions.accept(current_user.uid, draft_id, request)
