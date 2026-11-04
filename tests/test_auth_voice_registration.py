"""Authentication boundaries and deterministic multilingual profile collection."""
import asyncio
import json
import sys
import time
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_mira_onboarding import client as stored_client
from app.config import settings
from app.core.auth_dependency import token_fingerprint
from app.core.profile_conversation import parse_answer, PROMPTS, PROFILE_FIELDS
from app.routers import auth


@pytest.fixture
def client(stored_client, monkeypatch):
    http, db = stored_client
    monkeypatch.setattr(settings, 'ALLOW_TEST_AUTH', False)
    auth._evaluator_requests.clear()
    return http, db


def evaluator(http):
    issued = http.post('/api/v2/auth/evaluator')
    assert issued.status_code == 201, issued.text
    assert issued.headers['cache-control'] == 'no-store'
    token = issued.json()['token']
    http.headers['Authorization'] = 'Bearer ' + token
    profile = http.post('/api/v2/auth/session')
    assert profile.status_code == 200, profile.text
    assert profile.json()['email'] is None
    return token, profile.json()['firebase_uid']


def test_evaluator_is_persisted_hashed_expiring_and_isolated(client):
    http, db = client
    token, uid = evaluator(http)
    row = dict(db.sqlite.execute('SELECT * FROM evaluator_sessions').fetchone())
    assert row['token_hash'] == token_fingerprint(token) and token not in str(row)
    assert 7.9 * 3600 < row['expires_at'] - time.time() <= 8 * 3600
    http.patch('/api/v2/auth/me', json={'name':'First evaluator'})
    second, other = evaluator(http)
    assert uid != other and token != second
    assert http.get('/api/v2/auth/me').json()['name'] == ''
    http.headers['Authorization'] = 'Bearer ' + token
    assert http.get('/api/v2/auth/me').json()['name'] == 'First evaluator'
    assert asyncio.run(db.get_onboarding(other)) is None


def test_evaluator_forgery_expiry_and_logout_are_rejected(client, monkeypatch):
    http, db = client
    token, uid = evaluator(http)
    # Evaluator logout never calls Firebase with a non-Firebase identity.
    monkeypatch.setattr(auth.firebase_auth, 'revoke_refresh_tokens', lambda *_: pytest.fail('Firebase must not receive evaluator identities'))
    assert http.post('/api/v2/auth/logout').status_code == 200
    assert http.get('/api/v2/auth/me').status_code == 401
    fresh, _ = evaluator(http)
    db.sqlite.execute('UPDATE evaluator_sessions SET expires_at=? WHERE token_hash=?', (time.time()-1, token_fingerprint(fresh)))
    db.sqlite.commit()
    assert http.get('/api/v2/auth/me').status_code == 401
    for forged in ['ev1_'+'x'*43, 'ev1_bad', 'test-token-'+uid+':fake@example.com']:
        http.headers['Authorization'] = 'Bearer '+forged
        assert http.get('/api/v2/auth/me').status_code == 401


def test_evaluator_rate_limit_and_unavailable_storage_fail_closed(client, monkeypatch):
    http, db = client
    for _ in range(10):
        assert http.post('/api/v2/auth/evaluator').status_code == 201
    assert http.post('/api/v2/auth/evaluator').status_code == 429
    auth._evaluator_requests.clear()
    async def unavailable(*_):
        raise RuntimeError('storage unavailable')
    monkeypatch.setattr(db, 'save_evaluator_session', unavailable)
    assert http.post('/api/v2/auth/evaluator').status_code == 503


def test_registration_sequence_validation_repeat_and_correction(client):
    http, _ = client
    fields = list(PROFILE_FIELDS)
    for index, text in enumerate(['My name is Asha Patil', 'female', 'other backward class', 'nine eight seven six five four three two one zero', 'skip']):
        response = http.post('/api/v2/auth/registration/answer', json={'field':fields[index], 'text':text, 'language':'hi'})
        body = response.json()
        assert body['valid'] is True
        assert body['next_field'] == (fields[index+1] if index < 4 else None)
        if index < 4:
            assert body['reply'] == PROMPTS['hi'][index+1]
    invalid = http.post('/api/v2/auth/registration/answer', json={'field':'phone', 'text':'123'}).json()
    assert invalid['valid'] is False and invalid['field'] == 'phone'
    repeated = http.post('/api/v2/auth/registration/answer', json={'field':'phone', 'text':'repeat'}).json()
    assert repeated['next_field'] == 'phone' and repeated['values'] == {}
    corrected = http.post('/api/v2/auth/registration/answer', json={'field':'phone','text':'change my name to Asha Rao'}).json()
    assert corrected['values'] == {'name':'Asha Rao'} and corrected['next_field'] == 'phone'


