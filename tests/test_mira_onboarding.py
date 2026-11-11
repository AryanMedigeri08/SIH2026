import asyncio
import sqlite3
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from tests.test_planning_financial_baseline import frozen_evidence
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.onboarding_questions import next_question, money
from app.core.onboarding_store import OnboardingStore
from app.core import onboarding_location as locations
from app.routers import onboarding as route
from app.models.onboarding import OnboardingDraft, OnboardingLocation

LOCATION = dict(state_name='West Bengal', district_name='Bankura', block_name='Test block', village_name='Test village', confirmed=True)


@pytest.fixture
def client(monkeypatch):
    store = OnboardingStore(SimpleNamespace(pool=None, sqlite=None))
    monkeypatch.setattr(route, 'onboarding_store', store)
    monkeypatch.setattr(route, 'validate_location', AsyncMock(side_effect=lambda value: value.model_dump()))
    app = FastAPI(); app.include_router(route.router)
    owner = {'uid': 'alice'}
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid=owner['uid'])
    with TestClient(app) as browser:
        yield browser, owner, store


@pytest.mark.parametrize('path,expected', [
    ('existing', ['idea','business_id','idea_confirmed','odop_choice','own_cash','cash_confirmed','premise_type','monthly_rent','equipment_quote','project_cost','annual_sales','resources','enterprise_name','review_confirmed']),
    ('budget_only', ['own_cash','cash_confirmed','skills','premise_type','monthly_rent','resources','preferences','review_confirmed']),
    ('idea_only', ['idea','business_id','idea_confirmed','odop_choice','premise_type','monthly_rent','equipment_quote','own_cash','resources','enterprise_name','review_confirmed']),
])
def test_complete_three_conversations_without_provider_or_finance_calls(client, path, expected):
    browser, _, _ = client
    response = browser.put('/onboarding/session', json={'journey': path, 'language': 'hi', 'location': LOCATION})
    assert response.status_code == 200
    values = {'idea': 'Make curd for local shops', 'business_id': 'dairy_aggregation', 'idea_confirmed': True,
        'odop_choice': 'original', 'own_cash': 'unknown' if path == 'idea_only' else 'fifty thousand',
        'cash_confirmed': True, 'skills': 'none', 'premise_type': 'rented', 'monthly_rent': '0',
        'equipment_quote': 'unknown', 'project_cost': 'unknown', 'annual_sales': 'unknown',
        'resources': 'none', 'preferences': 'none', 'enterprise_name': 'Test dairy', 'review_confirmed': True}
    for field in expected:
        assert browser.get('/onboarding/question').json()['question'] == field
        response = browser.post('/onboarding/answer', json={'field': field, 'value': values[field]})
        assert response.status_code == 200, response.text
    state = response.json()
    assert state['question'] == 'ready'
    assert state['draft']['language'] == 'hi'
    assert state['draft']['answers']['own_cash'] == (None if path == 'idea_only' else 50000)
    assert state['draft']['answers']['monthly_rent'] == 0


def test_skip_and_stale_question_cannot_advance(client):
    browser, _, _ = client
    assert browser.post('/onboarding/answer', json={'field': 'review_confirmed', 'value': True}).status_code == 409
    browser.put('/onboarding/session', json={'journey': 'budget_only', 'location': LOCATION})
    assert browser.post('/onboarding/answer', json={'field': 'own_cash', 'value': 'unknown'}).status_code == 422
    assert browser.get('/onboarding/question').json()['question'] == 'own_cash'
    assert browser.post('/onboarding/answer', json={'field': 'own_cash', 'value': 0}).status_code == 200
    assert browser.post('/onboarding/answer', json={'field': 'cash_confirmed', 'value': False}).status_code == 422


def test_owner_isolation_and_sensitive_fields_rejected(client):
    browser, owner, _ = client
    assert browser.put('/onboarding/session', json={'answers': {'otp': '123456'}}).status_code == 422
    assert browser.put('/onboarding/session', json={'answers': {'phone': '9999999999'}}).status_code == 422
    browser.put('/onboarding/session', json={'journey': 'idea_only', 'language': 'mr'})
    owner['uid'] = 'bob'
    assert browser.get('/onboarding/session').json()['journey'] is None
    owner['uid'] = 'alice'
    assert browser.get('/onboarding/session').json()['language'] == 'mr'


