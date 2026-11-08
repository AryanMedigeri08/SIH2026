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
