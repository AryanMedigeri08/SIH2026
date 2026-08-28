"""
auth.py — REST API Router for User Authentication, Firebase Session Sync, and Profile Management.
"""

from __future__ import annotations
import logging
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse

from app.database import db_manager
from app.models.schemas import UserRegisterRequest, UserUpdateRequest, UserProfileResponse
from app.core.auth_dependency import get_current_user, AuthenticatedUser, token_fingerprint
from app.core.firebase_admin_client import firebase_auth

logger = logging.getLogger("udyam_saathi.routers.auth")

router = APIRouter(prefix="/auth", tags=["User Authentication & Profile"])


@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def register_user_profile(
    reg_in: UserRegisterRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Creates or updates the user's PostgreSQL profile row after client-side Firebase account registration.
    Idempotent upsert keyed by current_user.uid.
    """
    email = current_user.email or f"{current_user.uid}@udyam.gov.in"
    name = reg_in.name.strip() or current_user.name or email.split("@")[0]

    user_record = await db_manager.upsert_user(
        firebase_uid=current_user.uid,
        email=email,
        name=name,
        gender=reg_in.gender or "Unspecified",
        auth_provider=current_user.auth_provider,
        phone=reg_in.phone,
        additional_business_details=reg_in.additional_business_details,
    )

    projects_count = await db_manager.get_user_projects_count(current_user.uid)
    return UserProfileResponse(
        firebase_uid=user_record["firebase_uid"],
        name=user_record["name"],
        email=user_record["email"],
        gender=user_record.get("gender", "Unspecified"),
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
    name = (existing.get("name") if existing and existing.get("name") else current_user.name) or email.split("@")[0]

    user_record = await db_manager.upsert_user(
        firebase_uid=current_user.uid,
        email=email,
        name=name,
        gender=existing.get("gender", "Unspecified") if existing else "Unspecified",
        auth_provider=current_user.auth_provider,
        phone=existing.get("phone") if existing else None,
        additional_business_details=existing.get("additional_business_details") if existing else None,
        language=existing.get("language") if existing else None,
    )

    projects_count = await db_manager.get_user_projects_count(current_user.uid)
    return UserProfileResponse(
        firebase_uid=user_record["firebase_uid"],
        name=user_record["name"],
        email=user_record["email"],
        gender=user_record.get("gender", "Unspecified"),
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
        email=user_record["email"],
        gender=user_record.get("gender", "Unspecified"),
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
        email=updated["email"],
        gender=updated.get("gender", "Unspecified"),
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
        if not token.startswith(("test-token-", "mock-token-")):
            firebase_auth.revoke_refresh_tokens(current_user.uid)
    except Exception as exc:
        logger.warning("Firebase refresh-token revocation failed for %s: %s", current_user.uid, exc)
    logger.info(f"User '{current_user.uid}' ({current_user.email}) logged out and session revoked.")
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
        firebase_auth.delete_user(current_user.uid)
    except Exception as e:
        logger.warning(f"Could not delete Firebase user ({e}); local profile removed.")

    return {"status": "success", "message": f"Account '{current_user.uid}' deleted successfully."}
