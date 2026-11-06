"""Conversation scenarios and safety boundaries; all external intelligence is stubbed explicitly."""
import asyncio
import sqlite3
import json
import sys
import types
import uuid
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend' / 'app' / 'core'))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import onboarding as engine
from app.core.onboarding_understanding import fallback_extract, understand
from app.core.onboarding_location import OnboardingLocation, LocationUnavailable
from app.database import DatabaseManager
from app.models.onboarding import new_session, Facts, LocationSelection, GPSRequest
from app.models.schemas import UserInput
from app.routers import onboarding as api


LOC = {"state_name": "Maharashtra", "district_name": "Pune", "block_name": "Haveli", "village_name": "Example",
       "state_code": 27, "district_code": 490, "block_code": 123, "village_code": 456,
       "is_rural": True, "area_source": "lgd", "latitude": 18.5, "longitude": 73.9}


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def offline_intelligence(monkeypatch):
    async def regional(state):
        return {"evidence": {"confidence": "MEDIUM", "plain_language_summary": "Test regional evidence"}, "location": deepcopy(state["location"])}
    monkeypatch.setattr(engine, "regional_assessment", regional)
    monkeypatch.setattr(engine, "find_district_odop", lambda *_: None)
    from app.core.chat_service import ChatService
    monkeypatch.setattr(ChatService, "_get_api_key", lambda self: None)


def session():
    state = new_session({"name": "Asha", "gender": "Female", "promoter_category": "obc"})
    state.update(location=deepcopy(LOC), location_confirmed=True)
    return state


def update(state, facts, correction=False):
    engine.apply_updates(state, facts, correction=correction)
    run(engine.advance(state))
    return state["next"]["field"]


def requirements(state, **extra):
    update(state, {"idea": "I want a dairy processing unit", "activity": "process", "products": "paneer",
        "operations": "pasteuriser, reliable milk supply and two workers", "scale": "100 kg per day", **extra})
    state["business_confirmed"] = True
    run(engine.advance(state))


def assessed(own=100000, premises="owned"):
    state = session()
    requirements(state, premises=premises, space="600 square feet", premises_suitable=True)
    if premises == "rented":
        update(state, {"rent_amount": 60000, "rent_period": "annual"})
    update(state, {"cost_items": {"equipment": 350000, "premises_setup": 50000, "inventory": 50000, "working_capital": 50000},
                   "cost_basis": "Supplier estimates for the specified paneer unit", "personal_contribution": own})
    return state


def test_idea_without_budget_requires_real_requirements_before_money():
    state = session()
    assert update(state, {"idea": "I want a dairy processing unit"}) == "activity"
    assert state["assessment"] is None
    assert update(state, {"activity": "process", "products": "paneer"}) in ("operations", "odop_preference")
    assert state["estimate"] is None
    requirements(state, premises="owned", space="600 square feet", premises_suitable=True)
    assert state["next"]["field"] == "cost_items"
    update(state, {"cost_items": {"equipment": 300000, "working_capital": 100000}, "cost_basis": "supplier estimates"})
    assert state["next"]["field"] == "personal_contribution"
    assert state["assessment"] is None


def test_sufficient_capital_no_automatic_loan_or_enterprise_name():
    state = assessed(own=600000)
    assert state["assessment"]["capital_deficit"] == 0
    assert engine.value(state, "financing_choice") is None
    assert state["next"]["field"] == "financing_choice"
    update(state, {"financing_choice": "self"})
    assert state["next"]["field"] == "enterprise_name"
    update(state, {"enterprise_name": "Asha Paneer"})
    payload = engine.report_input(state)
    assert payload["project_cost"] == 500000
    assert payload["available_margin_capital"] == 600000
    assert payload["project_cost_components"]["equipment"] == 350000
    assert payload["financing_choice"] == "self"


def test_insufficient_budget_and_own_contribution_are_distinct():
    state = assessed(own=20000)
    update(state, {"budget": 300000, "budget_kind": "total"})
    assert engine.value(state, "personal_contribution") == 20000
    assert state["assessment"]["capital_deficit"] == 480000
    assert state["assessment"]["budget_shortfall"] == 200000
    assert set(state["next"]["choices"]) == {"increase", "normal", "sca"}
    assert state["assessment"]["capital_structure"]["equity_gap"] == 5000
    update(state, {"financing_choice": "increase"})
    assert state["next"]["field"] == "personal_contribution"
    update(state, {"personal_contribution": 100000}, correction=True)
    assert state["assessment"]["capital_deficit"] == 400000
    assert engine.value(state, "financing_choice") is None