def test_hybrid_adoption_is_explicit_and_preserves_existing_funding(client):
    browser, _, _ = client
    answers = {'idea': 'Make curd for local shops', 'business_id': 'dairy_aggregation', 'idea_confirmed': True, 'own_cash': 0}
    browser.put('/onboarding/session', json={'journey': 'idea_only', 'location': LOCATION, 'answers': answers})
    assert browser.post('/onboarding/answer', json={'field': 'odop_choice', 'value': 'hybrid'}).status_code == 422
    result = browser.post('/onboarding/answer', json={'field': 'odop_choice', 'value': 'hybrid',
        'hybrid_name': 'Curd in clay pots', 'hybrid_description': 'Make curd in food-safe artisan pots.'}).json()
    a = result['draft']['answers']
    assert a['original_idea'] == answers['idea']
    assert a['idea'] == 'Make curd in food-safe artisan pots.'
    assert a['own_cash'] == 0
    assert a['business_id'] == 'dairy_aggregation'


@pytest.mark.parametrize('value,expected', [('1.5 lakh',150000),('fifty thousand',50000),('₹५०,०००',50000),('०',0),('2 lakh fifty thousand',250000),('50000',50000)])
def test_indian_money_readback_values(value, expected):
    assert money(value) == expected


@pytest.mark.parametrize('value', ['-1','nan','infinity','10 bananas',100000001,True])
def test_money_does_not_guess_ambiguous_or_invalid_amounts(value):
    with pytest.raises(HTTPException): money(value)


def test_unknown_cash_and_zero_have_different_next_questions():
    draft = {'journey': 'idea_only', 'location': LOCATION, 'answers': dict(idea='A repair shop', business_id='custom', sector='repair', business_category='service', idea_confirmed=True, odop_choice='original', premise_type='owned', equipment_quote=None, own_cash=None)}
    assert next_question(draft) == 'resources'
    draft['answers']['own_cash'] = 0
    assert next_question(draft) == 'cash_confirmed'


def test_sqlite_drafts_survive_new_worker_and_are_independent():
    connection = sqlite3.connect(':memory:')
    database = SimpleNamespace(pool=None, sqlite=connection)
    one, two = OnboardingStore(database), OnboardingStore(database)
    asyncio.run(one.save('alice', {'language': 'ta', 'answers': {'own_cash': None}}))
    assert asyncio.run(two.get('alice'))['language'] == 'ta'
    assert asyncio.run(two.get('bob')) is None
    connection.close()


def test_gps_does_not_choose_first_or_ambiguous_location(monkeypatch):
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'address': {'state': 'West Bengal', 'district': 'Not in registry'}}
    class Client:
        def __init__(self, **kw): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, *args, **kw): return Response()
    monkeypatch.setattr(locations.httpx, 'AsyncClient', Client)
    monkeypatch.setattr(locations, 'location_options', AsyncMock(side_effect=[['West Bengal'],['Bankura','Purulia']]))
    result = asyncio.run(locations.resolve_gps(23,87))
    assert result['state_name'] == 'West Bengal'
    assert 'district_name' not in result
    assert result['confirmed'] is False


def test_mismatched_manual_hierarchy_rejected(monkeypatch):
    monkeypatch.setattr(locations, 'location_options', AsyncMock(side_effect=[['West Bengal'],['Bankura']]))
    with pytest.raises(HTTPException): asyncio.run(locations.validate_location(OnboardingLocation(**{**LOCATION, 'district_name': 'Other'})))


def test_preview_replay_is_owner_scoped_and_omits_private_appraisals(monkeypatch):
    import time
    from app.routers import planning
    from app.core.enterprise_planning import Draft
    from app.models.planning import PlanningRequest
    req = PlanningRequest(path='budget_only', own_cash=50000, promoter_name='Test', **{k:v for k,v in LOCATION.items() if k != 'confirmed'})
    draft = Draft('alice', time.time()+100, req, {'proposals': [], '_evaluations': {'private': 'hidden'}})
    store = SimpleNamespace(get=AsyncMock(return_value=draft))
    monkeypatch.setattr(planning, 'draft_store', store)
    result = asyncio.run(planning.saved_preview('saved-id', AuthenticatedUser(uid='alice')))
    store.get.assert_awaited_once_with('alice','saved-id')
    assert result['draft_id'] == 'saved-id'
    assert '_evaluations' not in result


def test_intent_provider_failure_never_blocks_manual_business_selection(monkeypatch):
    from app.core import onboarding_intent as intent
    monkeypatch.setattr(intent, '_get_groq_client', lambda: None)
    result = asyncio.run(intent.IntentService().interpret('alice', 'मुझे दही बनाकर बेचना है', 'hi'))
    assert result['business_id'] == 'custom'
    assert result['clarification'] == ''


