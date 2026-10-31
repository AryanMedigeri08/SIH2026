"""
financial.py — REST API Router for Standalone Deterministic Financial Calculators.
Includes Smart Turnover Sizing, Quarterly Amortization, and Machinery Schedule endpoints.
"""

from __future__ import annotations
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Query

try:
    from app.core.financial_calculator import (
        emi_with_moratorium, working_capital_estimate, compute_dscr, compute_bounded_dscr,
        rank_eligible_schemes, estimate_smart_turnover, calculate_quarterly_amortization,
    )
    from app.core.machinery_engine import extract_contextual_machinery
    from app.models.schemas import FinancialCalcRequest, FinancialCalcResponse
except ImportError:
    from backend.app.core.financial_calculator import (
        emi_with_moratorium, working_capital_estimate, compute_dscr, compute_bounded_dscr,
        rank_eligible_schemes, estimate_smart_turnover, calculate_quarterly_amortization,
    )
    from backend.app.core.machinery_engine import extract_contextual_machinery
    from backend.app.models.schemas import FinancialCalcRequest, FinancialCalcResponse

router = APIRouter(prefix="/financial", tags=["Financial Calculators"])


@router.post("/calculate", response_model=FinancialCalcResponse)
async def calculate_financial_summary(req: FinancialCalcRequest):
    """
    Executes standalone deterministic financial calculations:
    Multi-scheme ranking, net financial benefit, EMI amortization with moratorium,
    working capital requirement, and Debt Service Coverage Ratio (DSCR).
    Supports direct Available Margin Money input, Smart Turnover Sizing,
    and Quarterly Amortization Schedules.
    """
    try:
        # 1. Determine Project Cost from Available Margin if not directly given
        promoter_pct = 0.05 if req.promoter_category.lower() != "general" else 0.10
        if (req.project_cost is None or req.project_cost <= 0) and req.available_margin_capital:
            project_cost = float(req.available_margin_capital) / promoter_pct
        else:
            project_cost = float(req.project_cost or 1000000.0)

        margin_capital = float(req.available_margin_capital) if req.available_margin_capital else (project_cost * promoter_pct)

        # 2. Scheme Auto-Selection Tier
        # Logic A: <= 1.40 Lakh -> Micro Finance Scheme (6.5%, 3-yr tenure, 3-mo moratorium)
        # Logic B: > 1.40 Lakh to <= 50.00 Lakh -> Term Loan Scheme (8.0%, 7-yr tenure, 6-mo moratorium)
        if project_cost <= 140000:
            default_rate = 6.5
            default_tenure = 3.0
            default_morat = 3
        elif project_cost <= 5000000:
            default_rate = 8.0
            default_tenure = 7.0
            default_morat = 6
        else:
            default_rate = 9.5
            default_tenure = 7.0
            default_morat = 6

        tenure_years = req.tenure_years if req.tenure_years and req.tenure_years > 0 else default_tenure
        moratorium_months = req.moratorium_months if req.moratorium_months is not None else default_morat
        interest_rate = req.interest_rate_pct if req.interest_rate_pct and req.interest_rate_pct > 0 else default_rate

        # 3. Multi-Scheme Ranking
        ranked = rank_eligible_schemes(
            project_cost=project_cost,
            business_category=req.business_category,
            sector=req.sector,
            promoter_category=req.promoter_category,
            is_rural=req.is_rural,
            tenure_years=tenure_years,
            default_bank_interest_rate_pct=interest_rate,
            moratorium_months=moratorium_months,
        )
        top_scheme = next((r for r in ranked if r.eligible), ranked[0])

        promoter_margin = project_cost * promoter_pct
        loan_principal = max(project_cost - top_scheme.subsidy_grant_amount - promoter_margin, 0.0)

        amort = emi_with_moratorium(
            principal=max(loan_principal, 1.0),
            annual_rate_pct=top_scheme.effective_interest_rate_pct or interest_rate,
            tenure_years=tenure_years,
            moratorium_months=moratorium_months,
        )

        # 4. Smart Turnover Determination
        premise_type = (req.premise_type or "rented").lower()
        actual_rent = 0.0 if premise_type in ("owned", "panchayat") else (req.monthly_rent if req.monthly_rent is not None else None)

        smart_turnover = estimate_smart_turnover(
            project_cost=project_cost,
            sector=req.sector,
            loan_principal=loan_principal,
            annual_rate_pct=top_scheme.effective_interest_rate_pct or interest_rate,
            tenure_years=tenure_years,
            moratorium_months=moratorium_months,
            premise_type=premise_type,
            monthly_rent=actual_rent,
        )

        annual_turnover = float(req.annual_turnover) if (req.annual_turnover and req.annual_turnover > 0) else smart_turnover.recommended_annual_turnover
        wc = working_capital_estimate(annual_turnover, req.sector)

        # Operating margin & Rent accounting for DSCR
        op_margin = smart_turnover.operating_margin_pct / 100.0
        monthly_profit = (annual_turnover * op_margin) / 12.0
        monthly_noi = max(monthly_profit - (smart_turnover.monthly_rent_deducted or 0.0), 0.0)
        dscr_res = compute_dscr(monthly_noi, amort.monthly_emi)

        # 5. Quarterly Repayment Amortization Schedule
        q_amort = calculate_quarterly_amortization(
            principal=max(loan_principal, 1.0),
            annual_rate_pct=top_scheme.effective_interest_rate_pct or interest_rate,
            tenure_years=tenure_years,
            moratorium_months=moratorium_months,
        )

        # 6. Contextual Machinery Schedule (55% budget)
        machinery_budget = project_cost * 0.55
        machinery_sched = extract_contextual_machinery(
            enterprise_name=f"{req.sector.title()} Enterprise",
            business_category=req.business_category,
            sector=req.sector,
            allocated_machinery_budget=machinery_budget,
            use_ai=False,  # instant response for standalone calculator
        )

        return FinancialCalcResponse(
            project_cost=round(project_cost, 2),
            available_margin_capital=round(margin_capital, 2),
            top_scheme_id=top_scheme.scheme_id,
            top_scheme_name=top_scheme.full_name,
            subsidy_grant_amount=round(top_scheme.subsidy_grant_amount, 2),
            loan_principal=round(loan_principal, 2),
            monthly_emi=round(amort.monthly_emi, 2),
            total_interest_payable=round(amort.total_interest_payable, 2),
            total_repayment=round(amort.total_repayment, 2),
            working_capital_required=round(wc.working_capital_required, 2),
            dscr=round(dscr_res.dscr, 2),
            dscr_verdict=dscr_res.verdict,
            dscr_classification=dscr_res.classification,
            ranked_schemes=[s.to_dict() for s in ranked[:5]],
            quarterly_installment=round(q_amort.quarterly_installment, 2),
            quarterly_schedule=[e.to_dict() for e in q_amort.schedule],
            smart_turnover_breakdown=smart_turnover.to_dict(),
            machinery_schedule=machinery_sched.to_dict(),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/machinery-schedule")
async def get_machinery_for_enterprise(
    sector: str = Query("dairy", description="Sector name"),
    project_cost: float = Query(1000000.0, gt=0, description="Project Cost in INR"),
    enterprise_name: str = Query("Micro Enterprise", description="Commercial Name"),
    business_category: str = Query("manufacturing", description="Category"),
    additional_details: Optional[str] = Query(None, description="Promoter specifications"),
):
    """
    Returns itemized machinery & equipment Bill of Quantities (BoQ)
    scaled to the allocated 55% plant & machinery budget.
    """
    try:
        machinery_budget = project_cost * 0.55
        sched = extract_contextual_machinery(
            enterprise_name=enterprise_name,
            business_category=business_category,
            sector=sector,
            allocated_machinery_budget=machinery_budget,
            additional_details=additional_details,
            use_ai=True,
        )
        return sched.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
