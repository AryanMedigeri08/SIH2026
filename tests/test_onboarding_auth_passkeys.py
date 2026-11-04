import asyncio
import sqlite3
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.database import DatabaseManager
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.routers import passkeys as api


@pytest.fixture
def passkey_client(monkeypatch):
    db = DatabaseManager()
    db.sqlite = sqlite3.connect(':memory:', check_same_thread=False)
    db.sqlite.row_factory = sqlite3.Row
    db.sqlite.executescript('''CREATE TABLE users(firebase_uid TEXT PRIMARY KEY, name TEXT);
        INSERT INTO users VALUES('phone-user','Asha');
        CREATE TABLE passkey_challenges(challenge_id TEXT PRIMARY KEY,purpose TEXT,user_id TEXT,challenge TEXT,expires_at REAL);
        CREATE TABLE passkey_credentials(credential_id TEXT PRIMARY KEY,user_id TEXT,public_key TEXT,sign_count INTEGER,created_at TEXT);''')
    monkeypatch.setattr(api, 'db_manager', db)
    app = FastAPI()
    app.include_router(api.router)
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid='phone-user', phone_number='+919999999999', auth_provider='phone')
    with TestClient(app) as client:
        yield client, db
    db.sqlite.close()


def test_passkey_options_are_discoverable_and_user_verified(passkey_client):
    client, db = passkey_client
    response = client.post('/auth/passkeys/register/options')
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['credential']['user']['name'] == '+919999999999'
    assert body['credential']['authenticatorSelection']['userVerification'] == 'required'
    challenge = asyncio.run(db.consume_passkey_challenge(body['challenge_id'], 'register'))
    assert challenge['user_id'] == 'phone-user'
    assert asyncio.run(db.consume_passkey_challenge(body['challenge_id'], 'register')) is None


def test_verified_passkey_is_saved_and_challenge_cannot_be_replayed(passkey_client, monkeypatch):
    client, db = passkey_client
    options = client.post('/auth/passkeys/register/options').json()
    monkeypatch.setattr(api, 'verify_registration_response', lambda **_: SimpleNamespace(credential_id=b'key', credential_public_key=b'public', sign_count=0))
    request = {'challenge_id': options['challenge_id'], 'credential': {'id': 'a2V5'}}
    assert client.post('/auth/passkeys/register/verify', json=request).status_code == 200
    stored = asyncio.run(db.get_passkey_credential('a2V5'))
    assert stored['user_id'] == 'phone-user' and stored['public_key'] == 'cHVibGlj'
    assert client.post('/auth/passkeys/register/verify', json=request).status_code == 400


def test_authentication_checks_signature_counter_and_issues_firebase_token(passkey_client, monkeypatch):
    client, db = passkey_client
    asyncio.run(db.save_passkey_credential('a2V5', 'phone-user', 'cHVibGlj', 2))
    options = client.post('/auth/passkeys/authenticate/options').json()
    monkeypatch.setattr(api, 'verify_authentication_response', lambda **_: SimpleNamespace(credential_id=b'key', new_sign_count=3))
    monkeypatch.setattr(api, 'init_firebase_admin', lambda: None)
    monkeypatch.setattr(api.firebase_auth, 'create_custom_token', lambda uid: b'firebase-test-custom-token')
    response = client.post('/auth/passkeys/authenticate/verify', json={'challenge_id': options['challenge_id'], 'credential': {'id': 'a2V5'}})
    assert response.status_code == 200, response.text
    assert response.json()['custom_token'] == 'firebase-test-custom-token'
    assert asyncio.run(db.get_passkey_credential('a2V5'))['sign_count'] == 3


def test_authentication_rejects_invalid_signature(passkey_client, monkeypatch):
    client, db = passkey_client
    asyncio.run(db.save_passkey_credential('a2V5', 'phone-user', 'cHVibGlj', 0))
    options = client.post('/auth/passkeys/authenticate/options').json()
    def invalid(**_):
        raise ValueError('Invalid signature')
    monkeypatch.setattr(api, 'verify_authentication_response', invalid)
    response = client.post('/auth/passkeys/authenticate/verify', json={'challenge_id': options['challenge_id'], 'credential': {'id': 'a2V5'}})
    assert response.status_code == 401
    assert asyncio.run(db.get_passkey_credential('a2V5'))['sign_count'] == 0


def test_phone_registration_uses_verified_phone_and_preserves_demographics(monkeypatch):
    from app.routers import auth
    captured = {}
    class Store:
        async def upsert_user(self, **kwargs):
            captured.update(kwargs)
            return {**kwargs, 'created_at':'', 'updated_at':''}
        async def get_user_projects_count(self, uid):
            return 0
    monkeypatch.setattr(auth, 'db_manager', Store())
    app = FastAPI()
    app.include_router(auth.router)
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid='phone-user', phone_number='+919999999999', auth_provider='phone')
    with TestClient(app) as client:
        response = client.post('/auth/register', json={'name':'Asha', 'gender':'Female', 'promoter_category':'obc',
            'phone':'+918888888888', 'email':'asha@example.com'})
    assert response.status_code == 201, response.text
    assert captured['phone'] == '+919999999999'
    assert captured['gender'] == 'Female' and captured['promoter_category'] == 'obc'
    assert captured['email'] == 'asha@example.com'
