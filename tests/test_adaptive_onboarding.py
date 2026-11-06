"""Audio and typed answers use one persisted dependency-driven conversation."""
import asyncio
import sys
from pathlib import Path
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from test_mira_onboarding import client as stored_client, LOC
from app.routers import onboarding as api
from app.core import onboarding as engine


@pytest.fixture
def conversation(stored_client, monkeypatch):
    client, db = stored_client
    asyncio.run(db.update_user('mira-test', {'phone':'+919999999999'}))
    from app.core.chat_service import ChatService
    monkeypatch.setattr(ChatService, '_get_api_key', lambda *_: None)
    from app.core.translation_service import TranslationService
    async def no_external_translation(self, text, target_language, source_language='en'):
        return {'translated_text': text, 'provider': 'identity'}
    monkeypatch.setattr(TranslationService, 'translate_text', no_external_translation)
    monkeypatch.setattr(engine, 'find_district_odop', lambda *_: None)
    async def regional(state):
        return {'recommendation': 'MODERATE_OPPORTUNITY', 'confidence': 'MEDIUM',
            'evidence': {'confidence': 'MEDIUM', 'plain_language_summary': 'Synthetic regional test evidence'},
            'location': state['location']}
    monkeypatch.setattr(engine, 'regional_assessment', regional)
    async def select(self, _):
        return deepcopy(LOC)
    monkeypatch.setattr(api.OnboardingLocation, 'select', select)
    response = client.get('/api/v2/onboarding/session?experience=adaptive')
    assert response.status_code == 200, response.text
    state = response.json()['state']
    response = client.put('/api/v2/onboarding/location', json={'revision': state['revision'], 'state_code': 27,
        'district_code': 490, 'block_code': 123, 'village_code': 456})
    state = response.json()['state']
    return client, db, answer(client, state, text='yes', source='voice')


def answer(client, state, **kwargs):
    import uuid
    result = client.post('/api/v2/onboarding/turn', json={'revision': state['revision'], 'request_id': str(uuid.uuid4()), **kwargs})
    assert result.status_code == 200, result.text
    return result.json()['state']


def define_business(client, state, **extra):
    state = answer(client, state, updates={'idea': 'Paneer processing', 'products': 'paneer', 'activity': 'process', 'scale': '100 kg per day', **extra})
    assert state['next']['field'] == 'business_confirmation'
    return answer(client, state, text='yes', source='voice')


def test_idea_without_budget_receives_regional_and_cost_estimate_before_asking_cash(conversation):
    client, _, state = conversation
    state = define_business(client, state)
    assert state['regional']['recommendation'] == 'MODERATE_OPPORTUNITY'
    assert state['next']['field'] == 'premises'
    state = answer(client, state, updates={'premises': 'owned'})
    assert state['next']['field'] == 'cost_proposal'
    proposal = state['cost_proposal']
    assert 'not a supplier quote' in proposal['basis'].lower()
    assert engine.value(state, 'project_cost') is None  # Estimate awaits user confirmation.
    state = answer(client, state, text='yes', source='voice')
    assert engine.value(state, 'project_cost') == sum(proposal['items'].values())
    assert state['next']['field'] == 'personal_contribution'
    state = answer(client, state, text='I can invest zero rupees', source='voice')
    assert state['assessment']['personal_contribution'] == 0
    assert state['assessment']['capital_deficit'] == proposal['total']
    assert state['next']['field'] == 'operating_plan'
    state = answer(client, state, action='use_operating_estimate')
    assert 'sca' in state['next']['choices']


