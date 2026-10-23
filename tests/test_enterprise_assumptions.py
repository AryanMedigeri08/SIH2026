"""Regression cases for non-blocking estimates and honest financial outcomes."""
import json
import math

import pytest

from backend.app.core.capacity_units import parse_capacity
from backend.app.core.llm_capacity import interpret_capacity
from backend.app.core.enterprise_assumptions import estimate_operations, calculate_operations
from backend.app.core.business_interpreter import interpret_business_idea
from backend.app.core.operating_finance import project_cashflows
from backend.app.core.financial_calculator import emi_with_moratorium


def context(**updates):
    return {"idea": "Paneer manufacturing", "sector": "dairy", "project_cost": 500000,
            "business_category": "manufacturing", "households": 100,
            "machinery_profile": {"typical_capacity": "1000 L/day"},
            "amenities": {"power_supply_hours_per_day": 8}, **updates}


@pytest.mark.parametrize("text,quantity,unit", [
    ("3 Ton/hour", 600000, "kg"), ("20 Ton/day", 500000, "kg"),
    ("2,000 L/hour (100 jars/hr)", 400000, "litres"),
    ("60 pieces/min", 720000, "pieces"),
])
def test_capacity_is_interpreted_and_converted_by_llm(text, quantity, unit, monkeypatch):
    captured = {}
    def llm(**kwargs):
        captured.update(json.loads(kwargs["messages"][1]["content"]))
        return json.dumps(dict(quantity=quantity, unit=unit, period="hour", monthly_quantity=quantity,
            capacity_kind="throughput", basis="LLM converted source units and time period")), None, "test"
    import backend.app.core.capacity_units as legacy
    monkeypatch.setattr(legacy, "canonical_unit", lambda *args: pytest.fail("Legacy unit converter was called"))
    monkeypatch.setattr(legacy, "unit_scale", lambda *args: pytest.fail("Legacy scaling was called"))
    cap = interpret_capacity(text, context={"idea": "Test enterprise"}, llm_call=llm)
    assert captured["raw_capacity"] == text
    assert cap["monthly_quantity"] == quantity
    assert cap["unit"] == unit
    assert cap["source"] == "llm_calculated"


@pytest.mark.parametrize("text", ["10 MT capacity", "100 kg/batch", "500 kg/day", ""])
def test_legacy_parser_is_disabled_and_fallback_does_not_parse(text):
    assert parse_capacity(text).monthly_quantity is None
    cap = interpret_capacity(text)
    assert cap["source"] == "indicative_capacity_fallback"
    assert cap["unit"] == "units"
    result = calculate_operations(estimate_operations(context(machinery_profile={"typical_capacity": text})))
    assert result["annual_sales"] > 0
    assert result["calculation_source"] == "indicative_calculation_fallback"


@pytest.mark.parametrize("reply", ["not json", "[]", '{"selling_price_inr":null}', '{"selling_price_inr":1e999,"market_share":4}'])
def test_invalid_model_response_never_empties_sales(reply):
    assumptions = estimate_operations(context(), lambda **kwargs: (reply, None, "test"))
    result = calculate_operations(assumptions)
    assert math.isfinite(result["annual_sales"]) and result["annual_sales"] > 0


def model_plan(ctx):
    fallback = estimate_operations(ctx)
    fallback["values"]["rated_monthly_input_units"] = 25000
    calculations = calculate_operations(fallback)
    return {"values": fallback["values"], "calculations": calculations,
            "capacity": dict(quantity=1000, unit="litres", period="day", monthly_quantity=25000,
                capacity_kind="throughput", basis="1000 litres/day * 25 operating days/month")}


def test_llm_owns_raw_capacity_units_and_operating_calculations():
    captured = {}
    response = model_plan(context())
    def llm(**kwargs):
        captured.update(json.loads(kwargs["messages"][1]["content"]))
        return json.dumps(response), None, "test-model"
    assumptions = estimate_operations(context(), llm)
    assert captured["evidence"]["households"] == 100
    assert captured["evidence"]["amenities"]["power_supply_hours_per_day"] == 8
    assert captured["raw_capacity"] == "1000 L/day"
    assert "capacity_normalization" not in captured
    assert assumptions["values"]["rated_monthly_input_units"] == 25000
    assert assumptions["field_sources"]["rated_monthly_input_units"] == "llm_estimate"
    # These values would break the legacy calculations if that path ran.
    assumptions["evidence"]["households"] = "do not recalculate"
    result = calculate_operations(assumptions)
    for key in ("annual_sales", "monthly_saleable_capacity", "variable_cost_per_output_unit", "unit_cost_floor"):
        assert result[key] == response["calculations"][key]
    assert result["calculation_source"] == "llm_calculated"


