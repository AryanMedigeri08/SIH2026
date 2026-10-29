import copy
import asyncio
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.sales_catalogue import candidates, catalogue, monthly_input_capacity
from app.core.sales_forecast import ForecastPlan, build_payload, calculate_forecast, generate_sales_forecast


def source(unit, **kw):
    return dict(unit=unit, source_kind="scenario_assumption", evidence_ref=None,
                confidence="low", reasoning="Illustrative hypothesis for synthetic tests, not market research.", **kw)


def assumption(value, unit):
    return dict(value=value, **source(unit))


def user(**kw):
    data = dict(enterprise_name="Fresh milk dairy processing", additional_business_details="Milk retail and delivery",
                sector="dairy", state_name="Karnataka", district_name="Test", block_name="Test", village_name="Test",
                project_cost=2_000_000, annual_turnover_estimate=900_000, sales_context={}, forecast_start_month=None)
    return SimpleNamespace(**(data | kw))


def plan_dict():
    return dict(business_classification="Milk retail delivery B2C", operating_days=[25] * 12,
                hours_per_day=assumption(8, "hours/day"), availability=assumption(.8, "fraction"),
                non_machinery_budget_inr=assumption(300_000, "INR"), limitations=["Synthetic customer acquisition assumptions."],
                products=[dict(product_id="milk-retail", name="Milk", channel="delivery", unit="litre",
                    method="customer_purchases", method_reason="Repeat milk purchases by subscribing households.",
                    buyer_definition="Monthly active purchasing households, already captured by this enterprise.",
                    profile_id=None, output_per_input=assumption(1, "litre/litre"),
                    independent_capacity_per_month=[1500] * 12, capacity_basis=source("litre/month"),
                    assumptions={"active_buyers": source("buyers/month"),
                        "transactions_per_buyer": source("transactions/buyer/month"),
                        "units_per_transaction": source("litre/transaction"), "selling_price": source("INR/litre")},
                    scenarios={s: dict(drivers={"active_buyers": [n] * 12,
                        "transactions_per_buyer": [25] * 12, "units_per_transaction": [1] * 12},
                        selling_prices=[price] * 12)
                        for s, n, price in [("conservative", 20, 50), ("base", 40, 60), ("optimistic", 80, 65)]})])


def payload():
    return build_payload(user(), {"amenities": {"provenance": "regional_baseline"},
                                 "demographics": {"status": "projected", "population": 5000}})


def test_twelve_month_revenue_and_capacity_arithmetic():
    result = calculate_forecast(ForecastPlan(**plan_dict()), payload())
    assert result["annual_sales"] == {"conservative": 300000, "base": 720000, "optimistic": 1170000}
    assert result["monthly_scenarios"]["optimistic"][0]["products"][0]["units_sold"] == 1500
    assert result["input_hash"]
    assert result["status"] == "provisional"


def test_startup_months_are_summed_not_final_month_times_twelve():
    raw = plan_dict()
    for scenario in raw["products"][0]["scenarios"].values():
        scenario["drivers"]["active_buyers"] = list(range(1, 13))
    result = calculate_forecast(ForecastPlan(**raw), payload())
    assert result["annual_sales"]["base"] == sum(range(1, 13)) * 25 * 60
    assert result["annual_sales"]["base"] != 12 * 25 * 60 * 12


@pytest.mark.parametrize("mutate", [
    lambda d: d["products"][0]["scenarios"]["base"]["drivers"].update(market_share=[.1]*12),
    lambda d: d["products"][0]["scenarios"]["base"].update(selling_prices=[60]*11),
    lambda d: d["products"][0]["scenarios"]["base"]["drivers"]["active_buyers"].__setitem__(0, float("nan")),
    lambda d: d["products"][0]["assumptions"]["transactions_per_buyer"].update(unit="transactions/year"),
    lambda d: d["products"][0]["output_per_input"].update(value=0),
])
def test_invalid_equations_and_values_rejected(mutate):
    raw = plan_dict(); mutate(raw)
    with pytest.raises(ValidationError):
        ForecastPlan(**raw)


def test_context_does_not_become_verified_sales():
    raw = plan_dict()
    src = raw["products"][0]["assumptions"]["active_buyers"]
    src.update(source_kind="supplied_evidence", evidence_ref="evidence.demographics", confidence="high")
    result = calculate_forecast(ForecastPlan(**raw), payload())
    saved = result["accepted_plan"]["products"][0]["assumptions"]["active_buyers"]
    assert saved["source_kind"] == "scenario_assumption" and saved["confidence"] == "low"
    assert any("does not verify" in warning for warning in result["warnings"])


def test_fabricated_evidence_reference_is_discarded_and_never_shown_as_fact():
    raw = plan_dict()
    raw["products"][0]["assumptions"]["selling_price"].update(
        source_kind="supplied_evidence", evidence_ref="evidence.nonexistent_market_survey")
    result = calculate_forecast(ForecastPlan(**raw), payload())
    source_meta = result["accepted_plan"]["products"][0]["assumptions"]["selling_price"]
    assert source_meta["source_kind"] == "scenario_assumption"
    assert source_meta["evidence_ref"] is None and source_meta["confidence"] == "low"
    assert "discarded" in source_meta["reasoning"]