def test_no_idea_with_capital_supported_recommendations_and_reject_all():
    state = session()
    update(state, {"idea_status": "explore", "budget": 500000, "budget_kind": "total"})
    assert state["next"]["field"] == "skills"
    update(state, {"skills": "open to learning", "constraints": "use agricultural supplies, no particular activity excluded"})
    assert state["next"]["field"] == "recommendations"
    assert 2 <= len(state["recommendations"]) <= 3
    assert all(r["outlay_range"][0] <= 500000 for r in state["recommendations"])
    assert all("Regional catalogue" in r["market_evidence"] for r in state["recommendations"])
    state["rejected"] = [r["id"] for r in state["recommendations"]]
    run(engine.advance(state))
    assert not set(state["rejected"]) & {r["id"] for r in state["recommendations"]}


def test_change_business_preserves_capital_and_location_but_invalidates_cost():
    state = assessed()
    update(state, {"idea": "I want a mobile repair service", "activity": "service", "products": "phone repair"}, correction=True)
    assert state["assessment"] is None
    assert state["regional"] is None
    assert engine.value(state, "project_cost") is None
    assert engine.value(state, "cost_items") is None
    assert engine.value(state, "personal_contribution") == 100000
    assert state["location_confirmed"] is True
    assert state["classification"]["sector"] == "repair"
    assert state["next"]["field"] in ("operations", "odop_preference")


def test_location_change_invalidates_regional_financial_and_odop_only():
    state = assessed()
    engine.invalidate(state, {"location"})
    state["location"] = {**LOC, "district_name": "Nagpur"}
    state["location_confirmed"] = False
    run(engine.advance(state))
    assert state["next"]["field"] == "location_confirmation"
    assert state["assessment"] is None and state["regional"] is None
    assert engine.value(state, "products") == "paneer"
    assert engine.value(state, "personal_contribution") == 100000


def test_owned_premises_require_suitability_and_do_not_ask_rent():
    state = session()
    requirements(state, premises="owned", space="500 square feet")
    assert state["next"]["field"] == "premises_suitable"
    assert state["assessment"] is None
    update(state, {"premises_suitable": True})
    assert state["next"]["field"] == "cost_items"


def test_rented_premises_never_supply_default_rent():
    state = session()
    requirements(state, premises="rented", space="400 square feet", premises_suitable=True)
    assert state["next"]["field"] == "rent_amount"
    update(state, {"rent_amount": 12000})
    assert state["next"]["field"] == "rent_period"
    assert state["assessment"] is None


def test_rent_voice_transcript_and_annual_conversion():
    state = assessed(premises="rented")
    assert state["assessment"]["monthly_rent"] == 5000
    extracted = fallback_extract("The rent is ₹6,000 per month", "rent_amount")
    update(state, extracted, correction=True)
    assert state["assessment"]["monthly_rent"] == 6000
    assert engine.value(state, "rent_period") == "monthly"


def test_odop_offer_preserves_idea_and_allows_exploration(monkeypatch):
    monkeypatch.setattr(engine, "find_district_odop", lambda *_: {"matched_state_name": "Maharashtra", "matched_district_name": "Pune", "odop_product": "Food products", "matching_sectors": ["food_processing"]})
    state = session()
    update(state, {"idea": "dairy processing", "activity": "process", "products": "paneer"})
    assert state["next"]["field"] == "odop_preference"
    update(state, {"odop_preference": "explore"})
    assert state["next"]["field"] == "odop_explore"
    assert engine.value(state, "idea") == "dairy processing"
    update(state, {"odop_preference": "keep"}, correction=True)
    assert state["next"]["field"] == "operations"


def test_reject_odop_keeps_original_idea_and_no_fake_product(monkeypatch):
    monkeypatch.setattr(engine, "find_district_odop", lambda *_: None)
    state = session()
    update(state, {"idea": "dairy processing", "activity": "process", "products": "paneer", "odop_preference": "reject"})
    assert state["odop"] is None
    assert state["next"]["field"] == "operations"
    assert engine.value(state, "idea") == "dairy processing"