def test_mira_tts_enforces_bhashini_female_voice(monkeypatch):
    from app.routers import chat
    synthesis = AsyncMock(return_value=b'RIFFsynthetic-wave')
    fallback = AsyncMock(side_effect=AssertionError('Mira must use Bhashini'))
    monkeypatch.setattr(chat.bhashini_client, 'synthesize', synthesis)
    monkeypatch.setattr(chat.audio_chat_service, 'text_to_speech_v2', fallback)
    result = asyncio.run(chat.generate_speech(chat.TtsRequest(text='नमस्ते', language='hi', provider='bhashini')))
    synthesis.assert_awaited_once_with('नमस्ते', 'hi', gender='female')
    assert result['tier_used'] == 'bhashini'
    assert result['audio_base64'].startswith('data:audio/wav;base64,')
    fallback.assert_not_called()


def test_bhashini_failure_does_not_substitute_another_voice(monkeypatch):
    from app.routers import chat
    monkeypatch.setattr(chat.bhashini_client, 'synthesize', AsyncMock(side_effect=RuntimeError('synthetic outage')))
    fallback = AsyncMock(side_effect=AssertionError('No other voice for Mira'))
    monkeypatch.setattr(chat.audio_chat_service, 'text_to_speech_v2', fallback)
    with pytest.raises(HTTPException) as error:
        asyncio.run(chat.generate_speech(chat.TtsRequest(text='Hello', language='en', provider='bhashini')))
    assert error.value.status_code == 503
    fallback.assert_not_called()


def test_legacy_tts_keeps_existing_auto_behavior(monkeypatch):
    from app.routers import chat
    fallback = AsyncMock(return_value={'audio_base64': 'synthetic'})
    monkeypatch.setattr(chat.audio_chat_service, 'text_to_speech_v2', fallback)
    assert asyncio.run(chat.generate_speech(chat.TtsRequest(text='Hello')))['audio_base64'] == 'synthetic'
    fallback.assert_awaited_once_with(text='Hello', language='en')


def test_profile_category_language_and_gender_persist_after_memory_reset():
    from app.database import DatabaseManager
    connection = sqlite3.connect(':memory:'); connection.row_factory = sqlite3.Row
    connection.execute('CREATE TABLE users (firebase_uid TEXT PRIMARY KEY,email TEXT,name TEXT,gender TEXT,auth_provider TEXT,phone TEXT,additional_business_details TEXT,language TEXT,promoter_category TEXT,created_at TEXT,updated_at TEXT,last_login_at TEXT)')
    one = DatabaseManager(); one.sqlite = connection
    asyncio.run(one.upsert_user('alice', 'synthetic@example.test', 'Test promoter', gender='Female', promoter_category='st', language='kn'))
    two = DatabaseManager(); two.sqlite = connection
    asyncio.run(two.upsert_user('alice', 'synthetic@example.test', 'Test promoter', gender='Female'))
    restored = asyncio.run(two.get_user('alice'))
    assert (restored['gender'], restored['promoter_category'], restored['language']) == ('Female','st','kn')
    asyncio.run(two.update_user('alice', {'gender': 'Other', 'promoter_category': 'obc', 'language': 'ta'}))
    two.in_memory_users.clear()
    restored = asyncio.run(two.get_user('alice'))
    assert (restored['gender'], restored['promoter_category'], restored['language']) == ('Other','obc','ta')
    connection.close()


def test_phone_profile_uses_verified_claim_not_typed_number(monkeypatch):
    from app.routers import auth
    from app.models.schemas import UserRegisterRequest
    record = {'firebase_uid': 'alice', 'name': 'Test promoter', 'email': 'synthetic@example.test', 'created_at': '', 'updated_at': ''}
    save = AsyncMock(return_value=record)
    monkeypatch.setattr(auth, 'db_manager', SimpleNamespace(upsert_user=save, get_user_projects_count=AsyncMock(return_value=0)))
    user = AuthenticatedUser(uid='alice', auth_provider='phone', claims={'phone_number': '+919876543210'})
    asyncio.run(auth.register_user_profile(UserRegisterRequest(name='Test promoter', phone='+919999999999', promoter_category='sc', preferred_language='hi'), user))
    assert save.call_args.kwargs['phone'] == '+919876543210'
    assert save.call_args.kwargs['promoter_category'] == 'sc'
    assert save.call_args.kwargs['language'] == 'hi'


