"""Business demand semantics, scenario uncertainty and preservation of existing finances."""
import copy
import json
from types import SimpleNamespace

import pytest

from backend.app.core.demand_forecast import DemandForecast, DemandInput, validate_forecast, demand_metrics, reconcile_forecast, forecast_payload
from backend.app.core.enterprise_assumptions import estimate_operations, calculate_operations
from backend.app.core.llm_financials import calculate_report_finance
from backend.app.core.demand_report import demand_html, demand_markdown
from tests.planning_fixtures import business_demand_fixture
from tests.test_average_selling_price import weighted_package, run


UNITS = {'active_buyers':'people', 'reachable_prospects':'organizations', 'conversion_rate':'fraction',
    'transactions_per_buyer':'transactions/buyer/month', 'units_per_transaction':'output_units/transaction',
    'qualified_traffic':'website_users/month', 'repeat_transactions':'transactions/month',
    'starting_subscribers':'subscribers', 'new_subscribers':'subscribers/month', 'churned_subscribers':'subscribers/month',
    'units_per_subscriber':'output_units/subscriber/month', 'available_inventory':'inventory_units',
    'occupancy':'fraction', 'billing_units_per_inventory':'output_units/inventory/month',
    'category_monthly_units':'output_units/month', 'market_share':'fraction', 'seasonality':'factor'}


def inp(role, value, **updates):
    return dict(role=role, value=value, units=UNITS[role], reference_period='snapshot' if role == 'starting_subscribers' else 'annual_average_month',
        source_kind='scenario_assumption', source='Explicit synthetic planning assumption; no benchmark fetched',
        evidence_path=None, confidence='low', reasoning='Synthetic driver definition with a distinct buyer group and monthly reference period.', **updates)


CASES = [
    ('customer_purchases', 'people', [('active_buyers',100),('transactions_per_buyer',2),('units_per_transaction',3)], [(420,70,140),(600,100,200),(780,130,260)]),
    ('service_bookings', 'people', [('active_buyers',20),('transactions_per_buyer',1.5),('units_per_transaction',1)], [(21,14,21),(30,20,30),(39,26,39)]),
    ('b2b_orders', 'organizations', [('reachable_prospects',20),('conversion_rate',.25),('transactions_per_buyer',2),('units_per_transaction',40)], [(280,3.5,7),(400,5,10),(520,6.5,13)]),
    ('manufacturing_orders', 'organizations', [('reachable_prospects',30),('conversion_rate',.2),('transactions_per_buyer',1),('units_per_transaction',100)], [(420,4.2,4.2),(600,6,6),(780,7.8,7.8)]),
    ('ecommerce', 'website_users', [('qualified_traffic',1000),('conversion_rate',.02),('repeat_transactions',10),('units_per_transaction',2)], [(48,None,24),(60,None,30),(72,None,36)]),
    ('subscription', 'subscribers', [('starting_subscribers',100),('new_subscribers',20),('churned_subscribers',5),('units_per_subscriber',1)], [(85,85,85),(115,115,115),(145,145,145)]),
    ('occupancy', 'inventory_units', [('available_inventory',10),('occupancy',.6),('billing_units_per_inventory',30)], [(126,None,None),(180,None,None),(234,None,None)]),
    ('market_share', 'people', [('category_monthly_units',10000),('market_share',.02)], [(140,None,None),(200,None,None),(260,None,None)]),
]


def forecast(case=CASES[0]):
    method, buyer, drivers, expected = case
    f = business_demand_fixture({'product':'Synthetic business', 'output_unit':'units', 'selling_price_inr':50},
        {'monthly_local_demand_units':600, 'monthly_saleable_capacity':500})
    f.update(method=method, buyer_base=buyer)
    for n, name in enumerate(('conservative','base','optimistic')):
        demand, buyers, transactions = expected[n]
        inputs = [inp(role, value*(.7,1,1.3)[n] if index == 0 else value) for index,(role,value) in enumerate(drivers)]
        sold = min(demand,500)
        f['scenarios'][name] = dict(inputs=inputs, monthly_demand_units=demand, monthly_active_buyers=buyers,
            monthly_transactions=transactions, realized_monthly_units=sold, daily_unit_sales=sold/25,
            monthly_revenue_inr=sold*50, capacity_utilization_pct=sold/500*100)
    return f