def test_ambiguous_business_and_unqualified_budget_cannot_finalize():
    state = session()
    update(state, fallback_extract("I want to start a business and can invest 5 lakh", "idea"))
    assert state["classification"] is None
    assert state["assessment"] is None
    assert engine.value(state, "budget") == 500000
    assert engine.value(state, "personal_contribution") is None
    assert state["next"]["field"] == "activity"


def test_multiple_answers_are_collected_and_not_reasked():
    state = session()
    facts = fallback_extract("I want to start a dairy processing unit, I already own land, and I can invest ₹5 lakh.", "idea")
    update(state, facts)
    assert engine.value(state, "idea")
    assert engine.value(state, "premises") == "owned"
    assert engine.value(state, "budget") == 500000
    assert engine.value(state, "personal_contribution") is None
    assert state["next"]["field"] == "products"


def test_contradictions_are_confirmed_before_recalculation():
    state = assessed()
    update(state, {"personal_contribution": 50000})
    assert state["next"]["field"] == "pending_changes"
    assert state["assessment"] is None
    assert engine.value(state, "personal_contribution") == 100000
    changes = state["pending_changes"]
    state["pending_changes"] = {}
    update(state, changes, correction=True)
    assert state["assessment"]["personal_contribution"] == 50000


def test_cost_components_sum_and_dont_use_uniform_machinery_percentage():
    state = assessed()
    update(state, {"cost_items": {"equipment": 100000}}, correction=True)
    assert state["assessment"] is None  # Old total differs; confirmation required.
    assert state["pending_changes"]["project_cost"] == 250000
    changes = state["pending_changes"]
    state["pending_changes"] = {}
    update(state, changes, correction=True)
    assert state["assessment"]["project_outlay"] == 250000
    assert state["assessment"]["capital_structure"]["actual_machinery_cost"] == 100000
    assert state["assessment"]["capital_structure"]["true_project_outlay"] == 250000


@pytest.mark.parametrize("facts", [{"budget": -1}, {"rent_amount": -1}, {"personal_contribution": float('nan')},
    {"cost_items": {"equipment": float('inf')}}, {"is_rural": True}, {"subsidy": 100000}])
def test_invalid_and_derived_inputs_rejected(facts):
    with pytest.raises(ValueError):
        Facts(**facts)


def test_failure_hides_stale_calculation(monkeypatch):
    state = assessed()
    def fail(_):
        raise RuntimeError("calculation offline")
    monkeypatch.setattr(engine, "financial_assessment", fail)
    update(state, {"personal_contribution": 200000}, correction=True)
    assert state["assessment"] is None
    assert state["next"]["field"] == "calculation"


def test_no_financial_evaluation_before_location_confirmation():
    state = assessed()
    state["location_confirmed"] = False
    state["assessment"] = None
    run(engine.advance(state))
    assert state["assessment"] is None
    assert state["next"]["field"] == "location_confirmation"


