"""Map user-facing @udyam staff IDs to Firebase-compatible email identities."""

import re


def firebase_staff_email(sign_in_id: str) -> str:
    sign_in_id = sign_in_id.strip().lower()
    if sign_in_id.endswith("@udyam"):
        local = sign_in_id[:-6]
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,62}", local):
            raise ValueError("Invalid staff sign-in ID.")
        return f"{local}@udyam.example.com"
    return sign_in_id