def test_payload_excludes_targets_and_personal_identifiers():
    p = payload()
    assert "annual_turnover_estimate" not in p["business"]
    assert "monthly_emi" not in p and "dscr" not in p
    assert "promoter_name" not in p["business"]
    assert p["machinery_options"] and p["catalogue_version"]


def test_catalogue_restored_and_tonne_conversion_consistent():
    rows, version = catalogue()
    assert len(rows) == 37 and len(version) == 64
    variant = {"capacity": dict(quantity=2, unit="tonnes", period="hour", capacity_kind="throughput")}
    assert monthly_input_capacity(variant, 25, 8, 1) == 400000
    variant["capacity"]["quantity"] = 3
    assert monthly_input_capacity(variant, 25, 8, 1) == 600000


def test_storage_is_stock_days_not_monthly_production():
    v = {"capacity": dict(quantity=10, unit="tonnes", period="stock", capacity_kind="storage")}
    assert monthly_input_capacity(v, 25, 8, 1) == 250000


def test_shared_equipment_is_not_double_allocated_and_chooses_smallest():
    p = payload()
    row = next(x for x in p["machinery_options"] if "Dairy Processing" in x["business_name"])
    raw = plan_dict()
    for _ in range(1):
        second = copy.deepcopy(raw["products"][0]); second["product_id"] = "milk-wholesale"; second["channel"] = "shops"
        raw["products"].append(second)
    for prod in raw["products"]:
        prod["profile_id"] = row["profile_id"]
        prod["independent_capacity_per_month"] = [1e7] * 12
        for scenario in prod["scenarios"].values():
            scenario["drivers"]["active_buyers"] = [200] * 12
    result = calculate_forecast(ForecastPlan(**raw), p)
    assert len(result["selected_equipment"]) == 1
    equipment = result["selected_equipment"][0]
    for month in result["monthly_scenarios"]["base"]:
        assert sum(x["units_sold"] for x in month["products"]) <= equipment["monthly_input_capacity"][0] + 1e-6


def test_unaffordable_equipment_means_zero_production_not_fabricated_capacity():
    p = payload(); p["user_constraints"]["project_budget_inr"] = 310000
    row = p["machinery_options"][0]
    raw = plan_dict(); raw["products"][0]["profile_id"] = row["profile_id"]
    cap_unit = row["capacity_reference"]["unit"]
    assert cap_unit == "litres"
    result = calculate_forecast(ForecastPlan(**raw), p)
    assert result["annual_sales"]["base"] == 0
    assert not result["selected_equipment"]


@pytest.mark.parametrize("key,value", [("unit", "kg"), ("output_per_input", assumption(1, "litre/tonnes"))])
def test_price_or_conversion_unit_mismatch_rejected(key, value):
    p = payload(); raw = plan_dict()
    raw["products"][0]["profile_id"] = p["machinery_options"][0]["profile_id"]
    raw["products"][0][key] = value
    with pytest.raises(ValueError):
        calculate_forecast(ForecastPlan(**raw), p)


def test_calendar_days_validation():
    p = payload(); p["forecast_start_month"] = "2027-02-01"
    raw = plan_dict(); raw["operating_days"][0] = 30
    with pytest.raises(ValueError, match="calendar"):
        calculate_forecast(ForecastPlan(**raw), p)


def test_provider_failure_preserves_manual_estimate_without_false_validation(monkeypatch):
    async def unavailable(_): return None
    monkeypatch.setattr("app.core.sales_forecast.request_plan", unavailable)
    result = asyncio.run(generate_sales_forecast(user(), payload()["evidence"]))
    assert result["status"] == "manual_fallback"
    assert result["annual_sales"]["base"] == 900000
    assert not result["monthly_scenarios"]


def test_accepted_forecast_replays_without_llm():
    first = calculate_forecast(ForecastPlan(**plan_dict()), payload())
    replay = calculate_forecast(ForecastPlan(**first["accepted_plan"]), payload())
    assert first["annual_sales"] == replay["annual_sales"]
    assert first["monthly_scenarios"] == replay["monthly_scenarios"]