def validate(f, context=None):
    return validate_forecast(DemandForecast.model_validate(f), SimpleNamespace(output_unit='units', selling_price_inr=50),
        SimpleNamespace(working_days_per_month=25), 500, context or {})


@pytest.mark.parametrize('case', CASES, ids=[case[0] for case in CASES])
def test_industry_specific_methods_use_correct_units_and_buyer_definitions(case):
    f = forecast(case)
    validate(f)
    assert f['scenarios']['base']['monthly_demand_units'] == case[3][1][0]
    assert f['scenarios']['base']['realized_monthly_units'] <= 500


@pytest.mark.parametrize('extra', ['conversion_rate', 'market_share', 'seasonality'])
def test_already_captured_buyers_cannot_receive_extra_capture_or_seasonal_reductions(extra):
    f = forecast()
    for s in f['scenarios'].values():
        s['inputs'].append(inp(extra,.5))
    with pytest.raises(ValueError, match='Overlapping|seasonality'):
        validate(f)


def test_b2b_cannot_silently_use_households_as_organizations():
    f = forecast(CASES[2])
    f['buyer_base'] = 'households'
    for s in f['scenarios'].values():
        s['inputs'][0]['units'] = 'households'
    with pytest.raises(ValueError, match='organizations or contracts'):
        validate(f)


def test_monthly_purchase_frequency_cannot_be_an_annual_rate():
    f = forecast()
    f['scenarios']['base']['inputs'][1]['units'] = 'transactions/buyer/year'
    with pytest.raises(ValueError, match='monthly|transactions/buyer/month'):
        validate(f)


def test_equivalent_sold_unit_labels_are_validated_without_unit_scaling():
    f = forecast()
    for scenario in f['scenarios'].values():
        scenario['inputs'][1]['units'] = 'purchases per customer per month'
        scenario['inputs'][2]['units'] = 'units per purchase'
    validate(f)
    f['scenarios']['base']['inputs'][2]['units'] = 'kg per purchase'
    with pytest.raises(ValueError,match='Basket size'):
        validate(f)


def test_monthly_customer_counts_can_use_explicit_buyer_per_month_units():
    f = forecast()
    for scenario in f['scenarios'].values():
        scenario['inputs'][0]['units'] = 'buyers/month'
    validate(f)


def test_an_intermediate_active_count_is_checked_but_not_multiplied_again():
    f = forecast()
    for scenario in f['scenarios'].values():
        count = scenario['inputs'][0]['value']
        prospects = inp('reachable_prospects',count*10)
        prospects['units'] = 'people'
        scenario['inputs'] += [prospects,inp('conversion_rate',.1)]
    validate(f)
    assert f['scenarios']['base']['monthly_demand_units']==600
    f['scenarios']['base']['inputs'][-1]['value'] = .2
    with pytest.raises(ValueError,match='active_buyers derivation'):
        validate(f)


def test_monthly_active_buyers_are_not_an_inactive_customer_pool():
    f = forecast()
    f['scenarios']['base']['inputs'][1]['value'] = .35
    with pytest.raises(ValueError,match='Monthly active buyers'):
        validate(f)


def test_census_population_cannot_be_cited_as_observed_business_customers():
    inputs = [DemandInput.model_validate(inp(role,value)) for role,value in [('active_buyers',100),('transactions_per_buyer',2),('units_per_transaction',3)]]
    inputs[0].source_kind = 'verified_local_data'
    inputs[0].evidence_path = 'evidence.households'
    with pytest.raises(ValueError,match='Demographic counts'):
        demand_metrics('customer_purchases',inputs,'people','annual_average_month',{'households':100})