def test_idea_with_own_budget_keeps_cash_separate_and_collects_actual_rent(conversation):
    client, _, state = conversation
    state = define_business(client, state, budget=10000, budget_kind='personal')
    assert engine.value(state, 'personal_contribution') == 10000
    state = answer(client, state, updates={'premises': 'rented'})
    assert state['next']['field'] == 'rent_amount'
    assert state['rent_proposal'] > 0
    state = answer(client, state, text='Five thousand per month', source='voice')
    assert engine.value(state, 'rent_amount') == 5000
    state = answer(client, state, action='confirm_estimate')
    assert state['assessment']['monthly_rent'] == 5000
    assert state['assessment']['project_outlay'] != 10000
    state = answer(client, state, action='use_operating_estimate')
    assert 'sca' in state['next']['choices']
    assert state['assessment']['normal_loan']['tenure_years'] == 7
    state = answer(client, state, updates={'financing_choice': 'sca'})
    assert state['next']['field'] == 'financial_review'
    state = answer(client, state, action='accept_financial_risk')
    assert state['next']['field'] == 'enterprise_name'
    state = answer(client, state, text='Asha Paneer Works')
    assert state['next']['field'] == 'ready'
    result = engine.report_input(state)
    assert result['monthly_rent'] == 5000 and result['available_margin_capital'] == 10000
    assert result['financing_choice'] == 'sca'


def test_budget_without_idea_gets_two_or_three_screened_choices(conversation):
    client, _, state = conversation
    state = answer(client, state, text='I have no idea and I have 2 lakh of my own savings', source='voice')
    assert state['next']['field'] == 'skills'
    state = answer(client, state, text='Open to learning')
    assert state['next']['field'] == 'recommendations'
    assert 2 <= len(state['recommendations']) <= 3
    for candidate in state['recommendations']:
        assert candidate['regional_assessment']['confidence'] == 'MEDIUM'
    state = answer(client, state, recommendation_id=state['recommendations'][0]['id'])
    assert engine.value(state, 'idea')
    assert state['next']['field'] == 'scale'
    assert engine.value(state, 'personal_contribution') == 200000


def test_no_unsupported_claim_of_feasibility_for_saturated_candidates(conversation, monkeypatch):
    client, _, state = conversation
    async def saturated(state):
        return {'recommendation': 'SATURATED_MARKET', 'confidence': 'HIGH', 'evidence': {}}
    monkeypatch.setattr(engine, 'regional_assessment', saturated)
    state = answer(client, state, updates={'idea_status': 'explore', 'budget': 100000, 'budget_kind': 'personal', 'skills': 'open to learning'})
    assert state['recommendations'] == []
    assert state['next']['field'] == 'recommendations'


def test_increasing_own_cash_recomputes_and_finishes_before_enterprise_name(conversation):
    client, _, state = conversation
    state = define_business(client, state, personal_contribution=0, premises='owned')
    state = answer(client, state, action='confirm_estimate')
    state = answer(client, state, action='use_operating_estimate')
    state = answer(client, state, updates={'financing_choice': 'increase'})
    assert state['next']['field'] == 'personal_contribution'
    state = answer(client, state, text='5000000 rupees')
    assert state['next']['field'] == 'pending_changes'
    state = answer(client, state, action='confirm_change')
    assert state['assessment']['personal_contribution'] == 5000000
    assert state['assessment']['capital_deficit'] == 0
    state = answer(client, state, updates={'financing_choice': 'self'})
    assert state['next']['field'] == 'enterprise_name'


def test_resume_preserves_adaptive_questions_and_confirmed_answers(conversation):
    client, db, state = conversation
    state = define_business(client, state, personal_contribution=25000)
    db.in_memory_onboarding.clear()
    resumed = client.get('/api/v2/onboarding/session?experience=adaptive').json()['state']
    assert resumed['experience'] == 'adaptive'
    assert engine.value(resumed, 'personal_contribution') == 25000
    assert resumed['next']['field'] == state['next']['field']


def test_correction_invalidates_costs_and_regional_decision(conversation):
    client, _, state = conversation
    state = define_business(client, state, personal_contribution=10000, premises='owned')
    state = answer(client, state, action='confirm_estimate')
    assert state['assessment']
    state = answer(client, state, correction=True, updates={'idea': 'Phone repair workshop', 'products': 'phone repair', 'activity': 'service'})
    assert state['assessment'] is None
    assert engine.value(state, 'cost_items') is None
    assert state['next']['field'] == 'scale'