@pytest.mark.parametrize('language,category,number', [
    ('hi','ओबीसी','नौ आठ सात छह पांच चार तीन दो एक शून्य'),
    ('mr','एससी','नऊ आठ सात सहा पाच चार तीन दोन एक शून्य'),
    ('ta','ஓபிசி','ஒன்பது எட்டு ஏழு ஆறு ஐந்து நான்கு மூன்று இரண்டு ஒன்று பூஜ்யம்'),
    ('te','ఎస్సీ','తొమ్మిది ఎనిమిది ఏడు ఆరు ఐదు నాలుగు మూడు రెండు ఒకటి సున్నా'),
    ('kn','ಎಸ್ಟಿ','ಒಂಬತ್ತು ಎಂಟು ಏಳು ಆರು ಐದು ನಾಲ್ಕು ಮೂರು ಎರಡು ಒಂದು ಸೊನ್ನೆ'),
])
def test_native_answers_and_prompts(language, category, number):
    assert len(PROMPTS[language]) == 5 and all(PROMPTS[language])
    assert parse_answer('promoter_category',category)
    assert parse_answer('phone',number) == {'phone':'+919876543210'}
    assert parse_answer('promoter_category','Patil') is None


def test_authenticated_profile_is_sequential_persistent_and_redacted(client):
    http, db = client
    _, uid = evaluator(http)
    result = http.get('/api/v2/onboarding/session?experience=adaptive').json()
    for field, text in [('name','Asha Patil'), ('gender','female'), ('promoter_category','obc'), ('phone','9876543210'), ('email','asha at example dot com')]:
        assert result['state']['next']['field'] == field
        result = http.post('/api/v2/onboarding/turn', json={'revision':result['state']['revision'], 'request_id':str(uuid.uuid4()), 'text':text, 'source':'voice'}).json()
        assert result['accepted'] is True
    assert result['state']['next']['field'] == 'location'
    saved = asyncio.run(db.get_user(uid))
    assert saved['name'] == 'Asha Patil' and saved['phone'] == '+919876543210'
    assert saved['email'] == 'asha@example.com' and saved['promoter_category'] == 'obc'
    visible = json.dumps(result)
    assert 'Asha Patil' not in visible and '9876543210' not in visible and 'asha@example.com' not in visible
    assert result['state']['fields']['name']['redacted'] is True


def test_skipped_registration_email_is_not_asked_again(stored_client):
    http, db = stored_client
    from app.core.auth_dependency import get_current_user, AuthenticatedUser
    http.app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid='mira-test', phone_number='+919876543210', auth_provider='phone')
    asyncio.run(db.update_user('mira-test', {'email':'mira-test@udyam.gov.in'}))
    response = http.post('/api/v2/auth/register', json={'name':'Asha','gender':'Female','promoter_category':'obc','phone':'+919876543210','email_status':'skipped'})
    assert response.status_code == 201, response.text
    state = http.get('/api/v2/onboarding/session?experience=adaptive').json()['state']
    assert state['next']['field'] == 'location'
    assert 'email' not in state['fields']
    assert asyncio.run(db.get_onboarding('mira-test'))['fields']['email_status']['value'] == 'skipped'


def test_profile_language_does_not_depend_on_translation_provider(client, monkeypatch):
    http, _ = client
    evaluator(http)
    for language in PROMPTS:
        response = http.get(f'/api/v2/onboarding/session?experience=adaptive&language={language}').json()
        assert response['reply'] == PROMPTS[language][0]


def test_ambiguous_demographics_do_not_advance():
    assert parse_answer('gender', 'male or female') is None
    assert parse_answer('promoter_category', 'SC or ST') is None


def test_native_correction_preserves_later_answers_and_requires_confirmation(client):
    http, db = client
    _, uid = evaluator(http)
    http.patch('/api/v2/auth/me', json={'name':'Asha','gender':'Female','promoter_category':'obc','phone':'+919876543210'})
    result = http.get('/api/v2/onboarding/session?experience=adaptive').json()
    assert result['state']['next']['field'] == 'email'
    result = http.post('/api/v2/onboarding/turn', json={'revision':result['state']['revision'],'request_id':str(uuid.uuid4()),'text':'नाम बदलें आशा राव'}).json()
    assert result['state']['next']['field'] == 'pending_changes'
    assert 'आशा राव' not in json.dumps(result, ensure_ascii=False)
    result = http.post('/api/v2/onboarding/turn', json={'revision':result['state']['revision'],'request_id':str(uuid.uuid4()),'action':'confirm_change'}).json()
    assert result['state']['next']['field'] == 'email'
    saved = asyncio.run(db.get_user(uid))
    assert saved['name'] == 'आशा राव' and saved['phone'] == '+919876543210'
