"""Validate an LLM's explicit capacity-to-saleable-unit conversion.

No product recipes or capacity-string parsers live here. Numeric relationships
are checked, while accepted quantities and conversions remain model outputs.
"""
from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .llm_capacity import CalculationUnit


class ProductionConversion(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    business_model: Literal["manufacturing", "retail", "service", "storage"]
    capacity_basis: Literal["raw_input", "finished_output", "retail_supply", "service_time", "service_jobs", "storage_stock"]
    saleable_unit_definition: str = Field(min_length=12, max_length=350,
        description="Exact product portion or service/billing scope represented by ONE output unit, e.g. one 100 ml cup of ice cream.")
    saleable_unit_quantity: float = Field(gt=0, le=1e9,
        description="Physical content per ONE output unit in saleable_unit_measure; a 100 ml cup contains 0.1 litres, not 100 litres or 1 litre.")
    saleable_unit_measure: CalculationUnit = Field(
        description="Physical content measure, e.g. litres for a cup of ice cream, kg for a bag of flour, hours for a repair job. Do not put cups/pieces here when their content is a liquid or solid.")
    billing_period: Literal["item", "job", "hour", "day", "month", "cycle"]
    capacity_units_per_output_unit: float = Field(gt=0, le=1e9,
        description="Machine capacity units required for ONE sold unit, before utilization/losses. For raw_input this must equal values.input_units_per_output_unit exactly.")
    working_days_per_month: float = Field(gt=0, le=31,
        description="The exact day count used to obtain capacity.monthly_quantity from its daily/hourly rate; do not use a second different monthly schedule.")
    working_hours_per_day: float = Field(gt=0, le=24)
    batches_per_day: float = Field(gt=0, le=1e6)
    storage_cycles_per_month: float = Field(gt=0, le=1000)
    seasonality_factor: float = Field(gt=0, le=1)
    conversion_basis: str = Field(min_length=20, max_length=1500)


def validate_conversion(conversion: ProductionConversion, capacity, values) -> None:
    """Reject undefined portions, double conversions and inconsistent schedules."""
    def check(actual, expected, reason):
        if not math.isclose(actual, expected, rel_tol=.0001, abs_tol=.00001):
            raise ValueError(f"{reason} (returned {actual:.12g}; expected {expected:.12g} from the supplied factors)")

    d = conversion.working_days_per_month
    h = conversion.working_hours_per_day
    multipliers = {"minute": 60 * h * d, "hour": h * d, "day": d,
        "month": 1, "year": 1 / 12, "batch": conversion.batches_per_day * d, "stock": 1}
    if capacity.period in multipliers:
        check(capacity.monthly_quantity, capacity.quantity * multipliers[capacity.period],
            "capacity.monthly_quantity must match interpreted quantity, period and conversion working schedule; do not apply yield/utilization here")
    permitted = {"manufacturing": {"raw_input", "finished_output"}, "retail": {"retail_supply"},
        "service": {"service_time", "service_jobs"}, "storage": {"storage_stock"}}
    if conversion.capacity_basis not in permitted[conversion.business_model]:
        raise ValueError("Use the capacity basis belonging to the actual business model")
    if conversion.capacity_basis == "storage_stock":
        if capacity.period != "stock" or capacity.capacity_kind != "storage":
            raise ValueError("Storage starts from physical stock capacity, not invented daily throughput")
        billing_cycles = {"month": 1, "day": d, "hour": d * h}
        if conversion.billing_period not in {"month", "day", "hour", "cycle"}:
            raise ValueError("Storage needs an explicit month/day/hour/cycle billing period")
        if conversion.billing_period in billing_cycles:
            check(conversion.storage_cycles_per_month, billing_cycles[conversion.billing_period],
                "Storage cycles must match the billing period; do not multiply stock turnover into kg-month revenue")
    elif conversion.storage_cycles_per_month != 1:
        raise ValueError("storage_cycles_per_month must be 1 outside storage")
    if conversion.capacity_basis == "raw_input":
        if capacity.unit != values.input_unit:
            raise ValueError("Raw-input capacity must use the same normalized unit as raw-material costs")
        check(conversion.capacity_units_per_output_unit, values.input_units_per_output_unit,
            "For raw-input machinery, capacity conversion and input recipe must agree")
    if conversion.capacity_basis in {"finished_output", "retail_supply", "service_jobs"} and capacity.unit == values.output_unit:
        check(conversion.capacity_units_per_output_unit, 1,
            "Capacity already measured in the sold unit must not receive a second input-yield conversion")
    if conversion.capacity_basis == "service_time" and capacity.unit != "hours":
        raise ValueError("Service-time capacity must be normalized to available staff/equipment hours")
    if conversion.capacity_basis in {"finished_output", "service_time", "storage_stock"} and capacity.unit == conversion.saleable_unit_measure:
        check(conversion.capacity_units_per_output_unit, conversion.saleable_unit_quantity,
            "The portion/job/storage billing size must agree with capacity_units_per_output_unit")
    if values.output_unit in {"kg", "litres", "hours", "metres", "square_metres"}:
        if conversion.saleable_unit_measure != values.output_unit:
            raise ValueError("A price per kg/litre/hour/metre must define one of that exact unit")
        check(conversion.saleable_unit_quantity, 1, "Price per canonical output unit must refer to exactly one unit; use a count output unit for packs")
    if values.output_unit in {"pieces", "units", "cups", "bags", "boxes"} and values.input_unit in {"kg", "litres"}:
        if conversion.saleable_unit_measure not in {"kg", "litres"}:
            raise ValueError("Define the weight/volume of each sold piece, cup, pack, bag or box")
    # This legacy field remains available to callers, expressed as equivalent
    # raw inputs for the rated output. It is not the machinery capacity unit.
    check(values.rated_monthly_input_units,
        capacity.monthly_quantity / conversion.capacity_units_per_output_unit * values.input_units_per_output_unit * conversion.storage_cycles_per_month,
        "rated_monthly_input_units must be equivalent input requirements for the normalized rated output, before utilization/losses")