def test_odop_waits_for_explicit_choice_and_alignment_restarts_business_clarification(conversation,monkeypatch):
    client,_,state=conversation
    monkeypatch.setattr(engine,'find_district_odop',lambda *_:{'matched_state_name':'Maharashtra','matched_district_name':'Pune','odop_product':'Food products','matching_sectors':['food_processing']})
    state=define_business(client,state)
    assert state['next']['field']=='odop_preference'
    state=answer(client,state,text='not sure what that means')
    assert state['next']['field']=='odop_preference'
    assert client.get('/api/v2/onboarding/session?experience=adaptive').json()['state']['next']['field']=='odop_preference'
    state=answer(client,state,updates={'odop_preference':'explore'})
    assert state['next']['field']=='odop_explore'
    state=answer(client,state,action='align_odop')
    assert 'Food products' in engine.value(state,'idea')
    assert engine.value(state,'products') is None and state['assessment'] is None
    assert state['next']['field']=='activity'


def test_keeping_original_idea_after_odop_exploration_is_one_decision(conversation,monkeypatch):
    client,_,state=conversation
    monkeypatch.setattr(engine,'find_district_odop',lambda *_:{'matched_state_name':'Maharashtra','matched_district_name':'Pune','odop_product':'Food products','matching_sectors':['food_processing']})
    state=define_business(client,state)
    idea=engine.value(state,'idea')
    state=answer(client,state,updates={'odop_preference':'explore'})
    state=answer(client,state,text='keep my original idea')
    assert engine.value(state,'odop_preference')=='keep'
    assert engine.value(state,'idea')==idea and not state['pending_changes']
    assert state['next']['field']=='premises'


def test_poor_regional_result_offers_an_actual_change_of_path(conversation, monkeypatch):
    client, _, state = conversation
    async def saturated(state):
        return {'recommendation': 'SATURATED_MARKET', 'confidence': 'HIGH', 'evidence': {'plain_language_summary': 'Synthetic saturation evidence'}}
    monkeypatch.setattr(engine, 'regional_assessment', saturated)
    state = define_business(client, state)
    assert state['next']['field'] == 'regional_review'
    state = answer(client, state, action='explore_alternatives')
    assert engine.value(state, 'idea') is None
    assert engine.value(state, 'idea_status') == 'explore'
    assert state['assessment'] is None


def test_confirmed_estimate_reaches_real_report_pipeline_and_is_idempotent(conversation, monkeypatch):
    client, db, state = conversation
    from app.routers import feasibility, projects
    from amenities_client import VillageAmenitiesResult
    from executive_synthesizer import generate_executive_synthesis
    monkeypatch.setattr(projects, 'db_manager', db)
    monkeypatch.setattr(feasibility, 'db_manager', db)
    monkeypatch.setattr(feasibility, 'generate_executive_synthesis', lambda data, language: generate_executive_synthesis(data, language, force_fallback=True))
    monkeypatch.setattr(feasibility, 'fetch_village_amenities', lambda **_: VillageAmenitiesResult(7.0, 20, True, True, True, False, 'synthetic_fixture'))
    state = define_business(client, state, personal_contribution=0, premises='rented', rent_amount=3000, rent_period='monthly')
    state = answer(client, state, action='confirm_estimate')
    state = answer(client, state, action='use_operating_estimate')
    state = answer(client, state, updates={'financing_choice': 'sca'})
    state = answer(client, state, action='accept_financial_risk')
    state = answer(client, state, text='Asha Test Paneer')
    assert state['next']['field'] == 'ready'
    command = {'revision': state['revision']}
    response = client.post('/api/v2/onboarding/complete', json=command)
    assert response.status_code == 200, response.text
    project = response.json()
    report = project['analysis_result']['report']
    assert project['available_margin_capital'] == 0 and project['monthly_rent'] == 3000
    assert report['capital_structure']['true_project_outlay'] == engine.value(state, 'project_cost')
    assert report['financing_selection']['choice'] == 'sca'
    assert report['capital_structure']['actual_machinery_cost'] == engine.value(state, 'cost_items')['equipment']
    assert client.post('/api/v2/onboarding/complete', json=command).json()['project_id'] == project['project_id']
    assert asyncio.run(db.get_user_projects_count('mira-test')) == 1