@pytest.fixture
def client(monkeypatch, tmp_path):
    from app.core.translation_service import TranslationService
    async def no_external_translation(self, text, target_language='hi', source_language='en', **_):
        return {'translated_text': text, 'provider': 'identity'}
    monkeypatch.setattr(TranslationService, 'translate_text', no_external_translation)
    manager = DatabaseManager()
    manager.sqlite = sqlite3.connect(tmp_path / 'onboarding.sqlite3', check_same_thread=False)
    manager.sqlite.row_factory = sqlite3.Row
    manager.sqlite.executescript('''PRAGMA foreign_keys=ON;
        CREATE TABLE users(firebase_uid TEXT PRIMARY KEY,email TEXT,name TEXT,gender TEXT,promoter_category TEXT,auth_provider TEXT,phone TEXT,additional_business_details TEXT,language TEXT,created_at TEXT,updated_at TEXT,last_login_at TEXT);
        CREATE TABLE onboarding_sessions(user_id TEXT PRIMARY KEY REFERENCES users(firebase_uid) ON DELETE CASCADE,revision INTEGER,payload TEXT);
        CREATE TABLE revoked_sessions(token_hash TEXT PRIMARY KEY,user_id TEXT,revoked_at TEXT);
        CREATE TABLE evaluator_sessions(token_hash TEXT PRIMARY KEY,user_id TEXT REFERENCES users(firebase_uid) ON DELETE CASCADE,expires_at REAL);
        CREATE TABLE projects(project_id TEXT PRIMARY KEY,user_id TEXT,payload TEXT,created_at TEXT,updated_at TEXT);
        CREATE TABLE feasibility_reports(report_id TEXT PRIMARY KEY,user_id TEXT,payload TEXT,created_at TEXT);
    ''')
    monkeypatch.setattr(api, 'db_manager', manager)
    from app.core import auth_dependency
    from app.routers import auth, chat
    monkeypatch.setattr(auth_dependency, 'db_manager', manager)
    monkeypatch.setattr(auth, 'db_manager', manager)
    app = FastAPI()
    app.include_router(api.router, prefix='/api/v2')
    app.include_router(auth.router, prefix='/api/v2')
    app.include_router(chat.router, prefix='/api/v2/chat')
    test_client = TestClient(app)
    test_client.headers['Authorization'] = 'Bearer test-token-mira-test:asha@example.com'
    run(manager.upsert_user('mira-test', 'asha@example.com', 'Asha', gender='Female', promoter_category='obc'))
    yield test_client, manager
    manager.sqlite.close()


def api_turn(client, state, **kwargs):
    result = client.post('/api/v2/onboarding/turn', json={'revision': state['revision'], 'request_id': str(uuid.uuid4()), **kwargs})
    assert result.status_code == 200, result.text
    return result.json()['state']


def test_voice_text_switch_pause_and_process_restart_resume(client):
    client, db = client
    state = client.get('/api/v2/onboarding/session').json()['state']
    assert state['next']['field'] == 'location'
    state = api_turn(client, state, text='I want a dairy processing unit and I own land', source='voice')
    assert engine.value(state, 'premises') == 'owned'
    state = api_turn(client, state, updates={'budget': 500000, 'budget_kind': 'personal'}, source='text')
    assert engine.value(state, 'personal_contribution') == 500000
    state = api_turn(client, state, action='pause')
    assert state['paused']
    db_path = db.sqlite.execute('PRAGMA database_list').fetchone()[2]
    db.sqlite.close()
    db.sqlite = sqlite3.connect(db_path, check_same_thread=False)
    db.sqlite.row_factory = sqlite3.Row
    db.in_memory_onboarding.clear()
    db.in_memory_users.clear()
    restored = client.get('/api/v2/onboarding/session').json()['state']
    assert restored['fields'] == state['fields']
    assert restored['paused']
    restored = api_turn(client, restored, text='resume')
    assert not restored['paused']
    assert {turn.get('source') for turn in restored['history']} >= {'voice', 'text'}


def test_reused_speech_endpoint_feeds_reviewed_transcript_into_same_state(client, monkeypatch):
    client, _ = client
    from app.routers import chat
    async def transcribe(*args, **kwargs):
        return 'Rent is five thousand per month'
    monkeypatch.setattr(chat.bhashini_client, 'transcribe', transcribe)
    response = client.post('/api/v2/chat/stt', files={'file': ('answer.wav', b'test fixture audio', 'audio/wav')}, data={'language': 'en'})
    assert response.status_code == 200, response.text
    assert response.json()['provider'] == 'bhashini'
    state = client.get('/api/v2/onboarding/session').json()['state']
    state = api_turn(client, state, text=response.json()['transcript'], source='voice')
    assert engine.value(state, 'rent_amount') == 5000 and engine.value(state, 'rent_period') == 'monthly'
    state = api_turn(client, state, text='Rent is six thousand per month', source='text', correction=True)
    assert engine.value(state, 'rent_amount') == 6000


def test_revision_idempotency_and_owner_isolation(client):
    client, db = client
    state = client.get('/api/v2/onboarding/session').json()['state']
    payload = {'revision': state['revision'], 'request_id': 'request-1234', 'updates': {'budget': 500000}}
    first = client.post('/api/v2/onboarding/turn', json=payload)
    assert first.status_code == 200
    duplicate = client.post('/api/v2/onboarding/turn', json=payload)
    assert duplicate.json()['state']['revision'] == first.json()['state']['revision']
    payload['request_id'] = 'request-5678'
    assert client.post('/api/v2/onboarding/turn', json=payload).status_code == 409
    other = client.get('/api/v2/onboarding/session', headers={'Authorization': 'Bearer test-token-other:other@example.com'}).json()['state']
    assert 'budget' not in other['fields']
    assert client.get('/api/v2/onboarding/session', headers={'Authorization': ''}).status_code == 401