def test_explicit_zero_contribution_reaches_existing_pipeline():
    from app.routers.projects import _project_dict_to_user_input
    inputs = _project_dict_to_user_input({'project_cost': 300000, 'available_margin_capital': 0})
    assert inputs.available_margin_capital == 0


def test_preview_expiry_does_not_rerun_an_appraisal(monkeypatch):
    from app.routers import planning
    from app.core.enterprise_planning import Draft
    expired = Draft('alice', 1, None, {})
    monkeypatch.setattr(planning, 'draft_store', SimpleNamespace(get=AsyncMock(return_value=expired)))
    with pytest.raises(HTTPException) as error:
        asyncio.run(planning.saved_preview('expired', AuthenticatedUser(uid='alice')))
    assert error.value.status_code == 410


def test_progress_counts_explicit_unknown_answers_and_adapts_to_workspace(client):
    browser, _, _ = client
    browser.put('/onboarding/session', json={'journey': 'budget_only', 'location': LOCATION})
    initial = browser.get('/onboarding/question').json()
    assert initial['progress'] == {'completed': 0, 'total': 7}
    assert 'monthly_rent' not in initial['sequence']
    for field, value in [('own_cash',50000),('cash_confirmed',True),('skills','unknown'),('premise_type','rented')]:
        state = browser.post('/onboarding/answer', json={'field':field,'value':value}).json()
    assert state['progress'] == {'completed': 4, 'total': 8}
    assert state['question'] == 'monthly_rent'
    assert 'monthly_rent' in state['sequence']


def test_unchanged_revision_preserves_saved_appraisal_and_confirmation(client):
    browser, _, _ = client
    browser.put('/onboarding/session', json={'journey':'budget_only','location':LOCATION,
        'answers':{'own_cash':50000,'cash_confirmed':True,'review_confirmed':True},'preview_id':'saved-preview'})
    state = browser.post('/onboarding/revise', json={'field':'own_cash','value':'50000'}).json()
    assert state['draft']['preview_id'] == 'saved-preview'
    assert state['draft']['answers']['cash_confirmed'] is True
    assert state['draft']['answers']['review_confirmed'] is True


def test_changed_money_requires_confirmation_and_invalidates_only_appraisal(client):
    browser, _, _ = client
    answers = {'own_cash':50000,'cash_confirmed':True,'skills':'Tailoring','premise_type':'owned','resources':'none','preferences':'none','review_confirmed':True}
    browser.put('/onboarding/session', json={'journey':'budget_only','location':LOCATION,'answers':answers,'preview_id':'old'})
    response = browser.post('/onboarding/revise', json={'field':'own_cash','value':0})
    assert response.status_code == 200
    state = response.json()
    assert state['question'] == 'cash_confirmed'
    assert state['draft']['answers']['own_cash'] == 0
    assert state['draft']['answers']['skills'] == 'Tailoring'
    assert state['draft']['answers']['premise_type'] == 'owned'
    assert 'review_confirmed' not in state['draft']['answers']
    assert state['draft']['preview_id'] is None


def test_changing_hybrid_back_to_original_restores_original_idea(client):
    browser, _, _ = client
    answers = {'idea':'Make curd in artisan pots.', 'original_idea':'Make curd for local shops', 'business_id':'dairy_aggregation',
        'idea_confirmed':True,'odop_choice':'hybrid','enterprise_name':'Curd and pottery','own_cash':0,'cash_confirmed':True}
    browser.put('/onboarding/session', json={'journey':'idea_only','location':LOCATION,'answers':answers})
    state = browser.post('/onboarding/revise', json={'field':'odop_choice','value':'original'}).json()
    assert state['draft']['answers']['idea'] == answers['original_idea']
    assert 'enterprise_name' not in state['draft']['answers']
    assert 'original_idea' not in state['draft']['answers']
    assert state['draft']['answers']['own_cash'] == 0


def test_revisions_reject_missing_fields_and_remain_owner_scoped(client):
    browser, owner, _ = client
    browser.put('/onboarding/session', json={'journey':'budget_only','location':LOCATION,'answers':{'own_cash':50000}})
    assert browser.post('/onboarding/revise', json={'field':'phone','value':'123456'}).status_code == 409
    owner['uid'] = 'bob'
    assert browser.post('/onboarding/revise', json={'field':'own_cash','value':0}).status_code == 409
