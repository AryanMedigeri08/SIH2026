"""Investment cannot shrink below equipment or be reverse-sized to a DSCR target."""
import copy
import json

import pytest

from backend.app.core import project_budget as budgets, llm_financials
from tests.test_llm_calculation_modes import operations, facts


def context():
    return {"idea": "Ice cream venture", "machinery_profile": {"machinery_list": [
        {"machine_name": "Freezer", "estimated_cost_inr": 492700, "quantity": 1},
        {"machine_name": "Processing line", "estimated_cost_inr": 314600, "quantity": 1},
    ]}, "promoter_equity": 100000}


def test_actual_outlay_includes_missing_equipment_setup_and_reserve_independent_of_cash():
    ops, ctx = operations(), context()
    one = budgets.estimate_project_budget(ctx, ops, 492700)
    ctx["promoter_equity"] = 5000000
    two = budgets.estimate_project_budget(ctx, ops, 492700)
    assert one == two
    assert one["equipment_total"] == 807300
    assert one["net_fresh_outlay"] > 314600
    assert one["gross_project_cost"] - one["owned_machinery_credit"] == one["net_fresh_outlay"]
    assert one["monthly"]["wages"]["amount_inr"] > 0
    funded = budgets.reconcile_funding(one, 100000)
    assert funded["cash_applied"] + funded["loan_required"] == one["net_fresh_outlay"]
    assert funded["upfront_subsidy"] == 0


def test_ownership_is_matched_deduplicated_and_valued_at_selected_prices():
    ctx = context()
    owned = [{"machine_name": "Freezer", "estimated_cost_inr": 1e9, "quantity": 99},
             {"machine_name": "freezer", "quantity": 1}, {"machine_name": "unknown", "quantity": 10}]
    assert budgets.equipment_and_credit(ctx["machinery_profile"], 1e10, owned) == (807300, 492700)
    assert budgets.equipment_and_credit(ctx["machinery_profile"], 1e10) == (807300, 807300)
    assert budgets.equipment_and_credit(ctx["machinery_profile"], 1e10, []) == (807300, 0)


def test_cash_is_never_invented_or_spent_twice():
    budget = budgets.estimate_project_budget(context(), operations())
    missing = budgets.reconcile_funding(budget, None)
    assert missing["cash_applied"] == 0
    assert missing["loan_required"] == budget["net_fresh_outlay"]
    excess = budgets.reconcile_funding(budget, 10000000)
    assert excess["loan_required"] == 0
    assert excess["cash_applied"] + excess["unused_cash"] == 10000000


def test_budget_primary_repairs_its_arithmetic_and_keeps_sales(monkeypatch):
    ops, ctx = operations(), context()
    seed = budgets.estimate_project_budget(ctx, ops)
    good = {key: seed[key] for key in budgets.BudgetEstimate.model_fields}
    bad = copy.deepcopy(good)
    bad["net_fresh_outlay"] = 100
    calls = []
    def llm(**kwargs):
        calls.append(kwargs)
        package = json.loads(kwargs["messages"][1]["content"])
        assert "promoter_equity" not in package["budget_evidence"]
        assert package["immutable_equipment_total"] == 807300
        return json.dumps(bad if len(calls) == 1 else good), None, "test"
    monkeypatch.setattr(budgets, "_fallback", lambda *args: pytest.fail("Unexpected budget fallback"))
    budget = budgets.estimate_project_budget(ctx, ops, llm_call=llm)
    updated = budgets.apply_project_budget(ops, budget)
    assert len(calls) == 2
    assert budget["source"] == "llm_itemized_budget"
    for key in ("annual_sales", "monthly_sales_units", "selling_price_inr", "annual_variable_cost"):
        assert updated[key] == ops[key]
    assert updated["annual_operating_cashflow"] < 0
    assert ops["assumptions"].get("project_budget") is None