def test_unsigned_evaluator_tokens_are_rejected_when_test_auth_is_disabled(client, monkeypatch):
    client, _ = client
    from app.config import settings
    monkeypatch.setattr(settings, 'ALLOW_TEST_AUTH', False)
    assert client.get('/api/v2/onboarding/session').status_code == 401
    assert client.get('/api/v2/auth/me').status_code == 401


def test_report_input_requires_finished_session_and_rejects_output_injection(client):
    client, db = client
    state = client.get('/api/v2/onboarding/session').json()['state']
    assert client.post('/api/v2/onboarding/report-input', json={'revision': state['revision']}).status_code == 422
    assert client.post('/api/v2/onboarding/turn', json={'revision': 0, 'request_id': 'request-1234', 'updates': {'is_rural': True}}).status_code == 422


def test_profile_demographics_survive_upsert_and_memory_clear(client):
    client, db = client
    run(db.upsert_user('mira-test', 'mira-test@udyam.gov.in', 'Asha'))
    db.in_memory_users.clear()
    profile = run(db.get_user('mira-test'))
    assert profile['gender'] == 'Female' and profile['promoter_category'] == 'obc'
    assert profile['email'] == 'asha@example.com'


def test_existing_register_and_signin_contract_seed_mira_without_reasking(client):
    client, _ = client
    response = client.post('/api/v2/auth/register', json={'name': 'Asha Test', 'gender': 'Female', 'promoter_category': 'sc'})
    assert response.status_code == 201, response.text
    profile = client.post('/api/v2/auth/session').json()
    assert profile['name'] == 'Asha Test' and profile['promoter_category'] == 'sc'
    state = client.get('/api/v2/onboarding/session').json()['state']
    assert state['next']['field'] == 'location'
    assert engine.value(state, 'promoter_category') == 'sc'


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.calls = []
    async def fetchrow(self, sql, *args):
        self.calls.append((sql, args))
        return self.row if args == (27, 490, 123, 456) else None


class FakePool:
    def __init__(self, connection):
        self.connection = connection
    def acquire(self):
        return self
    async def __aenter__(self):
        return self.connection
    async def __aexit__(self, *args):
        pass


def test_hierarchy_validation_and_area_verification_fallback():
    row = {**LOC, 'development_block_name': 'Haveli'}
    db = types.SimpleNamespace(pool=FakePool(FakeConnection(row)))
    service = OnboardingLocation(db)
    selected = LocationSelection(revision=0, state_code=27, district_code=490, block_code=123, village_code=456)
    assert run(service.select(selected))['is_rural'] is True
    with pytest.raises(ValueError):
        run(service.select(selected.model_copy(update={'block_code': 999})))
    del row['is_rural']
    result = run(service.select(selected))
    assert result['is_rural'] is None and result['area_source'] == 'classification_unavailable'
    result = run(service.select(selected.model_copy(update={'verified_is_rural': False})))
    assert result['is_rural'] is None  # User selection cannot manufacture official classification.
    # An authoritative flag always wins over a client override.
    row['is_rural'] = True
    assert run(service.select(selected.model_copy(update={'verified_is_rural': False})))['is_rural'] is True


def test_location_offline_and_inaccurate_gps_never_fabricate():
    service = OnboardingLocation(types.SimpleNamespace(pool=None))
    with pytest.raises(LocationUnavailable):
        run(service.options('blocks', 123))
    with pytest.raises(ValueError, match='imprecise'):
        run(service.detect(GPSRequest(revision=0, latitude=18, longitude=73, accuracy=150000)))


