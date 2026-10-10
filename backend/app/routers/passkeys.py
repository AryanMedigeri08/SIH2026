"""WebAuthn passkeys linked to an existing, Firebase-verified account.

Challenges and public credentials live in the same persistent database as users.
No biometric data leaves the authenticator; Firebase remains the session issuer.
"""

from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url, options_to_json
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.config import settings
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.firebase_admin_client import firebase_auth, init_firebase_admin
from app.database import db_manager

router = APIRouter(prefix="/auth/passkeys", tags=["Passkeys"])
logger = logging.getLogger("udyam_saathi.passkeys")
CHALLENGE_SECONDS = 300


class PasskeyResponse(BaseModel):
    challenge_id: str
    credential: dict


def _active_challenge(row: dict | None) -> bytes:
    if not row or row["expires_at"] < time.time():
        raise HTTPException(status_code=400, detail="Passkey challenge expired or already used. Please retry.")
    return base64url_to_bytes(row["challenge"])


@router.post("/register/options", response_model=PasskeyResponse)
async def passkey_registration_options(user: AuthenticatedUser = Depends(get_current_user)):
    if user.auth_provider == "anonymous":
        raise HTTPException(status_code=403, detail="Evaluator sessions cannot create passkeys.")
    profile = await db_manager.get_user(user.uid)
    if not profile:
        raise HTTPException(status_code=409, detail="Complete account registration before adding a passkey.")
    options = generate_registration_options(
        rp_id=settings.PASSKEY_RP_ID,
        rp_name="Udyam Saathi",
        user_id=user.uid.encode("utf-8"),
        user_name=user.phone_number or user.email or user.uid,
        user_display_name=profile.get("name") or "Entrepreneur",
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )
    challenge_id = str(uuid.uuid4())
    await db_manager.save_passkey_challenge(
        challenge_id, "register", user.uid, bytes_to_base64url(options.challenge), time.time() + CHALLENGE_SECONDS
    )
    return PasskeyResponse(challenge_id=challenge_id, credential=json.loads(options_to_json(options)))


class VerifyPasskeyRequest(BaseModel):
    challenge_id: str
    credential: dict


@router.post("/register/verify")
async def passkey_registration_verify(
    request: VerifyPasskeyRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    row = await db_manager.consume_passkey_challenge(request.challenge_id, "register")
    challenge = _active_challenge(row)
    if row["user_id"] != user.uid:
        raise HTTPException(status_code=403, detail="This challenge belongs to another account.")
    try:
        verified = verify_registration_response(
            credential=request.credential,
            expected_challenge=challenge,
            expected_rp_id=settings.PASSKEY_RP_ID,
            expected_origin=settings.PASSKEY_ORIGIN,
            require_user_verification=True,
        )
        await db_manager.save_passkey_credential(
            bytes_to_base64url(verified.credential_id),
            user.uid,
            bytes_to_base64url(verified.credential_public_key),
            verified.sign_count,
        )
    except Exception as exc:
        logger.warning("Passkey registration rejected: %s", type(exc).__name__)
        raise HTTPException(status_code=400, detail="Passkey registration could not be verified.") from exc
    return {"status": "registered"}


@router.post("/authenticate/options", response_model=PasskeyResponse)
async def passkey_authentication_options():
    # Discoverable credentials let the device/account picker identify the user;
    # no phone/email enumeration endpoint is needed.
    options = generate_authentication_options(
        rp_id=settings.PASSKEY_RP_ID,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    challenge_id = str(uuid.uuid4())
    await db_manager.save_passkey_challenge(
        challenge_id, "authenticate", None, bytes_to_base64url(options.challenge), time.time() + CHALLENGE_SECONDS
    )
    return PasskeyResponse(challenge_id=challenge_id, credential=json.loads(options_to_json(options)))


@router.post("/authenticate/verify")
async def passkey_authentication_verify(request: VerifyPasskeyRequest):
    row = await db_manager.consume_passkey_challenge(request.challenge_id, "authenticate")
    challenge = _active_challenge(row)
    credential_id = request.credential.get("id")
    if not isinstance(credential_id, str):
        raise HTTPException(status_code=400, detail="Passkey credential ID is missing.")
    saved = await db_manager.get_passkey_credential(credential_id)
    if not saved:
        raise HTTPException(status_code=401, detail="Passkey is not registered.")
    try:
        verified = verify_authentication_response(
            credential=request.credential,
            expected_challenge=challenge,
            expected_rp_id=settings.PASSKEY_RP_ID,
            expected_origin=settings.PASSKEY_ORIGIN,
            credential_public_key=base64url_to_bytes(saved["public_key"]),
            credential_current_sign_count=saved["sign_count"],
            require_user_verification=True,
        )
        if bytes_to_base64url(verified.credential_id) != credential_id:
            raise ValueError("Credential ID mismatch")
    except Exception as exc:
        logger.warning("Passkey authentication rejected: %s", type(exc).__name__)
        raise HTTPException(status_code=401, detail="Passkey authentication failed.") from exc
    if not await db_manager.update_passkey_counter(credential_id, saved["sign_count"], verified.new_sign_count):
        raise HTTPException(status_code=401, detail="Passkey was used concurrently. Please retry.")
    if not await db_manager.get_user(saved["user_id"]):
        raise HTTPException(status_code=401, detail="Account no longer exists.")
    try:
        init_firebase_admin()
        custom_token = firebase_auth.create_custom_token(saved["user_id"])
    except Exception as exc:
        logger.exception("Firebase custom-token issuance failed")
        raise HTTPException(status_code=503, detail="Passkey verified, but sign-in service is unavailable.") from exc
    return {"custom_token": custom_token.decode("utf-8") if isinstance(custom_token, bytes) else custom_token}
