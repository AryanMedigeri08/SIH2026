import pytest
from backend.app.core.financial_calculator import calculate_asset_driven_capital_structure

def test_sca_capital_structure_general_category_deficit():
    # User has INR 90,000 cash, but machinery costs INR 12,00,000
    res = calculate_asset_driven_capital_structure(
        machinery_cost=1200000.0,
        available_promoter_cash=90000.0,
        promoter_category="general",
        gender="male",
    )

    # 1. Total Outlay Anchor: 12,00,000 / 0.55 = 21,81,818 rounded to nearest 1,000 = 21,82,000
    assert abs(res.true_project_outlay - 2182000.0) < 1.0
    assert res.actual_machinery_cost == 1200000.0
    assert res.working_capital_and_ancillaries == 982000.0

    # 2. Statutory 10% Margin for General Category
    assert res.statutory_margin_pct == 0.10
    assert res.required_promoter_equity == 218200.0

    # 3. Deficit Detection
    assert res.is_equity_deficit is True
    # Gap: 2,18,200 - 90,000 = 1,28,200
    assert res.equity_gap == 128200.0

    # 4. SCA Soft Loan & Means of Finance Reconciliation
    assert res.sca_soft_loan_eligible_amount == 128200.0
    mof = res.means_of_finance
    total_financed = mof["promoter_cash_contribution"] + mof["sca_margin_soft_loan"] + mof["bank_term_loan"]
    assert abs(total_financed - res.true_project_outlay) < 1.0

    # 5. 4 Bridge Pathways
    assert len(res.bridge_options) == 4
    sca_pathway = next(p for p in res.bridge_options if p["pathway_id"] == "sca_margin_assistance")
    assert sca_pathway["feasible"] is True
    assert sca_pathway["amount_inr"] == 128200.0

    concession_pathway = next(p for p in res.bridge_options if p["pathway_id"] == "category_concession")
    assert concession_pathway["feasible"] is True
    # Savings: 10% - 5% = 1,09,100
    assert concession_pathway["amount_inr"] == 109100.0


def test_sca_capital_structure_special_category_5pct():
    # Women / SC / ST / OBC promoter with INR 90,000 cash and INR 12,00,000 machinery
    res = calculate_asset_driven_capital_structure(
        machinery_cost=1200000.0,
        available_promoter_cash=90000.0,
        promoter_category="women",
        gender="female",
    )

    # 5% statutory margin
    assert res.statutory_margin_pct == 0.05
    assert res.required_promoter_equity == 109100.0

    # Equity Gap shrinks from 1,28,200 to only 19,100
    assert res.equity_gap == 19100.0
    assert res.sca_soft_loan_eligible_amount == 19100.0


def test_sca_capital_structure_surplus_equity():
    # Promoter has INR 3,00,000 cash for INR 12,00,000 machinery
    res = calculate_asset_driven_capital_structure(
        machinery_cost=1200000.0,
        available_promoter_cash=300000.0,
        promoter_category="general",
        gender="male",
    )

    assert res.is_equity_deficit is False
    assert res.equity_gap == 0.0
    assert res.sca_soft_loan_eligible_amount == 0.0



def test_sca_soft_loan_emi_and_debt_servicing():
    # Teammate scenario: INR 10 Lakh project, INR 5.5L machinery, INR 90,000 cash in hand
    res = calculate_asset_driven_capital_structure(
        machinery_cost=550000.0,
        available_promoter_cash=90000.0,
        promoter_category="general",
        gender="male",
        target_project_cost=1000000.0,
        bank_interest_rate_pct=9.5,
        tenure_years=5.0,
        moratorium_months=6,
        monthly_noi=35000.0,
        sca_interest_rate_pct=3.0,
        sca_tenure_years=5.0,
        sca_moratorium_months=6,
    )

    assert abs(res.true_project_outlay - 1000000.0) < 1.0
    assert res.required_promoter_equity == 100000.0
    assert res.available_promoter_cash == 90000.0
    assert res.equity_gap == 10000.0
    assert res.is_equity_deficit is True
    assert res.sca_soft_loan_eligible_amount == 10000.0

    # SCA Soft Loan EMI (~INR 180-210/mo at 3% for 5 years)
    assert res.sca_monthly_emi > 0.0
    assert abs(res.sca_monthly_emi - 198.0) < 50.0

    # Bank Loan EMI (~INR 18,913/mo for INR 9L at 9.5% for 5 years with 6m moratorium)
    assert res.bank_monthly_emi > 15000.0

    # Total Debt Service
    assert abs(res.total_monthly_debt_service - (res.bank_monthly_emi + res.sca_monthly_emi)) < 0.05

    # Combined DSCR with INR 35,000 NOI
    expected_dscr = round(35000.0 / res.total_monthly_debt_service, 2)
    assert res.combined_dscr == expected_dscr
    assert res.combined_dscr >= 1.33