def test_poor_demand_and_losses_survive_financial_projection():
    result = calculate_operations(estimate_operations(context(households=2)))
    rows = project_cashflows(result, 500000, 400000, 10, 7, 6, 5)
    assert rows[0]["gross_turnover"] == result["annual_sales"]
    assert rows[0]["ebitda"] < 0
    assert rows[0]["profit_after_tax"] < 0
    assert rows[0]["annual_dscr"] < 1
    # More debt cannot manufacture additional demand or revenue.
    more_debt = project_cashflows(result, 500000, 450000, 10, 7, 6, 5)
    assert more_debt[0]["gross_turnover"] == rows[0]["gross_turnover"]


def test_recipe_yield_and_demand_limit_sales_independently():
    ctx = context(households=1000000)
    a = estimate_operations(ctx, lambda **kwargs: (json.dumps(model_plan(ctx)), None, "test"))
    result = calculate_operations(a)
    assert result["monthly_saleable_capacity"] == pytest.approx(25000 / 5 * .75 * .97)
    assert result["monthly_sales_units"] == result["monthly_saleable_capacity"]
    local = calculate_operations(estimate_operations(context(households=10)))
    assert local["monthly_sales_units"] < result["monthly_sales_units"]


def test_zero_sales_and_zero_debt_are_valid_reports():
    result = calculate_operations(estimate_operations(context()), annual_sales_override=0)
    rows = project_cashflows(result, 500000, 0, 10, 5, 6, 5)
    assert rows[0]["gross_turnover"] == 0
    assert rows[0]["total_debt_service"] == 0
    assert rows[0]["annual_dscr"] == 0
    assert rows[0]["profit_after_tax"] < 0


def test_monthly_amortization_reconciles_to_quoted_emi_and_interest():
    result = calculate_operations(estimate_operations(context()))
    amort = emi_with_moratorium(400000, 10, 5, 6)
    rows = project_cashflows(result, 500000, 400000, 10, 5, 6, 5)
    assert sum(row["total_debt_service"] for row in rows) == pytest.approx(amort.total_repayment, abs=.03)
    assert rows[0]["total_debt_service"] == pytest.approx(amort.monthly_emi * 6, abs=.01)
    assert sum(row["loan_principal_repayment"] for row in rows) == pytest.approx(400000 + amort.moratorium_interest, abs=.03)


def test_semantic_idea_can_select_profile_outside_keyword_candidates():
    def llm(**kwargs):
        catalogue = json.loads(kwargs["messages"][1]["content"])["catalogue_candidates"]
        assert len(catalogue) == 37
        return json.dumps({"sector": "repair", "business_category": "service", "business_type": "service",
            "profile_name": "Automobile Workshop, Wheel Alignment & Hydraulic Ramp Station",
            "machine_names": ["Hydraulic Two-Post Vehicle Lift"]}), None, "test"
    result = interpret_business_idea("I will align tyres and maintain cars", llm)
    assert result["business_type"] == "service"
    assert result["sector"] == "repair"
    assert "Automobile Workshop" in result["matched_machinery_profile"]
    assert result["machinery_plan"]["machinery_list"]


def test_equipment_gaps_are_costed_as_estimates_not_supplier_quotes():
    def llm(**kwargs):
        return json.dumps({"sector": "general", "business_category": "manufacturing", "business_type": "manufacturing",
            "profile_name": None, "estimated_machines": [{"machine_name": "Desktop candle wax melter", "quantity": 1,
            "estimated_cost_inr": 18000}]}), None, "test"
    plan = interpret_business_idea("Make decorative candles", llm)["machinery_plan"]
    assert plan["has_estimated_equipment"]
    assert plan["machinery_list"][0]["cost_source"] == "llm_estimate"
    assert plan["total_machinery_cost_inr"] == 18000


def test_unit_prices_and_quantities_are_already_converted_in_llm_response():
    ctx = context(idea="Flour processing", sector="food_processing", machinery_profile={"typical_capacity": "1 Ton/hour"})
    response = model_plan(ctx)
    response["values"].update(input_unit="kg", output_unit="kg", rated_monthly_input_units=200000,
        selling_price_inr=40, raw_material_cost_per_input_unit_inr=25)
    response["capacity"].update(unit="kg", monthly_quantity=200000)
    fallback = estimate_operations(ctx)
    fallback["values"] = response["values"]
    response["calculations"] = calculate_operations(fallback)
    a = estimate_operations(ctx, lambda **kwargs: (json.dumps(response), None, "test"))
    assert a["values"]["selling_price_inr"] == 40
    assert a["values"]["raw_material_cost_per_input_unit_inr"] == 25
    assert a["values"]["rated_monthly_input_units"] == 200000
    assert a["values"]["output_unit"] == "kg"
    assert a["calculation_source"] == "llm_calculated"


def test_partial_unit_change_cannot_relabel_a_price():
    a = estimate_operations(context(), lambda **kwargs: (json.dumps({"output_unit": "tonnes", "selling_price_inr": 360000}), None, "test"))
    assert a["values"]["output_unit"] == "kg"
    assert a["values"]["selling_price_inr"] == 360
