"""Cryptographic WebAuthn registration/sign-in and challenge/ownership checks."""

import base64
import hashlib
import json
import sqlite3
import asyncio
import sys
from pathlib import Path

import cbor2
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from fastapi.testclient import TestClient
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT / "backend" / "app" / "core", ROOT / "backend", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.main import app
from app.database import db_manager, DatabaseManager
from app.routers import passkeys
from app.core.auth_dependency import _verify_token_claims, get_current_user, AuthenticatedUser


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


@pytest.fixture
def client(monkeypatch):
    previous_sqlite, previous_pool = db_manager.sqlite, db_manager.pool
    previous_users = db_manager.in_memory_users.copy()
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
      CREATE TABLE users (firebase_uid TEXT PRIMARY KEY, email TEXT NOT NULL, name TEXT NOT NULL, gender TEXT, auth_provider TEXT, phone TEXT, additional_business_details TEXT, language TEXT DEFAULT 'en', created_at TEXT, updated_at TEXT, last_login_at TEXT);
      CREATE TABLE passkey_credentials (credential_id TEXT PRIMARY KEY, user_id TEXT, public_key TEXT NOT NULL, sign_count INTEGER NOT NULL DEFAULT 0, created_at TEXT);
      CREATE TABLE passkey_challenges (challenge_id TEXT PRIMARY KEY, purpose TEXT NOT NULL, user_id TEXT, challenge TEXT NOT NULL, expires_at REAL NOT NULL);
      CREATE TABLE revoked_sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, revoked_at TEXT NOT NULL);
      CREATE TABLE projects (project_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, payload TEXT, created_at TEXT, updated_at TEXT);
      CREATE TABLE user_roles (user_id TEXT PRIMARY KEY, role TEXT NOT NULL, state_key TEXT, district_key TEXT, village_key TEXT, created_at TEXT);
    """)
    db_manager.sqlite, db_manager.pool = conn, None
    monkeypatch.setattr(passkeys, "init_firebase_admin", lambda: None)
    monkeypatch.setattr(passkeys.firebase_auth, "create_custom_token", lambda uid: f"firebase-custom:{uid}".encode())
    yield TestClient(app)
    db_manager.sqlite, db_manager.pool = previous_sqlite, previous_pool
    db_manager.in_memory_users = previous_users
    conn.close()


def registration_credential(options, origin="http://localhost:3000"):
    private_key = ec.generate_private_key(ec.SECP256R1())
    pub = private_key.public_key().public_numbers()
    credential_id = bytes(range(32))
    cose_key = {1: 2, 3: -7, -1: 1, -2: pub.x.to_bytes(32, "big"), -3: pub.y.to_bytes(32, "big")}
    auth_data = hashlib.sha256(b"localhost").digest() + bytes([0x45]) + (0).to_bytes(4, "big") + bytes(16) + len(credential_id).to_bytes(2, "big") + credential_id + cbor2.dumps(cose_key)
    attestation = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
    client_data = json.dumps({"type": "webauthn.create", "challenge": options["challenge"], "origin": origin}).encode()
    return private_key, credential_id, {
        "id": b64(credential_id), "rawId": b64(credential_id), "type": "public-key",
        "response": {"clientDataJSON": b64(client_data), "attestationObject": b64(attestation)},
        "clientExtensionResults": {},
    }


def authentication_credential(options, private_key, credential_id, counter=1):
    auth_data = hashlib.sha256(b"localhost").digest() + bytes([0x05]) + counter.to_bytes(4, "big")
    client_data = json.dumps({"type": "webauthn.get", "challenge": options["challenge"], "origin": "http://localhost:3000"}).encode()
    signature = private_key.sign(auth_data + hashlib.sha256(client_data).digest(), ec.ECDSA(hashes.SHA256()))
    return {
        "id": b64(credential_id), "rawId": b64(credential_id), "type": "public-key",
        "response": {"clientDataJSON": b64(client_data), "authenticatorData": b64(auth_data), "signature": b64(signature), "userHandle": b64(b"passkey_user")},
        "clientExtensionResults": {},
    }


def test_passkey_registration_and_authentication_preserve_uid(client):
    headers = {"Authorization": "Bearer test-token-passkey_user:person@example.com"}
    assert client.post("/api/v2/auth/register", headers=headers, json={"name": "Passkey User"}).status_code == 201
    options_res = client.post("/api/v2/auth/passkeys/register/options", headers=headers)
    assert options_res.status_code == 200, options_res.text
    options = options_res.json()
    private_key, credential_id, credential = registration_credential(options["credential"])
    verified = client.post("/api/v2/auth/passkeys/register/verify", headers=headers, json={"challenge_id": options["challenge_id"], "credential": credential})
    assert verified.status_code == 200, verified.text
    assert db_manager.sqlite.execute("SELECT user_id FROM passkey_credentials WHERE credential_id=?", (b64(credential_id),)).fetchone()[0] == "passkey_user"

    login_options = client.post("/api/v2/auth/passkeys/authenticate/options").json()
    assertion = authentication_credential(login_options["credential"], private_key, credential_id)
    login = client.post("/api/v2/auth/passkeys/authenticate/verify", json={"challenge_id": login_options["challenge_id"], "credential": assertion})
    assert login.status_code == 200, login.text
    assert login.json()["custom_token"] == "firebase-custom:passkey_user"
    assert client.post("/api/v2/auth/passkeys/authenticate/verify", json={"challenge_id": login_options["challenge_id"], "credential": assertion}).status_code == 400


def test_passkey_requires_auth_and_matching_challenge(client):
    assert client.post("/api/v2/auth/passkeys/register/options").status_code == 401
    owner = {"Authorization": "Bearer test-token-owner:owner@example.com"}
    other = {"Authorization": "Bearer test-token-other:other@example.com"}
    assert client.post("/api/v2/auth/register", headers=owner, json={"name": "Owner"}).status_code == 201
    assert client.post("/api/v2/auth/register", headers=other, json={"name": "Other"}).status_code == 201
    options = client.post("/api/v2/auth/passkeys/register/options", headers=owner).json()
    _, _, credential = registration_credential(options["credential"])
    result = client.post("/api/v2/auth/passkeys/register/verify", headers=other, json={"challenge_id": options["challenge_id"], "credential": credential})
    assert result.status_code == 403
    assert client.post("/api/v2/auth/passkeys/register/verify", headers=owner, json={"challenge_id": options["challenge_id"], "credential": credential}).status_code == 400


def test_passkey_rejects_wrong_origin(client):
    owner = {"Authorization": "Bearer test-token-owner:owner@example.com"}
    client.post("/api/v2/auth/register", headers=owner, json={"name": "Owner"})
    options = client.post("/api/v2/auth/passkeys/register/options", headers=owner).json()
    _, _, credential = registration_credential(options["credential"], origin="https://attacker.example")
    result = client.post("/api/v2/auth/passkeys/register/verify", headers=owner, json={"challenge_id": options["challenge_id"], "credential": credential})
    assert result.status_code == 400
    assert db_manager.sqlite.execute("SELECT count(*) FROM passkey_credentials").fetchone()[0] == 0


def test_synthetic_tokens_disabled_outside_tests(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("ALLOW_TEST_TOKENS", raising=False)
    with pytest.raises(HTTPException) as error:
        _verify_token_claims("test-token-attacker:attacker@example.com")
    assert error.value.status_code == 401


def test_phone_profile_requires_verified_number(client):
    async def phone_user():
        return AuthenticatedUser(uid="phone_uid", auth_provider="phone", phone_number="+919876543210")
    app.dependency_overrides[get_current_user] = phone_user
    try:
        mismatch = client.post("/api/v2/auth/register", json={"name": "Phone User", "phone": "+919999999999"})
        assert mismatch.status_code == 400
        match = client.post("/api/v2/auth/register", json={"name": "Phone User", "phone": "+919876543210"})
        assert match.status_code == 201, match.text
        assert match.json()["phone"] == "+919876543210"
    finally:
        app.dependency_overrides.clear()


def test_linked_phone_session_keeps_existing_account_uid_and_email(client):
    headers = {"Authorization": "Bearer test-token-existing_uid:owner@example.com"}
    assert client.post("/api/v2/auth/register", headers=headers, json={"name": "Existing Owner"}).status_code == 201

    async def linked_user():
        return AuthenticatedUser(uid="existing_uid", auth_provider="phone", phone_number="+919876543210")
    app.dependency_overrides[get_current_user] = linked_user
    try:
        result = client.post("/api/v2/auth/session")
        assert result.status_code == 200, result.text
        profile = result.json()
        assert profile["firebase_uid"] == "existing_uid"
        assert profile["email"] == "owner@example.com"
        assert profile["phone"] == "+919876543210"
    finally:
        app.dependency_overrides.clear()


def test_passkey_credential_persists_after_database_reopen(tmp_path):
    path = tmp_path / "passkeys.sqlite3"
    first = DatabaseManager()
    first.sqlite = sqlite3.connect(path, check_same_thread=False)
    first.sqlite.row_factory = sqlite3.Row
    first.sqlite.executescript("CREATE TABLE passkey_credentials (credential_id TEXT PRIMARY KEY, user_id TEXT, public_key TEXT, sign_count INTEGER, created_at TEXT);")
    asyncio.run(first.save_passkey_credential("cred-1", "same-firebase-uid", "public-key", 0))
    first.sqlite.close()
    second = DatabaseManager()
    second.sqlite = sqlite3.connect(path, check_same_thread=False)
    second.sqlite.row_factory = sqlite3.Row
    saved = asyncio.run(second.get_passkey_credential("cred-1"))
    assert saved["user_id"] == "same-firebase-uid"
    assert saved["public_key"] == "public-key"
    second.sqlite.close()
