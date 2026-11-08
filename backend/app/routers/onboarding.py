import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.onboarding_store import onboarding_store
from app.core.onboarding_location import resolve_gps, validate_location, location_options
from app.models.onboarding import OnboardingDraft, OnboardingLocation, GpsRequest

router = APIRouter(prefix='/onboarding', tags=['Mira onboarding'])
ALLOWED_ANSWERS = {'idea', 'idea_confirmed', 'business_id', 'sector', 'business_category', 'own_cash',
    'cash_confirmed', 'premise_type', 'monthly_rent', 'skills', 'resources', 'preferences',
    'equipment_quote', 'project_cost', 'annual_sales', 'enterprise_name', 'review_confirmed', 'odop_choice'}
gps_requests = {}


@router.get('/session')
async def get_session(user: AuthenticatedUser = Depends(get_current_user)):
    return await onboarding_store.get(user.uid) or OnboardingDraft().model_dump()


@router.put('/session')
async def save_session(draft: OnboardingDraft, user: AuthenticatedUser = Depends(get_current_user)):
    if set(draft.answers) - ALLOWED_ANSWERS or any(isinstance(v, str) and len(v) > 1000 for v in draft.answers.values()):
        raise HTTPException(422, 'Only supported business answers can be saved.')
    if draft.location and draft.location.confirmed:
        await validate_location(draft.location)
    return await onboarding_store.save(user.uid, draft.model_dump())


@router.post('/location/detect')
async def detect_location(gps: GpsRequest, user: AuthenticatedUser = Depends(get_current_user)):
    now = time.monotonic()
    if now - gps_requests.get(user.uid, -100) < 10:
        raise HTTPException(429, 'Please wait before detecting location again.')
    gps_requests[user.uid] = now
    if len(gps_requests) > 1000:
        gps_requests.clear(); gps_requests[user.uid] = now
    try:
        location = await resolve_gps(gps.latitude, gps.longitude)
    except Exception:
        location = {**gps.model_dump(), 'source': 'gps', 'confirmed': False}
    draft = await onboarding_store.get(user.uid) or OnboardingDraft().model_dump()
    if not (draft.get('location') or {}).get('confirmed'):
        draft['location'] = location
        await onboarding_store.save(user.uid, draft)
    return location


@router.get('/locations/{level}')
async def options(level: str, state: str = Query('', max_length=100), district: str = Query('', max_length=100),
                  block: str = Query('', max_length=100), user: AuthenticatedUser = Depends(get_current_user)):
    if level not in {'states', 'districts', 'blocks', 'villages'}:
        raise HTTPException(404, 'Unknown location level.')
    return await location_options(level, state, district, block)


@router.post('/location/confirm')
async def confirm_location(location: OnboardingLocation, user: AuthenticatedUser = Depends(get_current_user)):
    location.confirmed = True
    resolved = await validate_location(location)
    draft = await onboarding_store.get(user.uid) or OnboardingDraft().model_dump()
    draft['location'] = location.model_dump()
    draft['answers'] = {}  # location change invalidates a prior business appraisal
    await onboarding_store.save(user.uid, draft)
    return resolved
