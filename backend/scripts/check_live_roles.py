"""Live Firebase + Neon smoke check for staff sign-in, role gates, and logout.

Run from backend: python -m scripts.check_live_roles
Uses local ignored environment credentials; never prints passwords or tokens.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib import request

from dotenv import dotenv_values
from fastapi.testclient import TestClient

from app.config import settings
from app.core.staff_identity import firebase_staff_email
from app.main import app


def firebase_id_token(alias: str) -> str:
    frontend_env = Path(__file__).resolve().parents[2] / "frontend" / ".env"
    api_key = dotenv_values(frontend_env).get("VITE_FIREBASE_API_KEY")
    if not api_key or not settings.STAFF_INITIAL_PASSWORD:
        raise RuntimeError("Local Firebase Web API key or staff password is not configured.")
    payload = json.dumps({
        "email": firebase_staff_email(alias), "password": settings.STAFF_INITIAL_PASSWORD,
        "returnSecureToken": True,
    }).encode()
    endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    response = request.urlopen(request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"}), timeout=15)
    return json.load(response)["idToken"]


def main() -> None:
    for alias, role, allowed, denied in (
        ("Gov@udyam", "government", "/api/v2/roles/government/summary", "/api/v2/roles/admin/users"),
        ("SuperAdmin@udyam", "superadmin", "/api/v2/roles/admin/users", "/api/v2/roles/applications"),
    ):
        token = firebase_id_token(alias)
        headers = {"Authorization": f"Bearer {token}"}
        with TestClient(app) as client:
            session = client.post("/api/v2/auth/session", headers=headers)
            assert session.status_code == 200, f"{alias} session: HTTP {session.status_code} {session.text[:200]}"
            assert session.json()["role"] == role
            assert client.get(allowed, headers=headers).status_code == 200
            assert client.get(denied, headers=headers).status_code == 403
            assert client.get("/api/v2/projects", headers=headers).status_code == 403
            assert client.get("/api/v2/roles/me").status_code == 401
            assert client.post("/api/v2/auth/logout", headers=headers).status_code == 200
            assert client.get("/api/v2/roles/me", headers=headers).status_code == 401
            print(f"{alias}: Firebase sign-in, Neon role, API gates, and logout passed")


if __name__ == "__main__":
    main()
