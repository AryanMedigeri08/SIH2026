"""Dependency-led questions for the audio-first experience.

Only conversation policy and reviewable estimates live here. All project sums,
scheme ranking, normal/SCA servicing and final reports use the existing engines.
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from copy import deepcopy
from app.core import onboarding as base
from app.core.financial_calculator import confirmed_project_outlay, estimate_smart_turnover, calculate_asset_driven_capital_structure
from app.core.machinery_engine import extract_contextual_machinery


def proposal(state):
    reference = equipment_reference(state)
    if reference:
        equipment_cost = sum(item['estimated_cost_inr'] * item.get('quantity', 1) for item in reference['machinery_list'])
        if equipment_cost > 0:
            capital = calculate_asset_driven_capital_structure(equipment_cost, 0,
                promoter_category=base.value(state, 'promoter_category'), gender=base.value(state, 'gender'),
                is_rural=state.get('location', {}).get('is_rural', True))
            total = capital.true_project_outlay
            items = {'equipment': equipment_cost, 'premises_setup': round(total * .15, 2), 'working_capital': round(total * .20, 2)}
            items['other'] = round(total - sum(items.values()), 2)
            total = confirmed_project_outlay(items)
            schedule = {'items': [{'item_name': m['machine_name'], 'total_cost_inr': m['estimated_cost_inr'] * m.get('quantity', 1)} for m in reference['machinery_list']]}
            return {'label': reference['business_name'], 'low': total, 'high': total, 'total': total, 'items': items, 'equipment': schedule,
                'source': 'refactor_equipment_reference_current_goldrush_dpr_model',
                'basis': f"Reference equipment for {reference['business_name']} at {reference.get('typical_capacity', 'supplier-confirmed capacity required')}. "
                    'Not a supplier quote. This is a reference configuration, not a verified match to your requested scale. '
                    'The draft includes equipment, preparing the workspace, initial working funds and other setup costs. Check the actual capacity, local suppliers and running needs before borrowing.'}
    entries = base.catalogue_entries(state)
    entries = [e for e in entries if e['business_category'] == state['classification']['business_category']]
    if not entries:
        return None
    entry = entries[0]
    low, high = entry['typical_project_cost_range']
    # Existing DPR allocation; this is explicitly a starter planning example,
    # not a newly invented vendor quote or a cost derived from the user's cash.
    items = {'equipment': round(low * .55, 2), 'premises_setup': round(low * .15, 2),
        'working_capital': round(low * .20, 2), 'other': round(low * .10, 2)}
    schedule = extract_contextual_machinery(
        base.value(state, 'idea'), state['classification']['business_category'],
        state['classification']['sector'], items['equipment'], use_ai=False)
    return {'label': entry['enterprise_name'], 'low': low, 'high': high,
        'total': confirmed_project_outlay(items), 'items': items,
        'equipment': schedule.to_dict(), 'source': 'existing_sector_catalogue_and_dpr_allocations',
        'basis': f"Indicative starter estimate for {entry['enterprise_name']}; catalogue range ₹{low:,.0f}–₹{high:,.0f}. "
                 'Existing DPR allocations; not a supplier quote or a verified price for the requested capacity. Review equipment, capacity and local quotes before borrowing.'}


def equipment_reference(state):
    if base.value(state, 'activity') in ('retail', 'distribute'):
        return None  # A shop selling milk must not inherit a dairy processing plant.
    data = json.loads((Path(__file__).resolve().parents[1] / 'data' / 'onboarding_equipment_reference.json').read_text(encoding='utf-8'))
    text = (base.value(state, 'idea', '') + ' ' + base.value(state, 'products', '')).lower()
    ranked = []
    for profile in data['businesses']:
        keywords = profile.get('search_keywords', [])
        score = sum(len(keyword.split()) + 1 for keyword in keywords if re.search(r'(?<!\w)' + re.escape(keyword.lower()) + r'(?!\w)', text))
        if score:
            ranked.append((score, profile))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked or (len(ranked) > 1 and ranked[0][0] == ranked[1][0]):
        return None
    return ranked[0][1]


def next_question(state):
    v = lambda key: base.value(state, key)
    q = base.question
    if state.get('paused'):
        return q('paused', 'Your answers are saved. Say resume when you are ready.', action='resume')
    if state['pending_changes']:
        return q('pending_changes', 'I heard a change to your earlier answer. Shall I use the new information?', action='confirm_change')
    for key, text, choices in (
        ('name', 'What is your full name?', ()),
        ('gender', 'How would you describe your gender?', ('Male', 'Female', 'Other', 'Unspecified')),
        ('promoter_category', 'Which social category should I use to check relevant schemes?', ('general', 'sc', 'st', 'obc', 'minority', 'ph', 'artisan', 'women', 'women_shg'))):
        if v(key) is None:
            return q(key, text, choices)
    if v('phone') is None:
        return q('phone', 'What is your ten digit mobile number? Please say each digit.')
    if v('email') is None and v('email_status') != 'skipped':
        return q('email', 'Email is optional. Say your email address, or say skip.')
    loc = state.get('location')
    if not loc:
        return q('location', 'Let’s find your business location. I can use your device location, or you can choose it below.')
    if loc.get('is_rural') is None:
        return q('area_verification', 'I found the place. Its area classification is being checked from official records and village indicators. Some required data is unavailable; retry the data check or choose the correct village below.')
    if not state['location_confirmed']:
        return q('location_confirmation', ('Your device location is approximate. Please check the address carefully. ' if loc.get('approximate') else '') + f"I found {loc['village_name']}, {loc['block_name']}, {loc['district_name']}, {loc['state_name']}. "
            f"The recorded area type is {'rural' if loc['is_rural'] else 'urban or semi-urban'}. Is this where you will run the business?", action='confirm_location')
    if not v('idea') and v('idea_status') != 'explore':
        return q('idea', 'What business do you have in mind? Tell me what you want to make, sell or provide. If you have no idea yet, tell me your budget and I will help you explore.')
    if v('idea_status') == 'explore' and not v('idea'):
        if v('budget') is None:
            return q('budget', 'How much of your own money can you invest as promoter equity? This is your savings, separate from a future loan.')
        if v('budget_kind') not in ('personal', 'total', 'borrowing'):
            return q('budget_kind', 'Is this your own money, the total business budget, or an amount you plan to borrow?', ('personal', 'total', 'borrowing'))
        if not v('skills'):
            return q('skills', 'What work do you know or enjoy, and are there any limits such as space or electricity? You can also say open to learning.')
        return q('recommendations', 'Here are up to three businesses screened against your budget and regional evidence. Choose one to explore, or ask for alternatives.' if state.get('recommendations') else
            'I do not have a supported regional match for that budget and interest yet. Tell me another interest or change the budget; I will check again.')
    if not v('activity'):
        return q('activity', f"For {v('idea')}, will you make products, sell ready-made products, or provide a service?", ('manufacture', 'process', 'retail', 'distribute', 'service'))
    if not v('products'):
        return q('products', 'What exactly will customers buy from you? For example, tell me the product or the repair or other service.')
    if not state.get('classification'):
        return q('products', 'I need to understand the main product or service better. What will customers pay you for?')
    if not v('scale'):
        return q('scale', f"How much {v('products')} would you like to make or sell, or how many customers will you serve in a day or month? If unsure, say start small.")
    if not state['business_confirmed']:
        return q('business_confirmation', f"I understand you want to {v('activity')} {v('products')}, at {v('scale')}. Is that right?", action='confirm_business')
    if not state.get('regional'):
        return q('regional', 'The regional check could not finish. Your answers are saved. Please retry the regional check.', action='answer')
    if state['regional'].get('recommendation') in ('SATURATED_MARKET', 'CONSTRAINED_MARKET', 'NOT_RECOMMENDED', 'RECONSIDER', 'UNSUITABLE') and not state.get('regional_risk_accepted'):
        return q('regional_review', 'The regional evidence raises market or operating concerns for this idea. Would you like to explore other ideas, or continue reviewing this one with those risks?', action='accept_regional_risk')
    odop = state.get('odop')
    if odop and not v('odop_preference'):
        return q('odop_preference', f"Your district ODOP product is {odop['product']}. Shall we explore a useful connection, or keep your idea as it is?", ('explore', 'keep', 'reject'))
    if odop and v('odop_preference') == 'explore' and not state.get('odop_explained'):
        return q('odop_explore', f"The district record lists {odop['product']}. " +
            ('Your sector overlaps, but the actual product and scheme conditions still need checking. ' if odop['aligned'] else 'Your present sector does not match; we can keep your original idea. ') +
            'Describe a real product connection you want to make, or say keep my idea.', ('keep', 'reject'))
    if v('budget') is not None and v('budget_kind') not in ('personal', 'total', 'borrowing', 'other'):
        return q('budget_kind', 'When you say budget, do you mean your own savings, the total setup budget, or borrowing?', ('personal', 'total', 'borrowing'))
    if not v('premises'):
        return q('premises', 'Where will you run this business? Do you own a suitable space, need to rent, or have shared or Panchayat space?', ('owned', 'rented', 'shared', 'mobile'))
    if v('premises') in ('rented', 'shared'):
        if v('rent_amount') is None:
            suggested = state.get('rent_proposal')
            lead = f"For initial planning, the existing rent model gives about ₹{suggested:,.0f} per month. Local rent and the space you need may differ. " if suggested is not None else ''
            return q('rent_amount', lead + 'What rent or shared-space fee should we use? Say the amount per month or year, or confirm the planning estimate below.')
        if not v('rent_period'):
            return q('rent_period', 'Is that rent per month or per year?', ('monthly', 'annual'))
    if not v('cost_items'):
        p = state.get('cost_proposal')
        if p:
            lead = f"For {p['label']}, the reference setup estimate is ₹{p['total']:,.0f}. " if p['low'] == p['high'] else f"The reference setup range for {p['label']} is ₹{p['low']:,.0f}–₹{p['high']:,.0f}; a starter draft is ₹{p['total']:,.0f}. "
            return q('cost_proposal', lead + "This is a planning estimate, not a quote for your exact capacity. Shall we use it or enter your own costs?",
                action='confirm_estimate')
        return q('cost_items', 'This exact business has no supported setup-cost reference yet. What costs do you know for tools or equipment, initial stock, preparing the space and working capital? Enter what applies; we can refine it.')
    if not v('cost_basis'):
        return q('cost_basis', 'Are these supplier estimates, your own estimates or a previous setup cost? What do they cover?')
    if v('personal_contribution') is None:
        return q('personal_contribution', f"The draft setup cost is ₹{v('project_cost'):,.0f}. How much of your own money can you put in? This is separate from the total cost or a loan.")
    if not state.get('assessment'):
        return q('calculation', 'I could not finish the financial check. Check the amounts or retry; your answers are saved.')
    assessment = state['assessment']
    if not v('operating_basis') and not (v('monthly_sales') is not None and v('monthly_expenses') is not None):
        return q('operating_plan', 'What monthly sales and running expenses do you expect? Include materials, wages, utilities and rent in expenses, but not loan EMI. If you do not know yet, use the labelled planning scenario below; we can update it later.', action='use_operating_estimate')
    if not v('financing_choice') or v('financing_choice') == 'increase':
        if v('financing_choice') == 'increase':
            return q('personal_contribution', 'How much can you contribute now? I will recalculate the remaining amount.')
        if assessment['capital_deficit'] == 0:
            return q('financing_choice', 'Your stated own funds cover this draft cost. Would you like to use them, or explore a normal loan?', ('self', 'normal'))
        gap = assessment['capital_deficit']
        margin_gap = assessment['capital_structure']['equity_gap']
        choices = ('increase', 'normal', 'sca') if margin_gap > 0 else ('increase', 'normal')
        return q('financing_choice', f"The setup estimate is ₹{assessment['project_outlay']:,.0f}; your own funds are ₹{assessment['personal_contribution']:,.0f}. "
            f"The remaining funding need is ₹{gap:,.0f}. " +
            (f"There is also a promoter-margin shortfall of ₹{margin_gap:,.0f}; SCA assistance can be explored under the existing eligibility rules. " if margin_gap else '') +
            'Would you increase your contribution or explore financing?', choices)
    from app.core.onboarding_insights import operating_projection, financial_concerns
    concerns = financial_concerns(assessment, operating_projection(state, assessment))
    if concerns and not state.get('financial_risk_accepted'):
        return q('financial_review', 'This plan needs care: ' + ' '.join(concerns) + ' Would you like alternatives within your funds, change this plan, or explicitly accept these concerns and continue?', action='accept_financial_risk')
    if not v('enterprise_name'):
        return q('enterprise_name', 'Your business and funding draft are settled. What name would you like for your enterprise?')
    return q('ready', 'Your draft is ready. Review the details below, correct anything, or ask me to generate your feasibility report.')


async def advance(state):
    v = lambda key: base.value(state, key)
    state['classification'] = base.classify(state)
    if state.get('location') and state['location_confirmed'] and not state['pending_changes'] and not state.get('paused'):
        if state.get('odop') is None:
            state['odop'] = base.verified_odop(state)
        if v('idea_status') == 'explore' and not v('idea') and all(v(k) is not None for k in ('budget', 'budget_kind', 'skills')):
            # No unspecified constraint is invented as a user statement.
            if not state.get('recommendations'):
                candidates = await base.assess_recommendations(state, limit=8)
                supported = []
                for candidate in candidates:
                    if candidate.get('regional_assessment', {}).get('recommendation') in ('SATURATED_MARKET', 'CONSTRAINED_MARKET', 'NOT_RECOMMENDED', 'RECONSIDER', 'UNSUITABLE'):
                        continue
                    entry = next(e for e in base.SECTOR_CATALOG if e['sector_id'] == candidate['id'])
                    projected = deepcopy(state)
                    base.record(projected, 'idea', entry['enterprise_name'], 'existing_catalogue')
                    base.record(projected, 'products', entry['enterprise_name'], 'existing_catalogue')
                    base.record(projected, 'activity', 'manufacture' if entry['business_category'] == 'manufacturing' else 'service', 'existing_catalogue')
                    projected['classification'] = base.classify(projected)
                    p = proposal(projected) if projected['classification'] else None
                    outlay = p['total'] if p else candidate['outlay_range'][0]
                    kind, budget = v('budget_kind'), v('budget')
                    if kind == 'total' and outlay > budget:
                        continue
                    if kind == 'borrowing' and max(outlay - (v('personal_contribution') or 0), 0) > budget:
                        continue
                    if kind == 'personal':
                        capital = calculate_asset_driven_capital_structure(0, budget,
                            promoter_category=v('promoter_category'), gender=v('gender'), confirmed_project_cost=outlay)
                        if capital.required_promoter_equity > budget:
                            continue
                    if p:
                        candidate['outlay_range'] = [outlay, outlay]
                        candidate['market_evidence'] += ' Equipment costs are reference estimates and require capacity and supplier checks.'
                    from app.core.onboarding_insights import finance_preview
                    candidate['finance_preview'] = finance_preview(projected, p)
                    candidate['odop'] = base.verified_odop(projected)
                    candidate['requirements'] = p['basis'] if p else 'Equipment, premises, supplier quotations and local operating costs need confirmation.'
                    candidate['provisional'] = candidate.get('confidence') not in ('HIGH', 'MEDIUM')
                    supported.append(candidate)
                supported.sort(key=lambda item: ((item.get('regional_assessment') or {}).get('evidence', {}).get('composite_score', 0), item.get('score', 0)), reverse=True)
                state['recommendations'] = supported[:3]
        c = state.get('classification')
        if c and state['business_confirmed'] and state.get('regional') is None:
            try:
                state['regional'] = await asyncio.wait_for(base.regional_assessment(state), 30)
                region = state['regional']
                confidence = region.get('confidence') or region.get('evidence', {}).get('confidence') or 'INSUFFICIENT_DATA'
                summary = region.get('evidence', {}).get('plain_language_summary') or 'The available data does not establish suitability with confidence.'
                state['regional_announcement'] = f"Regional check: {region.get('recommendation') or 'INSUFFICIENT_DATA'}; confidence {confidence}. {summary}"
            except Exception:
                state['regional'] = None
        if c and state['business_confirmed'] and state.get('regional'):
            if state.get('cost_proposal') is None:
                state['cost_proposal'] = proposal(state)
            p = state.get('cost_proposal')
            if p:
                state['estimate'] = {'label': p['label'], 'low': p['low'], 'high': p['high'], 'source': p['source'], 'is_estimate': True}
                state['rent_proposal'] = estimate_smart_turnover(p['total'], c['sector'], premise_type='rented').monthly_rent_deducted
            rent_ready = v('premises') not in ('rented', 'shared') or (v('rent_amount') is not None and v('rent_period') is not None)
            if all(v(key) is not None for key in ('cost_items', 'project_cost', 'cost_basis', 'personal_contribution', 'premises')) and rent_ready and not state.get('assessment'):
                try:
                    state['assessment'] = base.financial_assessment(state)
                except Exception:
                    state['assessment'] = None
    state['next'] = next_question(state)
    if state['next']['field'] == 'odop_preference':
        state['odop_offered'] = True
    state['missing_information'] = [] if state['next']['field'] == 'ready' else [state['next']['field']]
    state['unresolved_ambiguities'] = list(state['pending_changes'])
    return state
