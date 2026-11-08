from fastapi import APIRouter, Depends, Query
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.odop_hybrid import district_context, hybrid_evaluator
from app.models.odop_hybrid import HybridRequest

router = APIRouter(prefix="/odop-hybrid", tags=["Optional ODOP hybrid advice"])


@router.get("/context")
async def context(state_name: str = Query(min_length=1, max_length=100), district_name: str = Query(min_length=1, max_length=100), user: AuthenticatedUser = Depends(get_current_user)):
    return district_context(state_name.strip(), district_name.strip())


@router.post("/evaluate")
async def evaluate(request: HybridRequest, user: AuthenticatedUser = Depends(get_current_user)):
    return await hybrid_evaluator.evaluate(user.uid, request)