@pytest.mark.parametrize("method,drivers", [
    ("buyer_orders", {"active_buyers": 5, "orders_per_buyer": 2, "units_per_order": 10}),
    ("service_visits", {"bookable_customers": 20, "visits_per_customer": 1, "units_per_visit": 1}),
    ("traffic_conversion", {"qualified_visits": 1000, "conversion_rate": .02, "units_per_order": 2}),
    ("subscriptions", {"active_subscribers": 30, "recognized_units_per_subscriber": 1}),
    ("occupancy", {"rentable_units": 10, "available_periods": 25, "occupancy_rate": .4}),
])
def test_business_specific_demand_equations(method, drivers):
    import math
    from app.core.sales_forecast import DRIVER_UNITS
    raw = plan_dict(); product = raw["products"][0]
    product["method"] = method
    product["assumptions"] = {key: source(DRIVER_UNITS[key].format(unit="litre")) for key in drivers}
    product["assumptions"]["selling_price"] = source("INR/litre")
    for scenario in product["scenarios"].values():
        scenario["drivers"] = {key: [value]*12 for key, value in drivers.items()}
    result = calculate_forecast(ForecastPlan(**raw), payload())
    assert result["annual_sales"]["base"] == math.prod(drivers.values()) * 60 * 12


def test_user_operating_schedule_cannot_be_overridden():
    p = payload(); p["user_constraints"]["operating_days_per_month"] = 20
    with pytest.raises(ValueError, match="user's operating schedule"):
        calculate_forecast(ForecastPlan(**plan_dict()), p)


def test_explicit_extraction_yield_is_applied_to_raw_throughput():
    p = build_payload(user(enterprise_name="Cold pressed edible oil seed extraction", additional_business_details="Oil sold by kg"), {})
    row = p["machinery_options"][0]
    raw = plan_dict(); prod = raw["products"][0]
    prod["profile_id"] = row["profile_id"]
    prod["output_per_input"] = assumption(.3, "litre/kg")
    prod["independent_capacity_per_month"] = [1e7]*12
    for scenario in prod["scenarios"].values():
        scenario["drivers"]["active_buyers"] = [1e5]*12
    result = calculate_forecast(ForecastPlan(**raw), p)
    machine = result["selected_equipment"][0]
    line = result["monthly_scenarios"]["base"][0]["products"][0]
    assert line["units_sold"] == pytest.approx(machine["monthly_input_capacity"][0] * .3)


def test_provider_schema_correction_is_bounded_and_recalculates(monkeypatch):
    import json, httpx
    from app.config import settings
    from app.core.sales_forecast import request_plan
    monkeypatch.setattr(settings, "GROQ_API_KEY_LLM", "synthetic-test-key")
    monkeypatch.setattr(settings, "SARVAM_API_KEY", None)
    invalid = plan_dict(); invalid["products"][0]["scenarios"]["base"]["selling_prices"] = [60]
    calls = []
    class Client:
        def __init__(self, **_): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *_): pass
        async def post(self, endpoint, **kwargs):
            calls.append(copy.deepcopy(kwargs["json"]))
            content = invalid if len(calls) == 1 else plan_dict()
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(content)}}]},
                                  request=httpx.Request("POST", endpoint))
    monkeypatch.setattr("app.core.sales_forecast.httpx.AsyncClient", Client)
    result = asyncio.run(request_plan(payload()))
    assert len(calls) == 2
    assert result["annual_sales"]["base"] == 720000
    assert "Correct these contract errors" in calls[1]["messages"][-1]["content"]
    assert "input" not in calls[1]["messages"][-1]["content"]


def test_no_configured_providers_returns_without_network(monkeypatch):
    from app.config import settings
    from app.core.sales_forecast import request_plan
    monkeypatch.setattr(settings, "GROQ_API_KEY_LLM", None)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "SARVAM_API_KEY", None)
    assert asyncio.run(request_plan(payload())) is None


def test_equivalent_labels_do_not_rescale_values():
    raw = plan_dict()
    raw["products"][0]["assumptions"]["active_buyers"]["unit"] = "households/month"
    raw["products"][0]["assumptions"]["transactions_per_buyer"]["unit"] = "transactions/household/month"
    raw["products"][0]["assumptions"]["selling_price"]["unit"] = "INR/litres"
    result = calculate_forecast(ForecastPlan(**raw), payload())
    assert result["annual_sales"]["base"] == 720000


def test_service_can_reserve_all_capital_without_fabricating_equipment():
    raw = plan_dict(); raw["non_machinery_budget_inr"]["value"] = 2_000_000
    result = calculate_forecast(ForecastPlan(**raw), payload())
    assert result["annual_sales"]["base"] == 720000
    assert not result["selected_equipment"]


def test_global_currency_scale_and_boolean_quantities_are_not_silently_accepted():
    raw = plan_dict(); raw["non_machinery_budget_inr"]["unit"] = "lakh"
    with pytest.raises(ValueError, match="Global assumptions"):
        calculate_forecast(ForecastPlan(**raw), payload())
    raw = plan_dict(); raw["availability"]["value"] = True
    with pytest.raises(ValidationError):
        ForecastPlan(**raw)


def test_small_capacity_utilisation_triggers_review_not_sales_inflation():
    raw = plan_dict(); raw["products"][0]["independent_capacity_per_month"] = [100000]*12
    result = calculate_forecast(ForecastPlan(**raw), payload())
    assert result["annual_sales"]["base"] == 720000
    assert result["review_required"]
    assert any("below 10%" in w for w in result["warnings"])
