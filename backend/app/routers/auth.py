"""
auth.py — REST API Router for User Authentication, Firebase Session Sync, and Profile Management.
"""

from __future__ import annotations
import logging
import re
import secrets
import time
import uuid
from collections import defaultdict, deque
from fastapi import Request
from pydantic import BaseModel, Field
from typing import Literal
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse

from app.database import db_manager
from app.models.schemas import UserRegisterRequest, UserUpdateRequest, UserProfileResponse
from app.core.auth_dependency import get_current_user, AuthenticatedUser, token_fingerprint
from app.core.firebase_admin_client import firebase_auth

logger = logging.getLogger("udyam_saathi.routers.auth")

router = APIRouter(prefix="/auth", tags=["User Authentication & Profile"])
_evaluator_requests = defaultdict(deque)


def profile_email(record):
    email = record.get('email')
    return None if not email or email.endswith('@evaluator.invalid') or email == f"{record['firebase_uid']}@udyam.gov.in" else email


@router.post('/evaluator', status_code=201)
async def create_evaluator_session(request: Request):
    """Issue a scoped, expiring identity; never accepts a client-chosen user ID."""
    now = time.time()
    ip = request.client.host if request.client else 'unknown'
    recent = _evaluator_requests[ip]
    while recent and recent[0] < now - 60:
        recent.popleft()
    if len(recent) >= 10:
        raise HTTPException(429, 'Please wait a minute before starting another evaluator session.')
    recent.append(now)
    uid = 'eval_' + uuid.uuid4().hex
    token = 'ev1_' + secrets.token_urlsafe(32)
    expires = now + 8 * 60 * 60
    try:
        await db_manager.upsert_user(uid, f'{uid}@evaluator.invalid', '', auth_provider='evaluator')
        await db_manager.save_evaluator_session(token_fingerprint(token), uid, expires)
    except Exception as exc:
        logger.warning('Evaluator session initialization failed (%s)', type(exc).__name__)
        raise HTTPException(503, 'The evaluator session could not be saved. Please retry.') from exc
    return JSONResponse(status_code=201, content={'token':token, 'expires_at':expires, 'is_evaluator':True},
        headers={'Cache-Control':'no-store'})


class RegistrationAnswer(BaseModel):
    field: Literal['name','gender','promoter_category','phone','email']
    text: str = Field(max_length=500)
    language: Literal['en','hi','mr','ta','te','kn'] = 'en'


class RegistrationProfileAnswers(BaseModel):
    name: str = Field('', max_length=120)
    gender: str = Field('', max_length=80)
    promoter_category: str = Field('', max_length=80)
    phone: str = Field('', max_length=150)
    email: str = Field('', max_length=254)
    language: Literal['en','hi','mr','ta','te','kn'] = 'en'


@router.post('/registration/profile')
async def validate_registration_profile(profile: RegistrationProfileAnswers):
    """Validate the whole form before sending an OTP; no unauthenticated storage."""
    from app.core.profile_conversation import parse_answer, prompt, PROFILE_FIELDS, RETRY
    values, errors = {}, {}
    for field in PROFILE_FIELDS:
        text = getattr(profile, field).strip()
        parsed = parse_answer(field, text or ('skip' if field == 'email' else ''))
        if parsed:
            values.update(parsed)
        else:
            errors[field] = prompt(field, profile.language)
    missing = next(iter(errors), None)
    return JSONResponse(content={'valid':not errors, 'values':values, 'errors':errors, 'next_field':missing,
        'reply':RETRY[profile.language] + ' ' + errors[missing] if missing else ''}, headers={'Cache-Control':'no-store'})


