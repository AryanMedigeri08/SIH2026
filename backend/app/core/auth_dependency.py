"""
auth_dependency.py — FastAPI Authentication Dependency for Firebase ID Token Verification.
"""

from __future__ import annotations
import logging
import hashlib
import os
from typing import Optional, Any
from dataclasses import dataclass, field
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

try:
    from app.core.firebase_admin_client import firebase_auth
    from app.database import db_manager
    from app.config import settings
except ImportError:
    from backend.app.core.firebase_admin_client import firebase_auth
    from backend.app.database import db_manager
    from backend.app.config import settings

logger = logging.getLogger("udyam_saathi.auth.dependency")


def token_fingerprint(token: str) -> str:
    """Return a non-reversible identifier suitable for a revoked-session store."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthenticatedUser(BaseModel):
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    email_verified: bool = False
    auth_provider: str = "email"  # 'email' | 'google.com' | 'custom'
    picture: Optional[str] = None
    phone_number: Optional[str] = None
    claims: dict[str, Any] = {}
    role: str = "entrepreneur"
    state_key: Optional[str] = None
    district_key: Optional[str] = None
    village_key: Optional[str] = None


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required (Bearer <token>).",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parts[1].strip()


def _verify_token_claims(token: str) -> dict[str, Any]:
    """
    Verifies Firebase ID token with firebase_admin.auth.
    Supports test/dev token fallback when running local test harness.
    """
    # 1. Test Harness Token Format: test-token-<uid>:<email>
    if token.startswith("test-token-") or token.startswith("mock-token-"):
        # Synthetic tokens have no signature. Never accept them in a running app.
        test_harness = bool(os.getenv("PYTEST_CURRENT_TEST")) or (
            settings.DEBUG and os.getenv("ALLOW_TEST_TOKENS") == "1"
        )
        if not test_harness:
            raise HTTPException(status_code=401, detail="Synthetic test tokens are disabled.")
        token_body = token.replace("test-token-", "").replace("mock-token-", "")
        uid = token_body.split(":")[0] if ":" in token_body else token_body
        email = token_body.split(":")[1] if ":" in token_body else f"{uid}@example.com"
        return {
            "uid": uid,
            "sub": uid,
            "user_id": uid,
            "email": email,
            "name": None,
            "email_verified": True,
            "firebase": {"sign_in_provider": "email"},
        }

    # 2. Real Firebase ID Token Verification
    try:
        try:
            from app.core.firebase_admin_client import init_firebase_admin
        except ImportError:
            from backend.app.core.firebase_admin_client import init_firebase_admin
        init_firebase_admin()

        decoded_claims = firebase_auth.verify_id_token(token, check_revoked=False)
        return decoded_claims
    except Exception as e:
        err_msg = str(e)
        logger.warning(f"Firebase token verification failed ({err_msg})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {err_msg}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> AuthenticatedUser:
    """
    FastAPI dependency that enforces a valid Firebase ID Token on incoming requests.
    Extracts Bearer token, verifies signature and claims, and returns an AuthenticatedUser.
    """
    token = _extract_bearer_token(authorization)
    if await db_manager.is_session_revoked(token_fingerprint(token)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication session has been revoked. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = _verify_token_claims(token)

    uid = claims.get("uid") or claims.get("user_id") or claims.get("sub")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user identifier (uid).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = claims.get("email")
    name = claims.get("name")
    email_verified = bool(claims.get("email_verified", False))
    firebase_meta = claims.get("firebase", {})
    sign_in_provider = firebase_meta.get("sign_in_provider", "email")
    picture = claims.get("picture")
    from app.core.role_store import get_role
    assigned = await get_role(str(uid))

    return AuthenticatedUser(
        uid=str(uid),
        email=email,
        name=name,
        email_verified=email_verified,
        auth_provider=sign_in_provider,
        picture=picture,
        phone_number=claims.get("phone_number"),
        claims=claims,
        role=assigned["role"],
        state_key=assigned.get("state_key"),
        district_key=assigned.get("district_key"),
        village_key=assigned.get("village_key"),
    )


async def get_entrepreneur(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if current_user.role != "entrepreneur":
        raise HTTPException(status_code=403, detail="Entrepreneur access required.")
    return current_user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Optional[AuthenticatedUser]:
    """
    Optional authentication dependency. Returns AuthenticatedUser if valid Bearer token
    is provided; returns None if authorization header is absent or invalid.
    """
    if not authorization or not authorization.strip():
        return None
    try:
        return await get_current_user(authorization=authorization)
    except HTTPException:
        return None