def test_households_are_not_automatically_the_right_buyers_for_consumer_products():
    f = forecast()
    f['buyer_base'] = 'households'
    for s in f['scenarios'].values():
        s['inputs'][0]['units'] = 'households'
    assert any('household decisions or individual visits' in warning for warning in validate(f))


def test_model_cannot_invent_external_benchmark_citations():
    f = forecast()
    f['scenarios']['base']['inputs'][0]['source'] = 'Claimed market benchmark at https://invented.invalid/market-study'
    with pytest.raises(ValueError,match='invent a benchmark'):
        validate(f)


def test_invalid_provider_evidence_is_a_low_confidence_hypothesis_without_changing_numbers():
    f = forecast()
    for scenario in f['scenarios'].values():
        scenario['inputs'][0].update(source_kind='actual_records', source='Claimed but unavailable benchmark', evidence_path=None, confidence='high')
    old = copy.deepcopy(f)
    fixed = reconcile_forecast(DemandForecast.model_validate(f), SimpleNamespace(output_unit='units',selling_price_inr=50),
        SimpleNamespace(working_days_per_month=25),500,{})
    payload = forecast_payload(fixed, [], False)
    assert payload['review_status']=='review_required'
    for name in ('conservative','base','optimistic'):
        current = payload['scenarios'][name]['inputs'][0]
        assert current['value']==old['scenarios'][name]['inputs'][0]['value']
        assert current['source_kind']=='scenario_assumption'
        assert current['confidence']=='low'
        assert current['evidence_path'] is None
    assert payload['warnings']
    assert payload['provisional']


def test_verified_claim_requires_supplied_numeric_evidence_and_exact_value():
    inputs = [DemandInput.model_validate(inp(role,value)) for role,value in [('active_buyers',100),('transactions_per_buyer',2),('units_per_transaction',3)]]
    inputs[0].source_kind = 'actual_records'
    with pytest.raises(ValueError, match='evidence'):
        demand_metrics('customer_purchases', inputs, 'people', 'annual_average_month', {})
    inputs[0].evidence_path = 'evidence.observed_monthly_customers'
    assert demand_metrics('customer_purchases', inputs, 'people', 'annual_average_month', {'observed_monthly_customers':100}) == (600,100,200)
    with pytest.raises(ValueError, match='evidence value'):
        demand_metrics('customer_purchases', inputs, 'people', 'annual_average_month', {'observed_monthly_customers':50})


@pytest.mark.parametrize('mistake', ['wrong_money','wrong_unit','point_only','hidden_uncertainty','reversed_scenarios','incompatible_roles'])
def test_forecast_does_not_hide_uncertainty_or_accept_inconsistent_outputs(mistake):
    f = forecast()
    if mistake == 'wrong_money':
        f['scenarios']['base']['monthly_revenue_inr'] += 1000
    elif mistake == 'wrong_unit':
        f['output_unit'] = 'kg'
    elif mistake == 'point_only':
        f['scenarios']['conservative'] = copy.deepcopy(f['scenarios']['base'])
        f['scenarios']['optimistic'] = copy.deepcopy(f['scenarios']['base'])
    elif mistake == 'hidden_uncertainty':
        f['provisional'] = False
    elif mistake == 'reversed_scenarios':
        f['scenarios']['conservative'], f['scenarios']['optimistic'] = f['scenarios']['optimistic'], f['scenarios']['conservative']
    else:
        f['scenarios']['base']['inputs'].append(inp('market_share', .1))
    with pytest.raises(ValueError):
        validate(f)


def test_reality_review_flags_extremes_without_manufacturing_sales():
    f = forecast()
    for s in f['scenarios'].values():
        for key in ('monthly_demand_units','monthly_active_buyers','monthly_transactions','realized_monthly_units','daily_unit_sales','monthly_revenue_inr','capacity_utilization_pct'):
            s[key] /= 1000
        s['inputs'][0]['value'] /= 1000
        # Original base demand was capacity-limited; restore demand-limited metrics.
        s['realized_monthly_units'] = s['monthly_demand_units']
        s['daily_unit_sales'] = s['realized_monthly_units']/25
        s['monthly_revenue_inr'] = s['realized_monthly_units']*50
        s['capacity_utilization_pct'] = s['realized_monthly_units']/500*100
    before = copy.deepcopy(f)
    flags = validate(f, {'households':3804})
    assert any('one sold unit' in flag for flag in flags)
    assert any('1%' in flag for flag in flags)
    assert f == before


