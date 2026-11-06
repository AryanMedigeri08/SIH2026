"""Chat-ready views of existing calculations and observed regional evidence.

Planning projections are never evidence of real demand. No loan terms or
financial-calculator formulas are replaced here.
"""
from copy import deepcopy
from app.core import onboarding as base
from app.core.financial_calculator import estimate_smart_turnover, calculate_asset_driven_capital_structure

ADVERSE = {'SATURATED_MARKET', 'CONSTRAINED_MARKET', 'NOT_RECOMMENDED', 'RECONSIDER', 'UNSUITABLE'}


def operating_projection(state, finance):
    v = lambda key, default=None: base.value(state, key, default)
    loan = finance['normal_loan']
    model = estimate_smart_turnover(finance['project_outlay'], state['classification']['sector'],
        loan_principal=loan['amount'], annual_rate_pct=loan['rate_pct'], tenure_years=loan['tenure_years'],
        moratorium_months=loan['moratorium_months'], premise_type=v('premises', 'rented'),
        monthly_rent=finance['monthly_rent'] if v('premises') else None)
    has_sales, has_expenses = v('monthly_sales') is not None, v('monthly_expenses') is not None
    sales = v('monthly_sales') if has_sales else model.monthly_gross_sales
    # User expenses include rent, wages, materials and utilities, but exclude loan EMI.
    expenses = v('monthly_expenses') if has_expenses else sales * (1 - model.operating_margin_pct / 100) + model.monthly_rent_deducted
    surplus = sales - expenses
    financing = v('financing_choice', 'normal')
    debt = finance['capital_structure']['total_monthly_debt_service'] if financing == 'sca' else 0 if financing == 'self' else loan['monthly_emi']
    after_debt = surplus - debt
    fixed, variable = v('monthly_fixed_costs'), v('variable_cost_pct')
    break_even = fixed / (1 - variable / 100) if fixed is not None and variable is not None and variable < 100 else None
    return {'basis': 'user_estimate' if has_sales and has_expenses else 'mixed_estimate' if has_sales or has_expenses else 'sector_model', 'is_estimate': True,
        'monthly_sales': round(sales, 2), 'monthly_expenses': round(expenses, 2),
        'monthly_operating_surplus': round(surplus, 2), 'monthly_emi': debt, 'debt_basis': financing,
        'monthly_after_debt': round(after_debt, 2), 'operating_margin_pct': round(surplus / sales * 100, 2) if sales else None,
        'simple_project_payback_months': round(finance['project_outlay'] / surplus, 1) if surplus > 0 else None,
        'break_even_monthly_sales': round(break_even, 2) if break_even is not None else None,
        'break_even_period_months': None,
        'missing_details': ([] if has_sales else ['Expected monthly customer sales']) + ([] if has_expenses else ['Monthly materials, wages, utilities and rent']) +
            ([] if break_even is not None else ['Fixed monthly expenses and variable cost percentage for a break-even sales calculation']) +
            ['Monthly sales ramp-up for a break-even date', 'Local customer orders and supplier quotations'],
        'notice': 'Planning scenario, not a verified profit forecast. The existing sector model sizes sales from capital and debt-service assumptions; it does not establish customer demand. Simple project payback is not the operating break-even date.'}


def finance_preview(state, cost_proposal):
    if not cost_proposal or not state.get('classification') or not state.get('location'):
        return None
    projected = deepcopy(state)
    outlay = cost_proposal['total']
    own = base.value(state, 'personal_contribution')
    required = calculate_asset_driven_capital_structure(0, own or 0,
        promoter_category=base.value(state, 'promoter_category'), gender=base.value(state, 'gender'),
        is_rural=state['location']['is_rural'], confirmed_project_cost=outlay).required_promoter_equity
    # Missing cash is an explicit scenario assumption; never persist it as the user's funds.
    base.record(projected, 'project_cost', outlay, 'planning_preview')
    base.record(projected, 'personal_contribution', own if own is not None else required, 'planning_preview')
    base.record(projected, 'cost_items', cost_proposal['items'], 'planning_preview')
    result = base.financial_assessment(projected)
    result['own_funds_known'] = own is not None
    result['operating_projection'] = operating_projection(projected, result)
    return result


def financial_concerns(finance, projection):
    if not finance:
        return []
    reasons = []
    if finance['capital_structure']['equity_gap'] > 0:
        reasons.append('Your own funds are below the required promoter margin. Review increasing funds or the existing SCA assistance option.')
    if finance.get('budget_kind') == 'total' and (finance.get('budget_shortfall') or 0) > 0:
        reasons.append('The setup estimate exceeds your stated total project budget.')
    if finance.get('budget_kind') == 'borrowing' and (finance.get('budget_shortfall') or 0) > 0:
        reasons.append('The funding gap exceeds the borrowing amount you stated.')
    if projection and projection['monthly_after_debt'] <= 0:
        reasons.append('The planning scenario leaves no positive monthly cash after expenses and the selected loan repayments.')
    return reasons


def insights(state):
    finance = state.get('assessment')
    preview = finance_preview(state, state.get('cost_proposal')) if not finance else None
    projection = operating_projection(state, finance) if finance else (preview or {}).get('operating_projection')
    regional = state.get('regional') or {}
    reasons = financial_concerns(finance, projection)
    return {'finance_preview': preview, 'operating_projection': projection, 'financial_concerns': reasons,
        'regional_risk_accepted': bool(state.get('regional_risk_accepted')),
        'financial_risk_accepted': bool(state.get('financial_risk_accepted')),
        'regional_status': regional.get('recommendation', 'PENDING'),
        'can_finish': state.get('next', {}).get('field') in ('ready', 'complete') and bool(state.get('business_confirmed')),
        'estimate_notice': 'Numbers are planning estimates using existing calculators. Unknown local demand, resources or competition remain unknown.'}
