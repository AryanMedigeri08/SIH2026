"""Provision the two requested root staff identities in Firebase and Neon.

Dry-run is the default.  --apply creates only missing identities; it never
promotes an existing Firebase identity with an unassigned/different role.
Run from the backend directory: python -m scripts.bootstrap_staff [--apply]
"""

from __future__ import annotations

import argparse
import asyncio

from firebase_admin import auth as firebase_auth

from app.config import settings
from app.core import role_store
from app.core.firebase_admin_client import init_firebase_admin
from app.core.staff_identity import firebase_staff_email
from app.database import db_manager


STAFF = (
    ("Gov@udyam", "Government Official", "government"),
    ("SuperAdmin@udyam", "SuperAdmin", "superadmin"),
)


async def main(apply: bool) -> None:
    if not settings.DATABASE_URL:
        raise RuntimeError("Neon DATABASE_URL is required for staff bootstrap.")
    if len(settings.STAFF_INITIAL_PASSWORD) < 6:
        raise RuntimeError("Configure STAFF_INITIAL_PASSWORD (at least 6 characters) outside Git.")
    if not (settings.FIREBASE_SERVICE_ACCOUNT_JSON or settings.FIREBASE_SERVICE_ACCOUNT_PATH):
        raise RuntimeError("Firebase Admin service-account credentials are required.")
    init_firebase_admin()
    await db_manager.initialize()
    try:
        if not db_manager.pool:
            raise RuntimeError("Neon is unavailable; refusing to bootstrap into SQLite fallback.")
        for email, name, role in STAFF:
            auth_email = firebase_staff_email(email)
            try:
                existing = firebase_auth.get_user_by_email(auth_email)
            except firebase_auth.UserNotFoundError:
                existing = None
            if existing:
                assigned = await role_store.get_role(existing.uid)
                if assigned["role"] != role:
                    raise RuntimeError(f"{email} already exists without the expected role; refusing to promote it.")
                print(f"{email}: already provisioned")
                continue
            if not apply:
                print(f"{email}: missing; would create {role}")
                continue
            created = firebase_auth.create_user(
                email=auth_email, password=settings.STAFF_INITIAL_PASSWORD,
                display_name=name, email_verified=True,
            )
            try:
                await db_manager.upsert_user(created.uid, auth_email, name, auth_provider="password")
                persisted = await db_manager.get_user(created.uid)
                if not persisted or persisted["firebase_uid"] != created.uid:
                    raise RuntimeError("User row did not persist in Neon.")
                await role_store.assign_role(created.uid, role)
                print(f"{email}: created with {role} role")
            except Exception:
                firebase_auth.delete_user(created.uid)
                raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Create missing staff accounts")
    arguments = parser.parse_args()
    asyncio.run(main(arguments.apply))