@router.post('/registration/answer')
async def registration_answer(answer: RegistrationAnswer):
    # Unverified registration values are validated, not stored or logged. The
    # existing authenticated register endpoint persists them after phone OTP.
    from app.core.profile_conversation import parse_answer, parse_correction, prompt, PROFILE_FIELDS, RETRY
    lower = answer.text.casefold().strip(' .!।')
    if lower in ('repeat','say that again','दोहराएं','पुन्हा सांगा','மீண்டும் சொல்லுங்கள்','మళ్ళీ చెప్పండి','ಮತ್ತೆ ಹೇಳಿ'):
        return {'valid':True, 'field':answer.field, 'values':{}, 'next_field':answer.field, 'reply':prompt(answer.field, answer.language)}
    values = parse_correction(answer.text)
    if values:
        return {'valid':True,'values':values,'next_field':answer.field,'reply':prompt(answer.field,answer.language)}
    parsed = parse_answer(answer.field, answer.text)
    if not parsed:
        return {'valid':False, 'field':answer.field, 'reply':RETRY[answer.language] + ' ' + prompt(answer.field, answer.language)}
    next_index = PROFILE_FIELDS.index(answer.field) + 1
    next_field = PROFILE_FIELDS[next_index] if next_index < len(PROFILE_FIELDS) else None
    return JSONResponse(content={'valid':True, 'field':answer.field, 'values':parsed, 'next_field':next_field,
        'reply':prompt(next_field, answer.language) if next_field else ''}, headers={'Cache-Control':'no-store'})


