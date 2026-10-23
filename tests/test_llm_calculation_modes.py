"""The primary calculation path accepts model results and never runs legacy math."""
import json

import pytest

from backend.app.core import llm_financials
from backend.app.core.enterprise_assumptions import estimate_operations, calculate_operations
from backend.app.core.llm_capacity import interpret_capacity
from backend.app.core.llm_json import response_object
from backend.app.core.llm_json import structured_response_format
from tests.planning_fixtures import raw_input_conversion, uniform_price_mix


def operations():
    a = estimate_operations({"idea": "Paneer manufacturing", "sector": "dairy", "households": 10,
        "project_cost": 500000, "business_category": "manufacturing"})
    return calculate_operations(a)


def facts():
    return dict(project_cost=500000, loan_principal=300000, annual_rate_pct=10,
        tenure_years=7, moratorium_months=6, sector="dairy", cpi_pct=5,
        subsidy_amount=100000, promoter_margin=100000)


def test_finance_tool_response_is_used_without_running_legacy_calculator(monkeypatch):
    ops, inputs = operations(), facts()
    response = llm_financials._fallback(ops, inputs).model_dump(mode="json")
    def legacy_must_not_run(*args, **kwargs):
        pytest.fail("Primary model path called the legacy calculator")
    monkeypatch.setattr(llm_financials, "_fallback", legacy_must_not_run)
    def llm(**kwargs):
        assert kwargs["response_format"]["json_schema"]["name"] == "financial_plan"
        package = json.loads(kwargs["messages"][1]["content"])
        assert package["accepted_operating_calculations"]["annual_sales"] == ops["annual_sales"]
        return "", {"name": "submit_financial_plan", "arguments": response}, "test-model"
    result = llm_financials.calculate_report_finance(ops, inputs, llm)
    assert result["source"] == "llm_calculated"
    assert result["result"].model_dump(mode="json") == response


@pytest.mark.parametrize("bad_field", ["sales", "principal", "nonfinite", "incomplete", "conflicting_dscr", "missing_year_one_debt", "broken_profit", "broken_emi"])
def test_invalid_model_finances_fall_back_without_inflating_sales(bad_field):
    ops, inputs = operations(), facts()
    response = llm_financials._fallback(ops, inputs).model_dump(mode="json")
    if bad_field == "sales":
        response["projections"][0]["gross_turnover"] = ops["annual_sales"] * 20
    elif bad_field == "principal":
        response["amortization"]["principal"] = 100
    elif bad_field == "nonfinite":
        response["amortization"]["monthly_emi"] = float("nan")
    elif bad_field == "incomplete":
        response["projections"] = response["projections"][:2]
    elif bad_field == "missing_year_one_debt":
        response["projections"][0]["total_debt_service"] = 0
    elif bad_field == "broken_profit":
        response["projections"][0]["profit_before_tax"] += 10000
    elif bad_field == "broken_emi":
        response["amortization"]["monthly_emi"] *= 2
    else:
        response["dscr"]["dscr"] = 99
    result = llm_financials.calculate_report_finance(ops, inputs,
        lambda **kwargs: ("", {"name": "submit_financial_plan", "arguments": response}, "test"))
    assert result["source"] == "indicative_calculation_fallback"
    assert result["result"].projections[0].gross_turnover == ops["annual_sales"]
    assert result["result"].dscr.dscr < 1


def test_capacity_function_response_retains_model_computed_monthly_value():
    response = dict(quantity=10000, unit="kg", period="stock", monthly_quantity=8000,
        capacity_kind="storage", basis="10 MT inventory; estimated 80% monthly occupancy")
    result = interpret_capacity("10 MT capacity", llm_call=lambda **kwargs: (
        "", {"name": "submit_capacity", "arguments": response}, "test"))
    assert result["monthly_quantity"] == 8000
    assert result["capacity_kind"] == "storage"
    assert result["source"] == "llm_calculated"


def test_json_provider_fences_and_trailing_comment_do_not_discard_a_valid_object():
    assert response_object('```json\n{"quantity":500}\n```\nExplanation', None, "test") == {"quantity": 500}
    with pytest.raises(ValueError):
        response_object("[]", None, "test")


def test_finance_schema_has_no_unresolved_references_or_optional_objects():
    schema = structured_response_format(llm_financials.ReportFinance, "financial_plan")["json_schema"]["schema"]
    assert "$ref" not in json.dumps(schema)
    assert schema["required"] == list(schema["properties"])
    assert schema["properties"]["amortization"]["additionalProperties"] is False


def test_llm_repairs_its_own_inconsistent_summary_without_backend_recalculation(monkeypatch):
    ops, inputs = operations(), facts()
    good = llm_financials._fallback(ops, inputs).model_dump(mode="json")
    bad = json.loads(json.dumps(good))
    bad["dscr"]["dscr"] = 99
    calls = []
    def llm(**kwargs):
        calls.append(kwargs)
        return json.dumps(bad if len(calls) == 1 else good), None, "test"
    monkeypatch.setattr(llm_financials, "_fallback", lambda *args: pytest.fail("Legacy calculation ran"))
    result = llm_financials.calculate_report_finance(ops, inputs, llm)
    assert len(calls) == 2
    assert "validation issue" in calls[-1]["messages"][-1]["content"]
    assert result["source"] == "llm_calculated"
    assert result["result"].dscr.dscr == good["dscr"]["dscr"]


def test_invalid_operating_arithmetic_is_not_accepted_as_llm_calculated():
    ctx = {"idea": "Paneer manufacturing", "sector": "dairy", "households": 100,
        "project_cost": 500000, "business_category": "manufacturing"}
    seed = estimate_operations(ctx)
    good = {"values": seed["values"], "calculations": calculate_operations(seed),
        "conversion": raw_input_conversion(seed["values"]),
        "pricing": uniform_price_mix(seed["values"]),
        "capacity": dict(quantity=0, unit=seed["values"]["input_unit"], period="unknown",
            monthly_quantity=seed["values"]["rated_monthly_input_units"], capacity_kind="unknown", basis="Fixture planning estimate")}
    bad = json.loads(json.dumps(good))
    bad["calculations"]["annual_sales"] = 1
    calls = []
    def repair(**kwargs):
        calls.append(kwargs)
        return json.dumps(bad if len(calls) == 1 else good), None, "test"
    result = estimate_operations(ctx, repair)
    assert len(calls) == 2
    assert result["calculation_source"] == "llm_calculated"
    assert result["calculations"]["annual_sales"] == good["calculations"]["annual_sales"]
    invalid = estimate_operations(ctx, lambda **kwargs: (json.dumps(bad), None, "test"))
    assert invalid["calculation_source"] == "indicative_calculation_fallback"
    assert calculate_operations(invalid)["annual_sales"] != 1