def test_gps_candidate_requires_unique_lgd_join_and_is_not_confirmed(client, monkeypatch):
    client, db = client
    from app.core import onboarding_location as locations
    import httpx
    state = client.get('/api/v2/onboarding/session').json()['state']
    location = {**LOC, 'development_block_name': 'Haveli'}
    conn = FakeConnection(location)
    candidates = [{'state_code': 27, 'district_code': 490, 'development_block_code': 123, 'village_code': 456}]
    async def fetch(sql, *args):
        assert args == ('maharashtra', ['pune'], ['example'])
        return candidates
    conn.fetch = fetch
    service = OnboardingLocation(types.SimpleNamespace(pool=FakePool(conn)))
    monkeypatch.setattr(api, 'OnboardingLocation', lambda _: service)
    http_client = httpx.AsyncClient
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={'address': {
        'state': 'Maharashtra', 'district': 'Pune', 'village': 'Example', 'house_number': '7'}}))
    monkeypatch.setattr(locations.httpx, 'AsyncClient', lambda **kwargs: http_client(transport=transport, **kwargs))
    gps = {'revision': state['revision'], 'latitude': 18.5, 'longitude': 73.9, 'accuracy': 50}
    result = client.post('/api/v2/onboarding/location/detect', json=gps).json()['state']
    assert result['location']['village_name'] == 'Example'
    assert not result['location_confirmed'] and result['next']['field'] == 'location_confirmation'
    assert 'house_number' not in str(result['physical_location']) and 'latitude' not in result['physical_location']
    result = api_turn(client, result, action='change_location')
    candidates.append({**candidates[0], 'village_code':457})
    gps['revision'] = result['revision']
    result = client.post('/api/v2/onboarding/location/detect', json=gps).json()['state']
    assert result['location'] is None and not result['location_confirmed']


def test_confirmed_input_reconciles_costs_and_preserves_zero_equity():
    state = assessed(own=0)
    update(state, {'financing_choice': 'sca', 'enterprise_name': 'Asha Dairy'})
    payload = engine.report_input(state)
    inp = UserInput(**payload)
    assert inp.available_margin_capital == 0
    with pytest.raises(ValueError, match='equal'):
        UserInput(**{**payload, 'project_cost': 999999})


def test_spoken_amounts_and_period_are_captured_together():
    assert fallback_extract('Five thousand per month', 'rent_amount') == {'rent_amount': 5000, 'rent_period': 'monthly'}
    assert fallback_extract('पाच लाख', 'budget')['budget'] == 500000
    assert fallback_extract('My budget is five lakh of my own savings', 'budget')['budget_kind'] == 'personal'
    assert fallback_extract('I have five lakh but no business idea', 'idea') == {'idea_status': 'explore', 'budget': 500000}
    assert fallback_extract('Dairy processing unit', 'idea')['idea'] == 'Dairy processing unit'


def test_model_can_extract_multiple_fields_but_cannot_change_money_or_geography(monkeypatch):
    from app.core.chat_service import ChatService
    monkeypatch.setattr(ChatService, '_get_api_key', lambda self: 'test-key')
    monkeypatch.setattr(ChatService, '_call_llm_chat_completion', lambda *args, **kwargs: ('', {
        'name': 'record_user_facts', 'arguments': {
            'updates': {'idea': 'Dairy', 'budget': 2000000, 'is_rural': False, 'subsidy': 300000, 'premises': 'owned'},
            'evidence': {'idea': 'Dairy', 'budget': '5 lakh', 'premises': 'I own land'}, 'ambiguities': []}}, 'stub'))
    state = session()
    run(engine.advance(state))
    updates, _, _ = run(understand('Dairy, I own land and can invest 5 lakh.', state))
    assert updates['budget'] == 500000 and updates['premises'] == 'owned'
    assert 'is_rural' not in updates and 'subsidy' not in updates


def test_correction_from_personal_to_total_clears_inferred_contribution():
    state = session()
    update(state, {'budget': 500000, 'budget_kind': 'personal'})
    assert engine.value(state, 'personal_contribution') == 500000
    update(state, {'budget_kind': 'total'}, correction=True)
    assert engine.value(state, 'personal_contribution') is None