def test_demand_repair_preserves_price_recipe_capacity_and_costs():
    good = weighted_package()
    bad = copy.deepcopy(good)
    bad['demand_forecast']['scenarios']['base']['monthly_demand_units'] = 2
    calls = []
    def llm(**kwargs):
        calls.append(kwargs)
        return json.dumps(bad if len(calls)==1 else good), None, 'test'
    a = estimate_operations({'idea':'Ice cream in 100 ml cups','households':4000,'sector':'dairy'}, llm)
    result = calculate_operations(a)
    assert len(calls)==2
    assert result['calculation_source']=='llm_calculated'
    assert result['monthly_sales_units']==1000
    assert a['values']==good['values']
    assert a['capacity']['monthly_quantity']==good['capacity']['monthly_quantity']
    assert a['pricing']['sales_mix']==good['pricing']['sales_mix']


def test_same_base_sales_leave_existing_prices_costs_funding_and_dscr_unchanged():
    response = weighted_package()
    modern = run(response)
    legacy = calculate_operations({'values':response['values'], 'capacity':response['capacity'],
        'conversion':response['conversion'], 'pricing':response['pricing'], 'evidence':{'households':4000},
        'source_summary':'Synthetic legacy fixture','calculation_source':'indicative_calculation_fallback'})
    for key in ('monthly_sales_units','selling_price_inr','annual_sales','annual_variable_cost','annual_fixed_cost','monthly_saleable_capacity'):
        assert modern[key]==pytest.approx(legacy[key], abs=1e-9)
    facts = dict(project_cost=500000,loan_principal=300000,annual_rate_pct=11,tenure_years=7,moratorium_months=6,
        sector='dairy',cpi_pct=5,subsidy_amount=0,promoter_margin=200000)
    old, new = [calculate_report_finance(ops,facts)['result'] for ops in (legacy,modern)]
    assert old.amortization==new.amortization
    assert old.projections==new.projections
    assert old.dscr==new.dscr


def test_forecast_exports_show_evidence_scenarios_and_escape_untrusted_text():
    f = forecast()
    f['target_customer'] = '<script>bad()</script>'
    html, md = demand_html(f), demand_markdown(f)
    for content in (html,md):
        assert 'Business-specific demand forecast' in content
        assert 'conservative' in content and 'optimistic' in content
        assert 'hypotheses, not verified sales' in content
        assert 'Confidence' in content and 'Justification' in content
        assert '<script>' not in content


@pytest.mark.parametrize('acknowledge_review', [False,True])
def test_eight_units_from_large_catchment_get_reexamined_without_an_artificial_floor(acknowledge_review):
    response = weighted_package()
    c, v = response['calculations'], response['values']
    c.update(monthly_sales_units=8, monthly_local_demand_units=8, monthly_gross_sales=208,
        annual_sales=2496, annual_variable_cost=264, annual_operating_cashflow=1032,
        unit_cost_floor=15.25)
    response['demand_forecast'] = business_demand_fixture(v,c)
    response['demand_forecast'].update(reality_reexamined=False, warnings=[])
    calls = []
    def llm(**kwargs):
        calls.append(kwargs)
        result = copy.deepcopy(response)
        if len(calls)>1:
            assert 'BUSINESS REALITY RE-EXAMINATION' in kwargs['messages'][-1]['content']
            if acknowledge_review:
                result['demand_forecast'].update(reality_reexamined=True,
                    warnings=['A limited pilot acquires only eight initial monthly buyers; category demand is not being treated as captured sales.'],
                    reality_review='Re-examined the buyer count and daily volume. This synthetic limited pilot has eight expected customers and no established distribution; retain a broad provisional range and review market acquisition before scaling.')
        return json.dumps(result), None, 'test'
    a = estimate_operations({'idea':'Ice cream in 100 ml cups','households':3804,'sector':'dairy'},llm)
    ops = calculate_operations(a)
    assert len(calls)==2
    assert ops['monthly_sales_units']==8
    assert ops['selling_price_inr']==26
    assert a['values']['raw_material_cost_per_input_unit_inr']==v['raw_material_cost_per_input_unit_inr']
    assert a['demand_forecast']['review_status']==('reexamined' if acknowledge_review else 'review_required')
    assert a['demand_forecast']['provisional']
    assert a['demand_forecast']['warnings']


