"""Explicit test-only conversion assumptions; these are not market estimates."""


def raw_input_conversion(values):
    return dict(business_model="manufacturing", capacity_basis="raw_input",
        saleable_unit_definition=f"1 {values['output_unit']} of the finished test product",
        saleable_unit_quantity=1, saleable_unit_measure=values["output_unit"],
        billing_period="item",
        capacity_units_per_output_unit=values["input_units_per_output_unit"],
        working_days_per_month=25, working_hours_per_day=8, batches_per_day=1,
        storage_cycles_per_month=1, seasonality_factor=1,
        conversion_basis="Test-only recipe: explicit input units per sold output unit, 25 working days/month.")


def uniform_price_mix(values):
    price = values["selling_price_inr"]
    return dict(output_unit=values["output_unit"], reference_selling_price_inr=price,
        sales_mix=[dict(segment="Uniform test price", quantity_share=1, quoted_price_inr=price,
            output_units_per_quote=1, discount_pct=0, realized_unit_price_inr=price)],
        basis="Synthetic uniform-price fixture: all sold units receive the same net price.")


def business_demand_fixture(values, calculations, days=25):
    """Keep established regression numbers; this is synthetic, not market evidence."""
    demand = calculations["monthly_local_demand_units"]
    capacity = calculations["monthly_saleable_capacity"]
    scenarios = {}
    for name, factor in (("conservative", .7), ("base", 1), ("optimistic", 1.3)):
        count = demand * factor
        def inp(role, value, units):
            return dict(role=role, value=value, units=units, reference_period="annual_average_month",
                source_kind="scenario_assumption", source="Synthetic regression fixture, not a verified benchmark",
                evidence_path=None, confidence="low", reasoning="Explicit synthetic assumption to preserve the established dimensional regression case.")
        sold = min(count, capacity)
        scenarios[name] = dict(inputs=[inp("active_buyers", count, "people"),
            inp("transactions_per_buyer", 1, "transactions/buyer/month"), inp("units_per_transaction", 1, "output_units/transaction")],
            monthly_demand_units=count, monthly_active_buyers=count, monthly_transactions=count,
            realized_monthly_units=sold, daily_unit_sales=sold/days,
            monthly_revenue_inr=sold*values["selling_price_inr"], capacity_utilization_pct=sold/capacity*100)
    return dict(industry="Synthetic test enterprise", business_model="B2C direct local sales",
        product_service=values["product"], target_customer="Already captured active business customers in a synthetic fixture",
        buyer_base="people", location="Synthetic test catchment", maturity="Startup scenario", sales_channel="Direct sales",
        buying_cycle="Monthly business purchases in this synthetic test", acquisition_constraints="Customer counts are synthetic scenarios, not observed demand",
        method="customer_purchases", output_unit=values["output_unit"], period="annual_average_month", forecast_month=None,
        equation_with_units="active business buyers [people] * transactions/buyer/month * output units/transaction",
        method_reason="Direct active-customer demand is used for this synthetic regression; it is not a claim about the actual industry.",
        effective_monthly_capacity=capacity, scenarios=scenarios, category_demand=None, independent_cross_check=None,
        reconciliation="No independent research is available in this test fixture; a scenario range retains established base numbers.",
        uncertainty_drivers=["Synthetic active customer counts"], warnings=["Synthetic customer counts need real market evidence"], limitations=["No external research; synthetic scenario only"],
        missing_data=["Observed business transactions"], reality_review="Synthetic demand has an explicit buyer and transaction definition; physical capacity independently caps sales.", reality_reexamined=True, provisional=True)