def test_official_area_flags_take_precedence_over_manual_status():
    from app.core.onboarding_location import OnboardingLocation
    assert OnboardingLocation.area_flag({'rural_urban':'urban'}) is False
    assert OnboardingLocation.area_flag({'administrative_level':'VILLAGE'}) is True
    assert OnboardingLocation.area_flag({'is_rural':False, 'rural_urban':'rural'}) is False
    assert OnboardingLocation.area_flag({'administrative_level':'DISTRICT'}) is None


def test_reviewed_cost_correction_updates_sum_without_a_repeated_confirmation(conversation):
    client, _, state = conversation
    state = define_business(client, state, personal_contribution=10000, premises='owned')
    state = answer(client, state, action='confirm_estimate')
    costs = {**engine.value(state, 'cost_items'), 'equipment': 100000}
    state = answer(client, state, correction=True, updates={'cost_items': costs, 'cost_basis': 'User reviewed supplier estimate'})
    assert state['pending_changes'] == {}
    assert state['assessment']['project_outlay'] == sum(costs.values())
    assert state['next']['field'] == 'operating_plan'
    state = answer(client, state, action='use_operating_estimate')
    assert state['next']['field'] == 'financing_choice'


def test_reference_finance_preview_does_not_invent_user_cash(conversation):
    client, _, state = conversation
    state = define_business(client, state)
    finance = state['insights']['finance_preview']
    assert finance['own_funds_known'] is False
    assert finance['personal_contribution'] == finance['capital_structure']['required_promoter_equity']
    assert engine.value(state, 'personal_contribution') is None
    assert engine.value(state, 'cost_items') is None
    assert finance['operating_projection']['basis'] == 'sector_model'
    assert finance['operating_projection']['break_even_period_months'] is None


def test_financial_concerns_require_explicit_acceptance_and_corrections_reset_it(conversation):
    client, _, state = conversation
    state = define_business(client, state, personal_contribution=0, premises='owned')
    state = answer(client, state, action='confirm_estimate')
    state = answer(client, state, text='Monthly sales 5000 and expenses 6000, fixed costs 1000 and variable costs 50%')
    state = answer(client, state, updates={'financing_choice': 'normal'})
    assert state['next']['field'] == 'financial_review'
    assert state['insights']['operating_projection']['monthly_after_debt'] < 0
    assert state['insights']['operating_projection']['break_even_monthly_sales'] == 2000
    assert state['insights']['can_finish'] is False
    assert client.post('/api/v2/onboarding/complete', json={'revision': state['revision']}).status_code == 422
    state = answer(client, state, text='I accept these risks')
    assert state['insights']['financial_risk_accepted'] is True
    assert state['next']['field'] == 'enterprise_name'
    state = answer(client, state, text='My reviewed business')
    assert state['next']['field'] == 'ready' and state['insights']['can_finish']
    state = answer(client, state, correction=True, updates={'monthly_sales': 0})
    assert not state['insights']['financial_risk_accepted']
    assert state['next']['field'] == 'financial_review'
    assert state['insights']['operating_projection']['monthly_sales'] == 0


def test_recommendations_include_finances_compare_and_discuss_without_selecting(conversation):
    client, _, state = conversation
    state = answer(client, state, text='I have no idea and 2 lakh of my own savings')
    state = answer(client, state, text='Open to learning')
    first = state['recommendations'][0]
    assert first['finance_preview']['capital_structure']['required_promoter_equity'] <= 200000
    assert first['finance_preview']['operating_projection']['is_estimate']
    state = answer(client, state, text='compare')
    assert state['comparison_requested'] and engine.value(state, 'idea') is None
    state = answer(client, state, action='recommendation_details', recommendation_id=first['id'])
    assert state['discussed_recommendation_id'] == first['id'] and engine.value(state, 'idea') is None
    state = answer(client, state, text='What is the profit for the first business?')
    assert 'monthly sales' in state['history'][-1]['text']
    assert engine.value(state, 'idea') is None
    previous = {item['id'] for item in state['recommendations']}
    state = answer(client, state, action='alternatives')
    assert not previous.intersection(item['id'] for item in state['recommendations'])


