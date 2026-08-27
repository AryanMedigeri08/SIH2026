"""
financial.py — REST API Router for Standalone Deterministic Financial Calculators.
"""

from __future__ import annotations
from typing import Optional, Any
from fastapi import APIRouter, HTTPException

from financial_calculator import (
    emi_with_moratorium, working_capital_estimate, compute_dscr, rank_eligible_schemes,
)
from app.models.schemas import FinancialCalcRequest, FinancialCalcResponse

router = APIRouter(prefix="/financial", tags=["Financial Calculators"])


@router.post("/calculate", response_model=FinancialCalcResponse)
async def calculate_financial_summary(req: FinancialCalcRequest):
    """
    Executes standalone deterministic financial calculations:
    Multi-scheme ranking, net financial benefit, EMI amortization with moratorium,
    working capital requirement, and Debt Service Coverage Ratio (DSCR).
    """
    try:
        ranked = rank_eligible_schemes(
            project_cost=req.project_cost,
            business_category=req.business_category,
            sector=req.sector,
            promoter_category=req.promoter_category,
            is_rural=req.is_rural,
            tenure_years=req.tenure_years,
            default_bank_interest_rate_pct=req.interest_rate_pct,
            moratorium_months=req.moratorium_months,
        )
        top_scheme = next((r for r in ranked if r.eligible), ranked[0])

        promoter_pct = 0.05 if req.promoter_category.lower() != "general" else 0.10
        promoter_margin = req.project_cost * promoter_pct
        loan_principal = max(req.project_cost - top_scheme.subsidy_grant_amount - promoter_margin, 0.0)

        amort = emi_with_moratorium(
            principal=max(loan_principal, 1.0),
            annual_rate_pct=top_scheme.effective_interest_rate_pct,
            tenure_years=req.tenure_years,
            moratorium_months=req.moratorium_months,
        )

        wc = working_capital_estimate(req.annual_turnover, req.sector)
        monthly_noi = req.annual_turnover * 0.30 / 12  # Standard 30% gross margin assumption
        dscr_res = compute_dscr(monthly_noi, amort.monthly_emi)

        return FinancialCalcResponse(
            project_cost=req.project_cost,
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
            ranked_schemes=[s.to_dict() for s in ranked[:5]],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
