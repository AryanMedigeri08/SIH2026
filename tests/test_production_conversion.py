"""Dimensional regressions across different enterprise revenue models.

All numeric product/price assumptions here are synthetic fixtures, not quotes.
"""
import copy
import json

import pytest

from backend.app.core.enterprise_assumptions import estimate_operations, calculate_operations


CASES = [
    # idea, model, basis, capacity unit, period, source quantity, monthly capacity,
    # input unit, output unit, input recipe, capacity conversion, portion measure,
    # portion size, utilization, saleable fraction, expected production, seasonality
    ("Ice cream in 100 ml cups from milk", "manufacturing", "raw_input", "litres", "day", 100, 2500,
        "litres", "cups", .075, .075, "litres", .1, .8, .96, 25600, .5),
    ("Ice cream in 100 ml cups from a finished mix output line", "manufacturing", "finished_output", "litres", "day", 100, 2500,
        "litres", "cups", .075, .1, "litres", .1, .8, .96, 19200, .5),
    ("Paneer sold by kg", "manufacturing", "raw_input", "litres", "day", 100, 2500,
        "litres", "kg", 5, 5, "kg", 1, .8, .96, 384, 1),
    ("Oil pressed from seed and sold by litre", "manufacturing", "raw_input", "kg", "day", 100, 2500,
        "kg", "litres", 3, 3, "litres", 1, .8, .96, 640, 1),
    ("Paper bags from a line rated in finished bags", "manufacturing", "finished_output", "bags", "day", 100, 2500,
        "kg", "bags", .01, 1, "kg", .01, .8, .96, 1920, 1),
    ("Repairs requiring two mechanic hours per job", "service", "service_time", "hours", "day", 8, 200,
        "jobs", "jobs", 1, 2, "hours", 2, .8, 1, 80, 1),
    ("Retail shop selling ready-made T-shirts", "retail", "retail_supply", "pieces", "month", 5000, 5000,
        "pieces", "pieces", 1, 1, "pieces", 1, .8, 1, 4000, 1),
    ("Cold storage billed per kg per month", "storage", "storage_stock", "kg", "stock", 10000, 10000,
        "kg", "kg", 1, 1, "kg", 1, .6, 1, 6000, 1),
]


def package(case):
    (idea, model, basis, cap_unit, period, quantity, monthly_cap, input_unit, output_unit,
        recipe, conversion_ratio, measure, portion, utilization, saleable, production, seasonal) = case
    values = dict(product=idea, input_unit=input_unit, output_unit=output_unit,
        selling_price_inr=20, raw_material_cost_per_input_unit_inr=10,
        input_units_per_output_unit=recipe, other_variable_cost_per_output_unit_inr=2,
        monthly_fixed_cost_inr=100, rated_monthly_input_units=monthly_cap / conversion_ratio * recipe,
        utilization=utilization, saleable_fraction=saleable, target_household_fraction=.5,
        purchases_per_household_month=1, output_units_per_purchase=1, market_share=1,
        external_monthly_demand_units=0, external_demand_basis="Synthetic local-only fixture",
        rationale="Synthetic first-year planning assumptions; explicit product portion, recipe and seasonal demand.")
    capacity = dict(quantity=quantity, unit=cap_unit, period=period, monthly_quantity=monthly_cap,
        capacity_kind="storage" if model == "storage" else "service" if model == "service" else "throughput",
        basis="Explicit synthetic source capacity with a 25-day monthly schedule and 8 hours/day.")
    conversion = dict(business_model=model, capacity_basis=basis,
        saleable_unit_definition=f"One sold unit of {idea}; {portion} {measure}",
        saleable_unit_quantity=portion, saleable_unit_measure=measure,
        billing_period="month" if model == "storage" else "job" if model == "service" else "item",
        capacity_units_per_output_unit=conversion_ratio, working_days_per_month=25,
        working_hours_per_day=8, batches_per_day=1, storage_cycles_per_month=1,
        seasonality_factor=seasonal, conversion_basis="Synthetic recipe and portion: source capacity divided by capacity per output, then utilization/losses once.")
    demand = 50000 * seasonal
    sold = min(production, demand)
    variable_cost = 10 * recipe + 2
    monthly_gross = sold * 20
    calculations = dict(monthly_sales_units=sold, monthly_gross_sales=monthly_gross,
        annual_sales=monthly_gross * 12, monthly_saleable_capacity=production,
        monthly_local_demand_units=demand, variable_cost_per_output_unit=variable_cost,
        annual_variable_cost=sold * variable_cost * 12, annual_fixed_cost=1200,
        annual_operating_cashflow=monthly_gross * 12 - sold * variable_cost * 12 - 1200,
        annual_capacity_sales=production * 20 * 12, unit_cost_floor=variable_cost + 100 / sold,
        output_unit=output_unit, selling_price_inr=20)
    return {"values": values, "capacity": capacity, "conversion": conversion, "calculations": calculations}


