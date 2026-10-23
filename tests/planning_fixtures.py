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
