"""Quantity-weighted realized price, with a fixed-volume review comparison."""
from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field

from .llm_capacity import CalculationUnit


class PriceSegment(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    segment: str = Field(min_length=1, max_length=100)
    quantity_share: float = Field(gt=0, le=1, description="Share of sold output units, not share of revenue. All segments sum to 1.")
    quoted_price_inr: float = Field(ge=0, le=1e10)
    output_units_per_quote: float = Field(gt=0, le=1e9, description="Number of the SAME defined output unit in this quoted pack/job/billing quantity. Ten 100 ml cups = 10 output units, not one cup.")
    discount_pct: float = Field(ge=0, le=100)
    realized_unit_price_inr: float = Field(ge=0, le=1e8, description="quoted_price_inr / output_units_per_quote * (1 - discount_pct / 100).")


class AverageSellingPrice(BaseModel):
    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)
    output_unit: CalculationUnit
    reference_selling_price_inr: float = Field(gt=0, le=1e8,
        description="An undiscounted regular single price per the same defined output unit, for a comparison scenario only; not a claimed historical report price.")
    sales_mix: list[PriceSegment] = Field(min_length=1, max_length=8)
    basis: str = Field(min_length=20, max_length=1200)


def validate_average_price(pricing: AverageSellingPrice, output_unit: str, average_price: float) -> None:
    if pricing.output_unit != output_unit:
        raise ValueError("Pricing must use the same defined output unit as sales quantity and production conversion")
    if not math.isclose(sum(row.quantity_share for row in pricing.sales_mix), 1, abs_tol=1e-6):
        raise ValueError("Sales-mix quantity shares must sum to 1; do not average by revenue share or normalize incomplete weights")
    for row in pricing.sales_mix:
        expected = row.quoted_price_inr / row.output_units_per_quote * (1 - row.discount_pct / 100)
        if not math.isclose(row.realized_unit_price_inr, expected, rel_tol=.0001, abs_tol=.005):
            raise ValueError(f"{row.segment}: realized_unit_price_inr must equal quote / output units per quote after discount (expected {expected:.12g})")
    expected = sum(row.quantity_share * row.realized_unit_price_inr for row in pricing.sales_mix)
    if not math.isclose(average_price, expected, rel_tol=.0001, abs_tol=.005):
        raise ValueError(f"selling_price_inr must be the quantity-weighted average realized price (expected {expected:.12g})")


def single_price_fallback(price: float, output_unit: str) -> dict:
    return {"output_unit": output_unit, "reference_selling_price_inr": price,
        "sales_mix": [{"segment": "Indicative uniform price", "quantity_share": 1,
            "quoted_price_inr": price, "output_units_per_quote": 1, "discount_pct": 0,
            "realized_unit_price_inr": price}],
        "basis": "Single-price fallback; no validated sales-channel mix was available.",
        "source": "indicative_single_price"}


def weighted_price_fallback(pricing: AverageSellingPrice, output_unit: str) -> tuple[dict, float] | None:
    """Only after invalid model arithmetic: preserve valid quote/share assumptions."""
    if pricing.output_unit != output_unit or not math.isclose(sum(r.quantity_share for r in pricing.sales_mix), 1, abs_tol=1e-6):
        return None
    rows = [{**row.model_dump(), "realized_unit_price_inr": row.quoted_price_inr / row.output_units_per_quote * (1 - row.discount_pct / 100)} for row in pricing.sales_mix]
    if any(not math.isfinite(row["realized_unit_price_inr"]) or not 0 <= row["realized_unit_price_inr"] <= 1e8 for row in rows):
        return None
    average = sum(row["quantity_share"] * row["realized_unit_price_inr"] for row in rows)
    if not 0 < average <= 1e8:
        return None
    return {**pricing.model_dump(), "sales_mix": rows, "source": "llm_mix_with_indicative_arithmetic"}, average


def price_comparison(operations: dict, assumptions: dict) -> dict | None:
    """Isolate the effect of pricing, holding accepted sales volume constant.

    These are comparison scenarios, not replacement financial calculations or
    assertions about an earlier saved report. Explicit user sales are immutable.
    """
    pricing = assumptions.get("pricing") or {}
    if assumptions.get("evidence", {}).get("annual_sales_override") is not None or operations.get("sales_source") == "user_supplied":
        return None
    if pricing.get("source") not in {"llm_quantity_weighted", "llm_mix_with_indicative_arithmetic"}:
        return None
    quantity = operations["monthly_sales_units"]
    reference_price = pricing["reference_selling_price_inr"]
    reference_monthly = quantity * reference_price
    weighted_monthly = operations["monthly_gross_sales"]
    reference_annual = reference_monthly * 12
    return {"basis": "Same-volume reference-price scenario; not an earlier report or verified market quotation.",
        "monthly_sales_units": quantity, "reference_unit_price_inr": reference_price,
        "average_selling_price_inr": operations["selling_price_inr"],
        "reference_monthly_sales": round(reference_monthly, 2),
        "weighted_monthly_sales": weighted_monthly,
        "reference_annual_sales": round(reference_annual, 2),
        "weighted_annual_sales": operations["annual_sales"],
        "annual_sales_difference": round(operations["annual_sales"] - reference_annual, 2),
        "annual_sales_change_pct": round((weighted_monthly / reference_monthly - 1) * 100, 2) if reference_monthly else 0}