def estimate(response, override=None):
    ctx = {"idea": response["values"]["product"], "sector": "general", "households": 100000,
        "business_type": response["conversion"]["business_model"], "project_cost": 500000,
        "annual_sales_override": override}
    return estimate_operations(ctx, lambda **kwargs: (json.dumps(response), None, "fixture-model"))


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_each_business_returns_one_validated_monthly_quantity_and_matching_revenue(case):
    response = package(case)
    assumptions = estimate(response)
    assert assumptions["calculation_source"] == "llm_calculated"
    result = calculate_operations(assumptions)
    assert result["monthly_saleable_capacity"] == case[15]
    assert result["monthly_sales_units"] == response["calculations"]["monthly_sales_units"]
    assert result["monthly_gross_sales"] == response["calculations"]["monthly_gross_sales"]
    assert result["annual_sales"] == result["monthly_gross_sales"] * 12
    assert result["saleable_unit_definition"] == response["conversion"]["saleable_unit_definition"]


@pytest.mark.parametrize("mistake", ["undefined_portion", "finished_yield_twice", "wrong_monthly_schedule", "inflated_sales", "wrong_monthly_revenue", "wrong_recipe", "storage_turnover", "raw_cost_price_unit"])
def test_invalid_conversion_is_rejected_and_report_stays_available(mistake):
    response = package(CASES[0])
    if mistake == "undefined_portion":
        response["conversion"].update(saleable_unit_measure="cups", saleable_unit_quantity=1,
            saleable_unit_definition="One generic ice cream piece")
    elif mistake == "finished_yield_twice":
        response = package(CASES[4])
        response["conversion"]["capacity_units_per_output_unit"] = .01
    elif mistake == "wrong_monthly_schedule":
        response["capacity"]["monthly_quantity"] = 25000
    elif mistake == "inflated_sales":
        response["calculations"]["monthly_sales_units"] = 100000
    elif mistake == "wrong_monthly_revenue":
        response["calculations"]["monthly_gross_sales"] = 1
    elif mistake == "wrong_recipe":
        response["conversion"]["capacity_units_per_output_unit"] = 1
    elif mistake == "storage_turnover":
        response = package(CASES[7])
        response["conversion"]["storage_cycles_per_month"] = 30
    else:
        response["values"]["input_unit"] = "kg"
    result = calculate_operations(estimate(response))
    assert result["calculation_source"] == "indicative_calculation_fallback"
    assert result["annual_sales"] >= 0


def test_bad_arithmetic_keeps_only_the_validated_product_conversion_in_fallback():
    response = package(CASES[0])
    response["calculations"]["annual_sales"] = 1
    a = estimate(response)
    assert a["calculation_source"] == "indicative_calculation_fallback"
    assert a["conversion"]["saleable_unit_quantity"] == .1
    result = calculate_operations(a)
    assert result["monthly_saleable_capacity"] == pytest.approx(25600)
    assert result["monthly_sales_units"] == 25000
    assert result["annual_sales"] == 6000000


def test_llm_repairs_portion_conversion_instead_of_backend_guessing_it():
    good = package(CASES[0])
    bad = copy.deepcopy(good)
    bad["conversion"]["saleable_unit_measure"] = "cups"
    calls = []
    def llm(**kwargs):
        calls.append(kwargs)
        return json.dumps(bad if len(calls) == 1 else good), None, "fixture-model"
    result = estimate_operations({"idea": good["values"]["product"], "households": 100000, "sector": "dairy"}, llm)
    assert len(calls) == 2
    assert result["calculation_source"] == "llm_calculated"
    payload = json.loads(calls[0]["messages"][1]["content"])
    assert "indicative_assumption_baselines" not in payload
    assert "conversion" in payload["output_schema_example"]


def test_explicit_zero_sales_remains_immutable_with_new_conversion():
    response = package(CASES[0])
    result = calculate_operations(estimate(response, override=0), annual_sales_override=0)
    assert result["annual_sales"] == 0
    assert result["monthly_sales_units"] == 0
    assert result["monthly_gross_sales"] == 0


@pytest.mark.parametrize("period,quantity", [("hour", 12.5), ("minute", 12.5 / 60), ("batch", 50), ("month", 2500), ("year", 30000)])
def test_schedule_conversion_preserves_same_monthly_input(period, quantity):
    response = package(CASES[0])
    response["capacity"].update(period=period, quantity=quantity)
    if period == "batch":
        response["conversion"]["batches_per_day"] = 2
    result = estimate(response)
    assert result["calculation_source"] == "llm_calculated"
    assert result["calculations"]["monthly_saleable_capacity"] == 25600


def test_storage_day_billing_uses_stock_days_not_invented_throughput():
    response = package(CASES[7])
    response["conversion"].update(billing_period="day", storage_cycles_per_month=25,
        saleable_unit_definition="1 kg of goods stored for one paid day")
    response["values"]["rated_monthly_input_units"] = 250000
    c = response["calculations"]
    c.update(monthly_saleable_capacity=150000, annual_capacity_sales=36000000)
    # Demand stays 50,000 kg-days/month, within the stock-day capacity.
    c.update(monthly_sales_units=50000, monthly_gross_sales=1000000, annual_sales=12000000,
        annual_variable_cost=7200000, annual_operating_cashflow=4798800, unit_cost_floor=12.002)
    result = estimate(response)
    assert result["calculation_source"] == "llm_calculated"
    assert result["calculations"]["monthly_saleable_capacity"] == 150000