@pytest.mark.parametrize("reply", [None, "[]", '{"gross_project_cost":1}', '{"gross_project_cost":NaN}'])
def test_budget_provider_failure_is_nonblocking_and_labelled(reply):
    def llm(**kwargs):
        if reply is None:
            raise TimeoutError("offline")
        return reply, None, "test"
    budget = budgets.estimate_project_budget(context(), operations(), 492700, llm_call=llm)
    assert budget["source"] == "indicative_budget_fallback"
    assert budget["net_fresh_outlay"] > 314600


def test_good_llm_cost_estimates_survive_invalid_total_arithmetic():
    ops, ctx = operations(), context()
    seed = budgets.estimate_project_budget(ctx, ops)
    response = {key: seed[key] for key in budgets.BudgetEstimate.model_fields}
    # Distinct AI estimate: it must not silently become the default wage allowance.
    response["monthly"]["wages"] = {"amount_inr": 18000, "basis": "Estimated one paid operator at the selected scale"}
    response["gross_project_cost"] = 1
    budget = budgets.estimate_project_budget(ctx, ops, llm_call=lambda **kwargs: (json.dumps(response), None, "test"))
    assert budget["source"] == "llm_costs_with_validated_arithmetic"
    assert budget["monthly"]["wages"]["amount_inr"] == 18000
    assert budget["monthly_fixed_cost"] == seed["monthly_fixed_cost"] + 6000
    assert budget["gross_project_cost"] == seed["gross_project_cost"]
    assert budget["net_fresh_outlay"] == seed["net_fresh_outlay"]


@pytest.mark.parametrize("bad_field", ["average", "interest_allocation", "verdict"])
def test_invalid_dscr_or_debt_schedule_cannot_pass_validation(bad_field):
    ops, inputs = operations(), facts()
    good = llm_financials._fallback(ops, inputs).model_dump()
    bad = copy.deepcopy(good)
    if bad_field == "average":
        bad["summary"]["average_dscr"] = 86
    elif bad_field == "verdict":
        bad["dscr"]["verdict"] = "VIABLE"
    else:
        bad["projections"][0]["bank_interest"] = 0
        bad["projections"][0]["loan_principal_repayment"] = bad["projections"][0]["total_debt_service"]
    result = llm_financials.calculate_report_finance(ops, inputs,
        lambda **kwargs: (json.dumps(bad), None, "test"))
    assert result["source"] == "indicative_calculation_fallback"
    assert result["result"].projections[0].annual_dscr == good["projections"][0]["annual_dscr"]


def test_full_year_moratorium_has_no_false_zero_coverage_verdict():
    ops, inputs = operations(), facts()
    inputs["moratorium_months"] = 12
    result = llm_financials.calculate_report_finance(ops, inputs)["result"]
    assert result.dscr.verdict == "MORATORIUM"
    assert result.projections[0].gross_turnover == ops["annual_sales"]
    assert result.projections[0].total_debt_service == 0
    assert result.projections[1].total_debt_service > 0


def test_future_sales_cannot_be_inflated_to_create_high_full_year_coverage():
    ops, inputs = operations(), facts()
    response = llm_financials._fallback(ops, inputs).model_dump()
    row = response["projections"][1]
    row["gross_turnover"] *= 100
    row["ebitda"] = row["gross_turnover"] - row["total_operating_expenses"]
    row["profit_before_tax"] = row["ebitda"] - row["depreciation"] - row["bank_interest"]
    row["tax_provision"] = row["profit_before_tax"] * .15
    row["profit_after_tax"] = row["profit_before_tax"] - row["tax_provision"]
    row["cash_accruals"] = row["profit_after_tax"] + row["depreciation"]
    row["annual_dscr"] = (row["cash_accruals"] + row["bank_interest"]) / row["total_debt_service"]
    response["summary"]["average_dscr"] = sum(r["annual_dscr"] for r in response["projections"]) / 5
    response["summary"]["dscr_benchmark_met"] = True
    result = llm_financials.calculate_report_finance(ops, inputs,
        lambda **kwargs: (json.dumps(response), None, "test"))
    assert result["source"] == "indicative_calculation_fallback"
    assert result["result"].projections[1].gross_turnover < row["gross_turnover"]