@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def register_user_profile(
    reg_in: UserRegisterRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Creates or updates the user's PostgreSQL profile row after client-side Firebase account registration.
    Idempotent upsert keyed by current_user.uid.
    """
    email = current_user.email or reg_in.email or f"{current_user.uid}@udyam.gov.in"
    name = reg_in.name.strip() or current_user.name or email.split("@")[0]

    user_record = await db_manager.upsert_user(
        firebase_uid=current_user.uid,
        email=email,
        name=name,
        gender=reg_in.gender,
        promoter_category=reg_in.promoter_category,
        auth_provider=current_user.auth_provider,
        phone=current_user.phone_number or reg_in.phone,
        additional_business_details=reg_in.additional_business_details,
    )

    if reg_in.email_status == 'skipped' and not await db_manager.get_onboarding(current_user.uid):
        from app.models.onboarding import new_session
        from app.core.onboarding import apply_updates, advance
        state = new_session(user_record)
        apply_updates(state, {'email_status':'skipped'}, 'registration')
        await advance(state)
        await db_manager.save_onboarding(current_user.uid, state)
    projects_count = await db_manager.get_user_projects_count(current_user.uid)
    return UserProfileResponse(
        firebase_uid=user_record["firebase_uid"],
        name=user_record["name"],
        email=profile_email(user_record),
        gender=user_record.get("gender", "Unspecified"),
        promoter_category=user_record.get("promoter_category"),
        auth_provider=user_record.get("auth_provider", "email"),
        phone=user_record.get("phone"),
        additional_business_details=user_record.get("additional_business_details"),
        preferred_language=user_record.get("language", "en"),
        projects_count=projects_count,
        created_at=user_record.get("created_at", ""),
        updated_at=user_record.get("updated_at", ""),
        last_login_at=user_record.get("last_login_at"),
    )


@router.post("/session", response_model=UserProfileResponse)
async def sync_user_session(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Called after every login (manual email/password or Google OAuth).
    Verifies Firebase token, updates last_login_at, and creates a minimal user record
    on first-time Google sign-in if not already present.
    """
    existing = await db_manager.get_user(current_user.uid)
    email = current_user.email or (existing.get("email") if existing else f"{current_user.uid}@udyam.gov.in")
    name = (existing.get("name") if existing and existing.get("name") else current_user.name) or ('' if current_user.auth_provider in ('phone','evaluator','anonymous') else email.split("@")[0])

    user_record = await db_manager.upsert_user(
        firebase_uid=current_user.uid,
        email=email,
        name=name,
        gender=existing.get("gender", "Unspecified") if existing else "Unspecified",
        promoter_category=existing.get("promoter_category") if existing else None,
        auth_provider=current_user.auth_provider,
        phone=current_user.phone_number or (existing.get("phone") if existing else None),
        additional_business_details=existing.get("additional_business_details") if existing else None,
        language=existing.get("language") if existing else None,
    )

    projects_count = await db_manager.get_user_projects_count(current_user.uid)
    return UserProfileResponse(
        firebase_uid=user_record["firebase_uid"],
        name=user_record["name"],
        email=profile_email(user_record),
        gender=user_record.get("gender", "Unspecified"),
        promoter_category=user_record.get("promoter_category"),
        auth_provider=user_record.get("auth_provider", "email"),
        phone=user_record.get("phone"),
        additional_business_details=user_record.get("additional_business_details"),
        preferred_language=user_record.get("language", "en"),
        projects_count=projects_count,
        created_at=user_record.get("created_at", ""),
        updated_at=user_record.get("updated_at", ""),
        last_login_at=user_record.get("last_login_at"),
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Returns the authenticated user's profile and count of associated projects.
    """
    user_record = await db_manager.get_user(current_user.uid)
    if not user_record:
        email = current_user.email or f"{current_user.uid}@udyam.gov.in"
        user_record = await db_manager.upsert_user(
            firebase_uid=current_user.uid,
            email=email,
            name=current_user.name or email.split("@")[0],
            auth_provider=current_user.auth_provider,
        )

    projects_count = await db_manager.get_user_projects_count(current_user.uid)
    return UserProfileResponse(
        firebase_uid=user_record["firebase_uid"],
        name=user_record["name"],
        email=profile_email(user_record),
        gender=user_record.get("gender", "Unspecified"),
        promoter_category=user_record.get("promoter_category"),
        auth_provider=user_record.get("auth_provider", "email"),
        phone=user_record.get("phone"),
        additional_business_details=user_record.get("additional_business_details"),
        preferred_language=user_record.get("language", "en"),
        projects_count=projects_count,
        created_at=user_record.get("created_at", ""),
        updated_at=user_record.get("updated_at", ""),
        last_login_at=user_record.get("last_login_at"),
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    update_in: UserUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Updates editable profile fields, including the user's application language.
    """
    fields_to_update = {}
    if update_in.name is not None and update_in.name.strip():
        fields_to_update["name"] = update_in.name.strip()
    if update_in.gender is not None:
        fields_to_update["gender"] = update_in.gender
    if update_in.promoter_category is not None:
        fields_to_update["promoter_category"] = update_in.promoter_category
    if update_in.phone is not None:
        fields_to_update["phone"] = update_in.phone
    if update_in.additional_business_details is not None:
        fields_to_update["additional_business_details"] = update_in.additional_business_details
    if update_in.preferred_language is not None:
        fields_to_update["language"] = update_in.preferred_language

    updated = await db_manager.update_user(current_user.uid, fields_to_update)
    if not updated:
        raise HTTPException(status_code=404, detail="User record not found.")

    projects_count = await db_manager.get_user_projects_count(current_user.uid)
    return UserProfileResponse(
        firebase_uid=updated["firebase_uid"],
        name=updated["name"],
        email=profile_email(updated),
        gender=updated.get("gender", "Unspecified"),
        promoter_category=updated.get("promoter_category"),
        auth_provider=updated.get("auth_provider", "email"),
        phone=updated.get("phone"),
        additional_business_details=updated.get("additional_business_details"),
        preferred_language=updated.get("language", "en"),
        projects_count=projects_count,
        created_at=updated.get("created_at", ""),
        updated_at=updated.get("updated_at", ""),
        last_login_at=updated.get("last_login_at"),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Logs out the user, invalidates active sessions, and confirms termination on backend.
    """
    # Firebase ID tokens are otherwise stateless.  Record this exact bearer token
    # as revoked so it cannot continue to read protected enterprise data after
    # logout (the client receives a newly issued token on the next sign-in).
    token = authorization.strip().split(" ", 1)[1].strip() if authorization and " " in authorization else ""
    if token:
        await db_manager.revoke_session(token_fingerprint(token), current_user.uid)
    try:
        # Firebase refresh-token revocation protects real deployments.  The
        # local deterministic test-token flow is covered by the session store.
        if not current_user.is_evaluator and not token.startswith(("test-token-", "mock-token-")):
            firebase_auth.revoke_refresh_tokens(current_user.uid)
    except Exception as exc:
        logger.warning('Firebase refresh-token revocation failed (%s)', type(exc).__name__)
    logger.info('Authenticated session terminated and revoked.')
    return {
        "status": "success",
        "message": "Session terminated successfully.",
        "uid": current_user.uid,
    }


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_my_account(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Deletes the user's PostgreSQL profile row (and cascade deletes their projects)
    and removes their account from Firebase.
    """
    await db_manager.delete_user(current_user.uid)
    try:
        if not current_user.is_evaluator:
            firebase_auth.delete_user(current_user.uid)
    except Exception as e:
        logger.warning('Firebase account deletion unavailable (%s)', type(e).__name__)

    return {"status": "success", "message": f"Account '{current_user.uid}' deleted successfully."}
