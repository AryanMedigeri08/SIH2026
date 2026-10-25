"""Keep quantities fixed while testing price-mix effects on revenue and coverage."""
import copy
import json

import pytest

from backend.app.core.enterprise_assumptions import estimate_operations, calculate_operations
from backend.app.core.llm_financials import calculate_report_finance
from tests.test_production_conversion import CASES, package
from tests.planning_fixtures import business_demand_fixture


def weighted_package():
    response = package(CASES[0])
    response["values"]["selling_price_inr"] = 26
    response["pricing"] = dict(output_unit="cups", reference_selling_price_inr=30,
        sales_mix=[dict(segment="Retail", quantity_share=.6, quoted_price_inr=30,
                       output_units_per_quote=1, discount_pct=0, realized_unit_price_inr=30),
                   dict(segment="Wholesale cartons of ten cups", quantity_share=.4, quoted_price_inr=250,
                       output_units_per_quote=10, discount_pct=20, realized_unit_price_inr=20)],
        basis="Synthetic scenario: 60% of units at retail price; 40% in ten-cup wholesale cartons with a 20% discount.")
    # Preserve the existing price experiment's 1,000-cup demand as synthetic active customers.
    c = response["calculations"]
    c.update(selling_price_inr=26, monthly_sales_units=1000, monthly_local_demand_units=1000,
        monthly_gross_sales=26000, annual_sales=312000, annual_variable_cost=33000,
        annual_fixed_cost=1200, annual_operating_cashflow=277800,
        annual_capacity_sales=7987200, unit_cost_floor=2.85)
    response["demand_forecast"] = business_demand_fixture(response["values"], c)
    return response


def run(response, override=None):
    ctx = dict(idea="Ice cream in 100 ml cups", sector="dairy", project_cost=500000,
        households=4000, business_category="manufacturing", annual_sales_override=override)
    a = estimate_operations(ctx, lambda **kwargs: (json.dumps(response), None, "test"))
    return calculate_operations(a, override)


def test_quantity_weighted_realized_price_drives_all_revenue_fields():
    ops = run(weighted_package())
    assert ops["calculation_source"] == "llm_calculated"
    assert ops["monthly_sales_units"] == 1000
    assert ops["selling_price_inr"] == ops["average_selling_price_inr"] == 26
    assert ops["monthly_gross_sales"] == 26000
    assert ops["annual_sales"] == 312000
    comparison = ops["price_comparison"]
    assert comparison["reference_annual_sales"] == 360000
    assert comparison["weighted_annual_sales"] == 312000
    assert comparison["annual_sales_difference"] == -48000
    assert comparison["annual_sales_change_pct"] == -13.33
    assert "not an earlier report" in comparison["basis"]


@pytest.mark.parametrize("mistake", ["simple_average", "wrong_quote_normalization", "double_discount", "weights", "unit", "reference_revenue", "nonfinite"])
def test_bad_mix_or_average_is_never_accepted_as_llm_calculated(mistake):
    response = weighted_package()
    if mistake == "simple_average":
        response["values"]["selling_price_inr"] = 25
        response["calculations"]["selling_price_inr"] = 25
    elif mistake == "wrong_quote_normalization":
        response["pricing"]["sales_mix"][1]["realized_unit_price_inr"] = 200
    elif mistake == "double_discount":
        response["pricing"]["sales_mix"][1]["realized_unit_price_inr"] = 16
    elif mistake == "weights":
        response["pricing"]["sales_mix"][1]["quantity_share"] = .2
    elif mistake == "unit":
        response["pricing"]["output_unit"] = "litres"
    elif mistake == "reference_revenue":
        response["calculations"]["annual_sales"] = 360000
    else:
        response["pricing"]["sales_mix"][0]["quoted_price_inr"] = float("inf")
    ops = run(response)
    assert ops["calculation_source"] == "indicative_calculation_fallback"
    assert ops["annual_sales"] >= 0
    if mistake in {"simple_average", "wrong_quote_normalization", "double_discount", "reference_revenue"}:
        assert ops["average_selling_price_inr"] == 26
        assert ops["monthly_sales_units"] == 1000
        assert ops["annual_sales"] == 312000


def test_valid_mix_survives_arithmetic_failure_with_conversion_preserved():
    response = weighted_package()
    response["values"]["selling_price_inr"] = 25
    response["calculations"]["selling_price_inr"] = 25
    ops = run(response)
    assert ops["assumptions"]["pricing"]["source"] == "llm_mix_with_indicative_arithmetic"
    assert ops["assumptions"]["conversion"]["saleable_unit_quantity"] == .1
    assert ops["price_comparison"]["annual_sales_difference"] == -48000


def test_explicit_user_sales_and_zero_are_preserved_and_have_no_comparison():
    for amount in (0, 120000):
        ops = run(weighted_package(), amount)
        assert ops["annual_sales"] == amount
        assert ops["price_comparison"] is None


def test_uniform_price_has_no_invented_revenue_change():
    response = weighted_package()
    response["pricing"]["sales_mix"] = [dict(segment="Uniform price", quantity_share=1,
        quoted_price_inr=26, output_units_per_quote=1, discount_pct=0, realized_unit_price_inr=26)]
    response["pricing"]["reference_selling_price_inr"] = 26
    ops = run(response)
    assert ops["calculation_source"] == "llm_calculated"
    assert ops["price_comparison"]["annual_sales_difference"] == 0


def test_model_can_repair_wrong_average_once():
    good = weighted_package()
    bad = copy.deepcopy(good)
    bad["values"]["selling_price_inr"] = bad["calculations"]["selling_price_inr"] = 25
    calls = []
    def llm(**kwargs):
        calls.append(kwargs)
        return json.dumps(bad if len(calls) == 1 else good), None, "test"
    a = estimate_operations(dict(idea="Ice cream in 100 ml cups", households=4000, sector="dairy"), llm)
    assert len(calls) == 2
    assert a["calculation_source"] == "llm_calculated"
    assert calculate_operations(a)["average_selling_price_inr"] == 26


def test_same_loan_and_costs_produce_lower_dscr_when_average_price_is_lower():
    weighted = run(weighted_package())
    reference = copy.deepcopy(weighted)
    reference["selling_price_inr"] = reference["average_selling_price_inr"] = 30
    reference["monthly_gross_sales"] = 30000
    reference["annual_sales"] = 360000
    reference["annual_operating_cashflow"] += 48000
    reference["assumptions"]["values"]["selling_price_inr"] = 30
    facts = dict(project_cost=500000, loan_principal=100000, annual_rate_pct=11,
        tenure_years=7, moratorium_months=6, cpi_pct=4, sector="dairy",
        subsidy_amount=0, promoter_margin=100000)
    old = calculate_report_finance(reference, facts)["result"]
    new = calculate_report_finance(weighted, facts)["result"]
    assert new.amortization.monthly_emi == old.amortization.monthly_emi
    assert new.dscr.dscr < old.dscr.dscr
    assert new.projections[0].total_operating_expenses == old.projections[0].total_operating_expenses