@pytest.mark.parametrize('financing_choice', ['normal', 'sca'])
def test_completed_conversation_creates_one_existing_project_and_dpr(client, monkeypatch, financing_choice):
    client, db = client
    from app.routers import feasibility, projects
    from amenities_client import VillageAmenitiesResult
    from executive_synthesizer import generate_executive_synthesis
    monkeypatch.setattr(projects, 'db_manager', db)
    monkeypatch.setattr(feasibility, 'db_manager', db)
    monkeypatch.setattr(feasibility, 'generate_executive_synthesis', lambda data, language: generate_executive_synthesis(data, language, force_fallback=True))
    monkeypatch.setattr(feasibility, 'fetch_village_amenities', lambda **_: VillageAmenitiesResult(7.0, 20, True, True, True, False, 'test_fixture'))
    async def select(self, _):
        return deepcopy(LOC)
    monkeypatch.setattr(api.OnboardingLocation, 'select', select)
    state = client.get('/api/v2/onboarding/session').json()['state']
    selected = client.put('/api/v2/onboarding/location', json={'revision': state['revision'], 'state_code': 27,
        'district_code': 490, 'block_code': 123, 'village_code': 456})
    assert selected.status_code == 200, selected.text
    state = selected.json()['state']
    state = api_turn(client, state, text='yes', source='voice')
    state = api_turn(client, state, updates={
        'idea': 'Paneer processing', 'activity': 'process', 'products': 'paneer', 'operations': 'pasteuriser and chill storage',
        'scale': '200 kg per month', 'premises': 'rented', 'space': '600 square feet', 'premises_suitable': True,
        'personal_contribution': 0, 'cost_items': {'equipment': 310000, 'inventory': 50000, 'working_capital': 90000},
        'cost_basis': 'local supplier quotes', 'odop_preference': 'reject'})
    state = api_turn(client, state, action='confirm_business')
    assert state['next']['field'] == 'rent_amount' and state['assessment'] is None
    state = api_turn(client, state, text='Five thousand per month', source='voice')
    assert state['assessment']['monthly_rent'] == 5000
    state = api_turn(client, state, updates={'financing_choice': financing_choice})
    state = api_turn(client, state, text='Asha Paneer Works')
    assert state['next']['field'] == 'ready'
    command = {'revision': state['revision']}
    result = client.post('/api/v2/onboarding/complete', json=command)
    assert result.status_code == 200, result.text
    project = result.json()
    assert project['available_margin_capital'] == 0 and project['monthly_rent'] == 5000
    assert project['financing_choice'] == financing_choice
    assert project['expected_monthly_units'] == 200
    report = project['analysis_result']['report']
    dpr = project['analysis_result']['dpr']['section_2_capital_outlay_and_finance']
    assert report['input_parameters']['project_cost'] == report['capital_structure']['true_project_outlay'] == 450000
    assert report['capital_structure']['actual_machinery_cost'] == 310000
    assert report['input_parameters']['is_rural'] is True
    assert report['financing_selection']['choice'] == financing_choice
    assert report['odop_alignment']['preference'] == 'reject' and not report['odop_alignment']['is_aligned']
    assert report['financing_selection']['remaining_funding_need'] == 450000
    assert dpr['capital_outlay']['total_capital_outlay'] == 450000
    assert dpr['capital_outlay']['plant_and_machinery']['amount_inr'] == 310000
    duplicate = client.post('/api/v2/onboarding/complete', json=command)
    assert duplicate.json()['project_id'] == project['project_id']
    assert run(db.get_user_projects_count('mira-test')) == 1


def test_legacy_finance_functions_match_branch_baseline_exactly():
    # Golden numbers captured from operation-goldrush before adding Mira.
    baseline = json.loads((Path(__file__).parent / 'fixtures' / 'mira_legacy_finance.json').read_text(encoding='utf-8'))
    import app.core.financial_calculator as current
    for case in baseline['cases']:
        cost = case['input']['machinery_cost']
        capital = current.calculate_asset_driven_capital_structure(**case['input']).to_dict()
        assert {key: capital[key] for key in case['capital']} == case['capital']
        assert current.emi_with_moratorium(cost, 9.5, 5, 6).to_dict() == case['emi']
        assert current.working_capital_estimate(cost, 'dairy').to_dict() == case['working_capital']
        ranked = current.rank_eligible_schemes(project_cost=cost, business_category='manufacturing', sector='dairy',
            promoter_category=case['input']['promoter_category'], is_rural=True)
        assert [{key: getattr(scheme, key) for key in case['schemes'][0]} for scheme in ranked] == case['schemes']
