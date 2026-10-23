"""One monthly repayment schedule and operating model for report and dashboard."""
from __future__ import annotations

from .financial_calculator import emi_with_moratorium


def project_cashflows(operations: dict, project_cost: float, principal: float,
                      interest_rate: float, tenure_years: float, moratorium_months: int,
                      cpi_pct: float, annual_noi_override: float | None = None) -> list[dict]:
    a = operations["assumptions"]["values"]
    amort = emi_with_moratorium(max(principal, 1), interest_rate, tenure_years, moratorium_months)
    balance = principal
    monthly_rate = interest_rate / 1200
    total_months = round(tenure_years * 12)
    depreciation_base = project_cost * .55
    rows = []
    for year in range(1, 6):
        idx = year - 1
        utilization = min(a["utilization"] + .05 * idx, 1.0)
        volume_factor = utilization / a["utilization"]
        # Sales grow only within the capacity and demand assumptions; no DSCR target.
        monthly_units = min(operations["monthly_sales_units"] * volume_factor,
                            operations["monthly_saleable_capacity"] / a["utilization"] * utilization,
                            (operations["monthly_local_demand_units"] + a["external_monthly_demand_units"]) * (1.02 ** idx))
        if operations["sales_source"] == "user_supplied":
            monthly_units = operations["monthly_sales_units"] * volume_factor
        revenue = monthly_units * a["selling_price_inr"] * 12 * (1.02 ** idx)
        cost_index = (1 + max(cpi_pct, -50) / 100) ** idx
        raw = monthly_units * a["input_units_per_output_unit"] * a["raw_material_cost_per_input_unit_inr"] * 12 * cost_index
        variable = monthly_units * a["other_variable_cost_per_output_unit_inr"] * 12 * cost_index
        fixed = operations["annual_fixed_cost"] * cost_index
        opex = raw + variable + fixed
        ebitda = revenue - opex
        if annual_noi_override is not None:
            ebitda = annual_noi_override * volume_factor
            opex = revenue - ebitda
            # Override replaces the expense estimate; keep component sums honest.
            raw, variable, fixed = 0, 0, opex
        interest = principal_due = 0.0
        for month in range(idx * 12 + 1, year * 12 + 1):
            if balance <= 0 or month > total_months:
                continue
            if month <= moratorium_months:
                balance += principal * monthly_rate
                continue
            monthly_interest = balance * monthly_rate
            payment = min(amort.monthly_emi, balance + monthly_interest)
            repayment = payment - monthly_interest
            balance = max(balance - repayment, 0)
            interest += monthly_interest
            principal_due += repayment
        depreciation = depreciation_base * .15
        depreciation_base -= depreciation
        pbt = ebitda - depreciation - interest
        tax = max(pbt, 0) * .15 if pbt > 250000 else 0
        pat = pbt - tax
        debt_service = principal_due + interest
        coverage_cashflow = pat + depreciation + interest
        rows.append(dict(year=year, capacity_utilization_pct=round(utilization * 100, 2),
                         gross_turnover=revenue, raw_materials_and_inputs=raw,
                         power_and_utilities=variable, wages_and_labor=0,
                         overheads_and_maintenance=fixed, total_operating_expenses=opex,
                         ebitda=ebitda, depreciation=depreciation, bank_interest=interest,
                         profit_before_tax=pbt, tax_provision=tax, profit_after_tax=pat,
                         cash_accruals=pat + depreciation, loan_principal_repayment=principal_due,
                         total_debt_service=debt_service,
                         annual_dscr=coverage_cashflow / debt_service if debt_service > 0 else 0))
    return [{key: round(value, 2) if isinstance(value, float) else value for key, value in row.items()} for row in rows]
