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


def test_fabricated_evidence_reference_rejected():
    raw = plan_dict()
    raw["products"][0]["assumptions"]["selling_price"].update(
        source_kind="supplied_evidence", evidence_ref="evidence.nonexistent_market_survey")
    with pytest.raises(ValueError, match="Invented"):
        calculate_forecast(ForecastPlan(**raw), payload())


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
