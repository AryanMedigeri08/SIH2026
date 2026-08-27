"""
pricing_engine.py — Phase 2, Udyam Saathi

Blueprint §2.5 (Phase 2 Step 2.5): unit cost floor derived from the cost stack
(EMI + Working Capital outlay + Living/subsistence draw), divided by expected
monthly output units, then adjusted for state CPI inflation to project forward
pricing so the DPR's price recommendation doesn't go stale between report
generation and actual bank disbursal / operations start.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict


DEFAULT_MONTHLY_LIVING_DRAW = 8000.0  # ₹, conservative rural promoter subsistence draw


@dataclass
class PricingResult:
    monthly_emi: float
    monthly_working_capital_outlay: float
    monthly_living_draw: float
    total_monthly_cost_stack: float
    expected_monthly_units: float
    unit_cost_floor: float
    cpi_inflation_pct: float
    projection_months: int
    cpi_adjusted_unit_price_floor: float
    recommended_selling_price_band_low: float
    recommended_selling_price_band_high: float

    def to_dict(self) -> dict:
        d = asdict(self)
        for k, v in d.items():
            if isinstance(v, float):
                d[k] = round(v, 2)
        return d


def compute_pricing(
    monthly_emi: float,
    monthly_working_capital_outlay: float,
    expected_monthly_units: float,
    cpi_inflation_pct: float,
    monthly_living_draw: float = DEFAULT_MONTHLY_LIVING_DRAW,
    projection_months: int = 12,
    target_margin_pct: float = 0.20,
) -> PricingResult:
    """
    unit_cost_floor = (EMI + WC_outlay + Living) / expected_monthly_units
    CPI-adjusted forward floor compounds the *monthly* CPI rate (annual % / 12)
    across `projection_months` so the floor reflects cost inflation by the time
    the unit is actually sold, not just at report-generation time.
    Recommended selling band = floor scaled by [1.0, 1+target_margin] over the
    CPI-adjusted floor, giving the bank/promoter a defensible range rather than
    a single number.
    """
    if expected_monthly_units <= 0:
        raise ValueError("expected_monthly_units must be > 0")
    if monthly_emi < 0 or monthly_working_capital_outlay < 0 or monthly_living_draw < 0:
        raise ValueError("cost components cannot be negative")

    total_cost_stack = monthly_emi + monthly_working_capital_outlay + monthly_living_draw
    unit_cost_floor = total_cost_stack / expected_monthly_units

    monthly_cpi_rate = (cpi_inflation_pct / 100.0) / 12.0
    cpi_adjusted_floor = unit_cost_floor * ((1 + monthly_cpi_rate) ** projection_months)

    band_low = cpi_adjusted_floor  # breakeven floor
    band_high = cpi_adjusted_floor * (1 + target_margin_pct)

    return PricingResult(
        monthly_emi=monthly_emi,
        monthly_working_capital_outlay=monthly_working_capital_outlay,
        monthly_living_draw=monthly_living_draw,
        total_monthly_cost_stack=total_cost_stack,
        expected_monthly_units=expected_monthly_units,
        unit_cost_floor=unit_cost_floor,
        cpi_inflation_pct=cpi_inflation_pct,
        projection_months=projection_months,
        cpi_adjusted_unit_price_floor=cpi_adjusted_floor,
        recommended_selling_price_band_low=band_low,
        recommended_selling_price_band_high=band_high,
    )


if __name__ == "__main__":
    result = compute_pricing(
        monthly_emi=9500, monthly_working_capital_outlay=15000,
        expected_monthly_units=780, cpi_inflation_pct=5.2,
    )
    print(result.to_dict())