def test_regional_alternatives_reuse_reference_ceiling_without_claiming_own_cash(conversation, monkeypatch):
    client, _, state = conversation
    async def constrained(state):
        return {'recommendation': 'CONSTRAINED_MARKET', 'confidence': 'HIGH', 'evidence': {'top_risk_factors': ['Synthetic power constraint']}}
    monkeypatch.setattr(engine, 'regional_assessment', constrained)
    state = define_business(client, state)
    ceiling = state['cost_proposal']['total']
    state = answer(client, state, action='explore_alternatives')
    assert engine.value(state, 'budget') == ceiling and engine.value(state, 'budget_kind') == 'total'
    assert engine.value(state, 'personal_contribution') is None
    assert 'reference setup cost' in state['alternative_budget_basis']


def test_typed_input_language_is_independent_of_selected_mira_language(conversation, monkeypatch):
    from app.core.translation_service import TranslationService
    inputs = []
    async def translated(self, text, target_language, source_language='en'):
        inputs.append((text, target_language, source_language))
        return {'translated_text': 'I have no business idea and 2 lakh of my own savings', 'provider': 'synthetic_verified_translation'}
    monkeypatch.setattr(TranslationService, 'translate_text', translated)
    client, _, state = conversation
    original = 'मेरे पास अपना व्यवसाय विचार नहीं है और २ लाख की बचत है'
    state = answer(client, state, text=original, language='en')
    assert engine.value(state, 'personal_contribution') == 200000
    assert state['history'][-2]['text'] == original
    assert inputs[0][1:] == ('en', 'auto')


def test_local_money_parser_handles_native_digits_and_zero():
    from app.core.onboarding_understanding import money
    for text in ('२ लाख', '௨ லட்சம்', '౨ లక్షలు', '೨ ಲಕ್ಷ'):
        assert money(text) == 200000
    assert money('०') == 0


def test_latin_script_input_is_also_auto_detected(conversation, monkeypatch):
    from app.core.translation_service import TranslationService
    captured = []
    async def translate(self, text, target_language, source_language='en'):
        captured.append((text, source_language, target_language))
        return {'translated_text': 'I have no idea and 2 lakh of my own savings', 'provider': 'synthetic_translation'}
    monkeypatch.setattr(TranslationService, 'translate_text', translate)
    client, _, state = conversation
    state = answer(client, state, text='No tengo una idea y tengo ahorros para invertir')
    assert engine.value(state, 'personal_contribution') == 200000
    assert captured == [('No tengo una idea y tengo ahorros para invertir', 'auto', 'en')]


def test_generic_regional_category_cannot_turn_into_an_unrelated_named_intent(monkeypatch):
    from app.core.intelligence.engine import MarketOpportunityEngine
    from app.core.intelligence.models import BusinessIntent
    captured = {}
    async def analyze(self, **kwargs):
        captured.update(kwargs)
        return type('Report', (), {'to_dict': lambda self: {'evidence': {}, 'recommendation': 'INSUFFICIENT_DATA'}})()
    monkeypatch.setattr(MarketOpportunityEngine, 'analyze_opportunity', analyze)
    state = {'experience': 'adaptive', 'location': deepcopy(LOC),
        'classification': {'intent_id': 'manufacturing', 'category_id': 'MANUFACTURING', 'label': 'General Manufacturing'},
        'fields': {'idea': {'value': 'Detergent production'}, 'products': {'value': 'detergent'}}}
    asyncio.run(engine.regional_assessment(state))
    assert isinstance(captured['business_intent'], BusinessIntent)
    assert captured['business_intent'].primary_category == 'MANUFACTURING'
    assert captured['business_intent'].intent_id != 'tailoring'