def test_focused_demand_recovery_cannot_change_the_accepted_economics():
    good = weighted_package()
    bad = copy.deepcopy(good)
    for scenario in bad['demand_forecast']['scenarios'].values():
        scenario['inputs'].append(inp('market_share', .045))
    calls = []
    def llm(**kwargs):
        calls.append(kwargs)
        if kwargs['response_format']['json_schema']['name'] == 'business_demand':
            data = json.loads(kwargs['messages'][1]['content'])
            assert data['accepted_facts']['selling_price_inr']==26
            assert data['accepted_facts']['output_unit']=='cups'
            assert 'promoter_equity' not in data['evidence']
            assert 'project_cost' not in data['evidence']
            return json.dumps(good['demand_forecast']), None, 'demand-repair-test'
        return json.dumps(bad), None, 'operating-test'
    a = estimate_operations({'idea':'Ice cream in 100 ml cups','sector':'dairy','households':4000,
        'project_cost':500000,'promoter_equity':100000},llm)
    result = calculate_operations(a)
    assert len(calls)==3
    assert result['monthly_sales_units']==1000
    assert a['values']==good['values']
    assert a['pricing']['sales_mix']==good['pricing']['sales_mix']
    assert a['capacity']['monthly_quantity']==good['capacity']['monthly_quantity']
    assert a['demand_forecast']['model']=='demand-repair-test'
    assert result['calculation_source']=='indicative_calculation_fallback'


def test_a_peak_month_cannot_silently_be_annualized_as_a_full_year():
    good = weighted_package()
    bad = copy.deepcopy(good)
    bad['demand_forecast']['period'] = 'forecast_month'
    bad['demand_forecast']['forecast_month'] = '2026-05'
    calls = []
    def llm(**kwargs):
        calls.append(kwargs)
        return json.dumps(bad if len(calls)==1 else good), None, 'test'
    a = estimate_operations({'idea':'Ice cream in 100 ml cups','sector':'dairy','households':4000},llm)
    assert len(calls)==2
    assert a['demand_forecast']['period']=='annual_average_month'
    assert calculate_operations(a)['annual_sales']==312000


@pytest.mark.parametrize('missing', [True,False])
def test_invalid_new_demand_metadata_does_not_discard_valid_production_or_prices(missing):
    good = weighted_package()
    bad = copy.deepcopy(good)
    if missing:
        bad.pop('demand_forecast')
    else:
        bad['demand_forecast'] = {'method':'unsupported'}
    def llm(**kwargs):
        if kwargs['response_format']['json_schema']['name']=='business_demand':
            return json.dumps(good['demand_forecast']),None,'demand-test'
        return json.dumps(bad),None,'operating-test'
    a = estimate_operations({'idea':'Ice cream in 100 ml cups','sector':'dairy','households':4000},llm)
    ops = calculate_operations(a)
    assert a['values']==good['values']
    assert a['capacity']['monthly_quantity']==2500
    assert a['conversion']['saleable_unit_quantity']==.1
    assert ops['selling_price_inr']==26
    assert ops['monthly_sales_units']==1000
    assert ops['annual_sales']==312000
    assert a['demand_forecast']['model']=='demand-test'
