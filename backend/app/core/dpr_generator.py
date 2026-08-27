"""
dpr_generator.py — Phase 5, Udyam Saathi

Tier 3 / Phase 5: Bank-Ready Detailed Project Report (DPR) Generator.
Transforms multi-tier feasibility analysis (Tier 1 Math + Tier 2 ML + Tier 3 AI Synthesis)
into an official 7-Section Bank Credit Appraisal Document matching Scheduled Commercial
Bank and District Industries Centre (DIC) standards for PMEGP, PMFME, MUDRA & Stand-Up India.

Official 7-Section Structure:
    1. Header & Enterprise Profile (DPR ID, Promoter Demographics, LGD Geography)
    2. Capital Outlay & Means of Finance (Exact rupee reconciliation: Outlay == Means of Finance)
    3. Financial & Cash Flow Projections (5-Year Horizon with Capacity Slabs, EBITDA, PAT, DSCR)
    4. Multi-Scheme Optimization & Subsidy Matrix (Top Ranked Schemes by Net Benefit)
    5. Machine Learning Viability & Risk Assessment (XGBoost 10-D Probabilities & Factor Drivers)
    6. Grounded SWOT & 8-Point Quantified Risk Mitigation Table (Rupee buffers & Audited Sources)
    7. Statutory Bank Submission Document Checklist (Category & Sector-specific Mandatory Docs)

Exports Supported:
    - Structured Pydantic v2 Model / JSON dictionary
    - Formatted Markdown Bank Memorandum
    - Print-Ready HTML Document
"""

from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from typing import Optional, Union, Any
from pathlib import Path
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Pydantic v2 Models for Strict Serialization & REST API compatibility
# ---------------------------------------------------------------------------

class EnterpriseProfileHeader(BaseModel):
    dpr_reference_id: str = Field(..., description="Unique Bank DPR Reference Number")
    report_date: str = Field(..., description="Date of Feasibility Appraisal (ISO / Formatted)")
    enterprise_name: str
    constitution: str = Field("Sole Proprietorship", description="Legal Constitution of Enterprise")
    sector: str
    business_category: str = Field(..., description="manufacturing | service")
    promoter_name: str = "Enterprise Promoter"
    promoter_category: str = Field("general", description="general | sc | st | obc | women | artisan | women_shg")
    gender: str = "Unspecified"
    target_state: str
    target_district: str
    target_block: str = "N/A"
    target_village: str = "N/A"
    is_rural: bool = True
    catchment_projected_population: int = 0
    nodal_lending_agency: str = "Scheduled Commercial Bank / District Industries Centre (DIC)"


class CapitalOutlayItem(BaseModel):
    item_name: str
    percentage_of_outlay: float
    amount_inr: float
    description: str


class CapitalOutlayTable(BaseModel):
    plant_and_machinery: CapitalOutlayItem
    electrification_and_site_works: CapitalOutlayItem
    initial_working_capital_reserve: CapitalOutlayItem
    contingency_and_pre_operative: CapitalOutlayItem
    total_capital_outlay: float


class MeansOfFinanceTable(BaseModel):
    promoter_margin_amount: float
    promoter_margin_pct: float
    capital_subsidy_amount: float
    capital_subsidy_pct: float
    subsidy_scheme_name: str
    bank_term_loan_amount: float
    bank_term_loan_pct: float
    total_means_of_finance: float
    reconciliation_balanced: bool = True


class FinancialProjectionYear(BaseModel):
    year: int
    capacity_utilization_pct: float
    gross_turnover: float
    raw_materials_and_inputs: float
    power_and_utilities: float
    wages_and_labor: float
    overheads_and_maintenance: float
    total_operating_expenses: float
    ebitda: float
    depreciation: float
    bank_interest: float
    profit_before_tax: float
    tax_provision: float
    profit_after_tax: float
    cash_accruals: float
    loan_principal_repayment: float
    total_debt_service: float
    annual_dscr: float


class FiveYearFinancialHorizon(BaseModel):
    projection_years: list[FinancialProjectionYear]
    average_dscr: float
    dscr_benchmark_met: bool
    break_even_point_pct: float
    recommended_unit_price_floor: float


class SchemeOptimizationEntry(BaseModel):
    rank: int
    scheme_id: str
    full_name: str
    eligible: bool
    ineligibility_reason: Optional[str] = None
    subsidy_grant_amount: float
    effective_interest_rate_pct: float
    total_interest_payable: float
    net_financial_benefit: float
    collateral_free: bool
    administering_body: str = "Government of India / Nodal Bank"


class MLViabilitySection(BaseModel):
    verdict: str  # SUITABLE | CAUTION | RECONSIDER
    confidence_pct: float
    class_probabilities: dict[str, float]
    feature_vector_audit: dict[str, float]
    top_positive_factors: list[str]
    top_risk_factors: list[str]
    model_version: str


class SWOTQuadrantItem(BaseModel):
    text: str
    data_source: str


class SWOTSection(BaseModel):
    strengths: list[SWOTQuadrantItem]
    weaknesses: list[SWOTQuadrantItem]
    opportunities: list[SWOTQuadrantItem]
    threats: list[SWOTQuadrantItem]


class RiskMitigationItem(BaseModel):
    risk_id: str
    title: str
    score: float
    severity: str
    basis: str
    mitigation: str
    rupee_buffer: Optional[float] = None
    data_source: str


class RiskSection(BaseModel):
    risk_points: list[RiskMitigationItem]
    average_risk_score: float
    overall_severity: str
    high_or_severe_risk_count: int


class StatutoryChecklistItem(BaseModel):
    document_code: str
    document_name: str
    category_requirement: str  # "Universal Mandatory" | "Social Category Specific" | "Sector Specific"
    issuing_authority: str
    is_mandatory: bool
    notes: str


class BankDPRDocument(BaseModel):
    dpr_version: str = "2.0"
    generated_at_utc: str
    section_1_header_and_profile: EnterpriseProfileHeader
    section_2_capital_outlay_and_finance: dict[str, Any]
    section_3_financial_projections: FiveYearFinancialHorizon
    section_4_scheme_optimization: list[SchemeOptimizationEntry]
    section_5_ml_viability_appraisal: MLViabilitySection
    section_6_swot_and_risk_matrix: dict[str, Any]
    section_7_statutory_checklist: list[StatutoryChecklistItem]
    tier_3_ai_synthesis: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


# ---------------------------------------------------------------------------
# 5-Year Financial Horizon Calculator (Standard Banking Formulas)
# ---------------------------------------------------------------------------
def _compute_5yr_projections(
    base_annual_turnover: float,
    project_cost: float,
    loan_principal: float,
    annual_interest_rate_pct: float,
    tenure_years: float,
    moratorium_months: int,
    sector: str,
    cpi_inflation_pct: float,
    unit_price_floor: float,
) -> FiveYearFinancialHorizon:
    """
    Computes a deterministic 5-Year Cash Flow Projection using standard Scheduled
    Commercial Bank appraisal standards:
      - Capacity Utilization: Y1: 60%, Y2: 70%, Y3: 80%, Y4: 85%, Y5: 90%
      - Inflation Escalation: 4% p.a. on expenses
      - Depreciation: 15% on Plant & Machinery (55% of project cost)
      - Loan Amortization: Equal principal repayment over tenure
    """
    capacity_slabs = [0.60, 0.70, 0.80, 0.85, 0.90]
    plant_machinery_cost = project_cost * 0.55
    depreciation_rate = 0.15

    # Sector cost assumptions (% of revenue at 100% capacity)
    sector_lower = sector.lower()
    if sector_lower in ("dairy", "food_processing"):
        raw_mat_ratio = 0.62
        power_ratio = 0.05
        labor_ratio = 0.08
        overhead_ratio = 0.04
    elif sector_lower in ("apparel", "tailoring", "artisan_trades", "artisan"):
        raw_mat_ratio = 0.45
        power_ratio = 0.04
        labor_ratio = 0.18
        overhead_ratio = 0.05
    elif sector_lower in ("repair", "service"):
        raw_mat_ratio = 0.25
        power_ratio = 0.06
        labor_ratio = 0.28
        overhead_ratio = 0.06
    else:
        raw_mat_ratio = 0.52
        power_ratio = 0.05
        labor_ratio = 0.12
        overhead_ratio = 0.05

    # Principal repayment per year (post moratorium)
    repay_tenure = max(tenure_years - (moratorium_months / 12), 1.0)
    annual_principal = loan_principal / min(repay_tenure, 5.0) if loan_principal > 0 else 0.0

    years_data: list[FinancialProjectionYear] = []
    remaining_loan = loan_principal
    machinery_wdv = plant_machinery_cost

    for yr_idx, cap_pct in enumerate(capacity_slabs, start=1):
        # Revenue scaled to capacity utilization and modest annual price indexation (2%)
        price_index = (1 + 0.02) ** (yr_idx - 1)
        gross_rev = base_annual_turnover * (cap_pct / 0.70) * price_index

        # Expenses scaled to volume and CPI inflation
        cost_index = (1 + (cpi_inflation_pct / 100 * 0.5)) ** (yr_idx - 1)
        raw_mat = gross_rev * raw_mat_ratio * cost_index
        power = gross_rev * power_ratio * cost_index
        labor = gross_rev * labor_ratio * cost_index
        overheads = gross_rev * overhead_ratio * cost_index

        total_opex = raw_mat + power + labor + overheads
        ebitda = max(gross_rev - total_opex, 0.0)

        # Depreciation (Written Down Value)
        depr = machinery_wdv * depreciation_rate
        machinery_wdv = max(machinery_wdv - depr, 0.0)

        # Bank Interest on opening loan balance
        interest = remaining_loan * (annual_interest_rate_pct / 100.0) if remaining_loan > 0 else 0.0
        principal_due = min(annual_principal, remaining_loan) if remaining_loan > 0 else 0.0
        remaining_loan = max(remaining_loan - principal_due, 0.0)

        pbt = max(ebitda - depr - interest, 0.0)
        tax = pbt * 0.15 if pbt > 250000 else 0.0  # Concessional micro enterprise slab
        pat = pbt - tax
        cash_accruals = pat + depr

        total_debt_service = principal_due + interest
        if total_debt_service > 0:
            annual_dscr = (pat + depr + interest) / total_debt_service
        else:
            annual_dscr = 3.50

        years_data.append(FinancialProjectionYear(
            year=yr_idx,
            capacity_utilization_pct=round(cap_pct * 100, 1),
            gross_turnover=round(gross_rev, 2),
            raw_materials_and_inputs=round(raw_mat, 2),
            power_and_utilities=round(power, 2),
            wages_and_labor=round(labor, 2),
            overheads_and_maintenance=round(overheads, 2),
            total_operating_expenses=round(total_opex, 2),
            ebitda=round(ebitda, 2),
            depreciation=round(depr, 2),
            bank_interest=round(interest, 2),
            profit_before_tax=round(pbt, 2),
            tax_provision=round(tax, 2),
            profit_after_tax=round(pat, 2),
            cash_accruals=round(cash_accruals, 2),
            loan_principal_repayment=round(principal_due, 2),
            total_debt_service=round(total_debt_service, 2),
            annual_dscr=round(annual_dscr, 2),
        ))

    avg_dscr = sum(y.annual_dscr for y in years_data) / len(years_data)
    dscr_ok = avg_dscr >= 1.33
    bep_pct = round((total_opex + interest + depr) / gross_rev * 100, 1) if gross_rev > 0 else 55.0

    return FiveYearFinancialHorizon(
        projection_years=years_data,
        average_dscr=round(avg_dscr, 2),
        dscr_benchmark_met=dscr_ok,
        break_even_point_pct=min(bep_pct, 85.0),
        recommended_unit_price_floor=round(unit_price_floor, 2),
    )


# ---------------------------------------------------------------------------
# Statutory Document Checklist Compiler
# ---------------------------------------------------------------------------
def _compile_statutory_checklist(
    scheme_id: str,
    promoter_category: str,
    sector: str,
    business_category: str,
    project_cost: float,
) -> list[StatutoryChecklistItem]:
    """
    Builds the official bank submission document checklist tailored to the scheme,
    promoter social category, and enterprise sector.
    """
    checklist: list[StatutoryChecklistItem] = []

    # 1. Universal KYC and Enterprise Basics
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-KYC-01",
        document_name="Promoter Identity & Address Proof (Aadhaar & PAN Card)",
        category_requirement="Universal Mandatory",
        issuing_authority="UIDAI / Income Tax Department",
        is_mandatory=True,
        notes="Self-attested copies of Aadhaar Card and PAN Card of the main promoter.",
    ))
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-REG-02",
        document_name="Udyam MSME Registration Certificate",
        category_requirement="Universal Mandatory",
        issuing_authority="Ministry of MSME (Udyam Portal)",
        is_mandatory=True,
        notes="Online Udyam registration acknowledgement showing enterprise category.",
    ))
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-LOC-03",
        document_name="Proof of Worksite / Land Ownership or Lease Deed",
        category_requirement="Universal Mandatory",
        issuing_authority="Gram Panchayat / Revenue Authority / Landlord",
        is_mandatory=True,
        notes="Registered lease deed (minimum 5-year tenure) or Khatiyan / Land tax receipt.",
    ))
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-QUO-04",
        document_name="Machinery & Equipment Quotations with GST Numbers",
        category_requirement="Universal Mandatory",
        issuing_authority="Authorized Machinery Suppliers / OEMs",
        is_mandatory=True,
        notes="Itemized commercial quotations from at least two reputable suppliers.",
    ))
    checklist.append(StatutoryChecklistItem(
        document_code="DOC-BNK-05",
        document_name="Bank Passbook / Statement (Last 6 Months)",
        category_requirement="Universal Mandatory",
        issuing_authority="Operating Bank Branch",
        is_mandatory=True,
        notes="Shows promoter's margin contribution capability and clean financial track record.",
    ))

    # 2. Scheme & Social Category Specifics
    cat_lower = promoter_category.lower()
    if cat_lower in ("sc", "st", "obc"):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-SOC-06",
            document_name="Social Category / Caste Certificate",
            category_requirement="Social Category Specific",
            issuing_authority="Tehsildar / Sub-Divisional Magistrate (SDM)",
            is_mandatory=True,
            notes=f"Mandatory for claiming special subsidy slabs under {scheme_id}.",
        ))
    if cat_lower in ("artisan", "artisan_trades"):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-ART-07",
            document_name="PM Vishwakarma Artisan Registration Card / Certificate",
            category_requirement="Social Category Specific",
            issuing_authority="Ministry of MSME / Skill Verification Officer",
            is_mandatory=True,
            notes="Required for fixed 5% interest subvention under PM Vishwakarma.",
        ))
    if cat_lower in ("women_shg", "shg"):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-SHG-08",
            document_name="NRLM / SRLM Women SHG Affiliation & Resolution Copy",
            category_requirement="Social Category Specific",
            issuing_authority="State Rural Livelihood Mission (SRLM)",
            is_mandatory=True,
            notes="Resolution passed by SHG members for availing enterprise credit.",
        ))

    # Educational qualification check for PMEGP
    if "PMEGP" in scheme_id and ((business_category == "manufacturing" and project_cost > 1000000) or
                                  (business_category == "service" and project_cost > 500000)):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-EDU-09",
            document_name="Minimum 8th Standard Pass Educational Certificate",
            category_requirement="Scheme Specific Mandatory",
            issuing_authority="Recognized School Board / Education Dept",
            is_mandatory=True,
            notes="Mandatory under PMEGP guidelines for project outlay exceeding ₹10L (Mfg) or ₹5L (Service).",
        ))

    # 3. Sector Specific Regulatory Clearances
    sec_lower = sector.lower()
    if sec_lower in ("dairy", "food_processing"):
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-FSS-10",
            document_name="FSSAI Basic Registration / Food Safety License",
            category_requirement="Sector Specific Regulatory",
            issuing_authority="Food Safety and Standards Authority of India (FSSAI)",
            is_mandatory=True,
            notes="Mandatory prior to commercial food/dairy processing and packaging operations.",
        ))
    if business_category == "manufacturing":
        checklist.append(StatutoryChecklistItem(
            document_code="DOC-PCB-11",
            document_name="State Pollution Control Board Consent (White / Green Category)",
            category_requirement="Sector Specific Regulatory",
            issuing_authority="State Pollution Control Board (SPCB)",
            is_mandatory=False,
            notes="Exempt for white category; green category requires standard online self-declaration.",
        ))

    return checklist


# ---------------------------------------------------------------------------
# Master Bank DPR Assembly Function
# ---------------------------------------------------------------------------
def build_bank_dpr(
    enterprise_name: str,
    business_category: str,
    sector: str,
    promoter_name: str,
    promoter_category: str,
    gender: str,
    state_name: str,
    district_name: str,
    block_name: str,
    village_name: str,
    is_rural: bool,
    project_cost: float,
    annual_turnover_estimate: float,
    tenure_years: float,
    moratorium_months: int,
    pop_projection: Any,
    tam_estimate: Any,
    msme_density: Any,
    ranked_schemes: list[Any],
    amortization: Any,
    dscr_result: Any,
    risk_points: list[Any],
    risk_verdict: dict[str, Any],
    swot_matrix: Any,
    pricing_result: Any,
    ml_prediction: Any,
    ai_synthesis: Any,
    constitution: str = "Sole Proprietorship",
) -> BankDPRDocument:
    """
    Compiles the complete 7-Section Bank DPR appraisal document.
    Ensures 100% financial and accounting balance reconciliation.
    """
    # 1. DPR Header & ID
    state_code_prefix = "".join(w[0] for w in state_name.split()[:2]).upper()
    dpr_ref = f"DPR-2026-{state_code_prefix}-{int(project_cost // 1000):04d}"
    now_iso = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC")

    profile = EnterpriseProfileHeader(
        dpr_reference_id=dpr_ref,
        report_date=now_iso,
        enterprise_name=enterprise_name,
        constitution=constitution,
        sector=sector,
        business_category=business_category,
        promoter_name=promoter_name,
        promoter_category=promoter_category,
        gender=gender,
        target_state=state_name,
        target_district=district_name,
        target_block=block_name,
        target_village=village_name,
        is_rural=is_rural,
        catchment_projected_population=pop_projection.projected_population,
        nodal_lending_agency="Scheduled Commercial Bank / DIC",
    )

    # 2. Capital Outlay Breakdown (100% standard allocation)
    cost_machinery = project_cost * 0.55
    cost_civil = project_cost * 0.15
    cost_wc = project_cost * 0.20
    cost_contingency = project_cost * 0.10

    outlay_table = CapitalOutlayTable(
        plant_and_machinery=CapitalOutlayItem(
            item_name="Plant, Machinery & Core Equipment",
            percentage_of_outlay=55.0,
            amount_inr=round(cost_machinery, 2),
            description="Primary processing machinery, tools, and technical apparatus",
        ),
        electrification_and_site_works=CapitalOutlayItem(
            item_name="Electrification, Installation & Site Works",
            percentage_of_outlay=15.0,
            amount_inr=round(cost_civil, 2),
            description="Power cabling, transformer connection, foundation, and fixtures",
        ),
        initial_working_capital_reserve=CapitalOutlayItem(
            item_name="Initial Working Capital Reserve",
            percentage_of_outlay=20.0,
            amount_inr=round(cost_wc, 2),
            description="Raw material inventory buffer and operating liquidity for launch",
        ),
        contingency_and_pre_operative=CapitalOutlayItem(
            item_name="Contingency & Pre-Operative Outlay",
            percentage_of_outlay=10.0,
            amount_inr=round(cost_contingency, 2),
            description="Trial run expenses, licensing, logistics contingency, and buffer",
        ),
        total_capital_outlay=round(project_cost, 2),
    )

    # Means of Finance (Promoter Margin + Subsidy Grant + Bank Loan == Outlay)
    top_scheme = next((r for r in ranked_schemes if r.eligible), ranked_schemes[0])
    subsidy_amt = top_scheme.subsidy_grant_amount
    subsidy_pct = (subsidy_amt / project_cost * 100) if project_cost > 0 else 0.0

    promoter_pct = 5.0 if promoter_category.lower() != "general" else 10.0
    promoter_margin_amt = project_cost * (promoter_pct / 100.0)

    bank_loan_amt = max(project_cost - subsidy_amt - promoter_margin_amt, 0.0)
    bank_loan_pct = (bank_loan_amt / project_cost * 100) if project_cost > 0 else 0.0

    means_of_finance = MeansOfFinanceTable(
        promoter_margin_amount=round(promoter_margin_amt, 2),
        promoter_margin_pct=round(promoter_pct, 1),
        capital_subsidy_amount=round(subsidy_amt, 2),
        capital_subsidy_pct=round(subsidy_pct, 1),
        subsidy_scheme_name=f"{top_scheme.scheme_id} ({top_scheme.full_name})",
        bank_term_loan_amount=round(bank_loan_amt, 2),
        bank_term_loan_pct=round(bank_loan_pct, 1),
        total_means_of_finance=round(promoter_margin_amt + subsidy_amt + bank_loan_amt, 2),
        reconciliation_balanced=abs((promoter_margin_amt + subsidy_amt + bank_loan_amt) - project_cost) < 1.0,
    )

    # 3. 5-Year Cash Flow Projections
    projections = _compute_5yr_projections(
        base_annual_turnover=annual_turnover_estimate,
        project_cost=project_cost,
        loan_principal=bank_loan_amt,
        annual_interest_rate_pct=top_scheme.effective_interest_rate_pct,
        tenure_years=tenure_years,
        moratorium_months=moratorium_months,
        sector=sector,
        cpi_inflation_pct=pricing_result.cpi_inflation_pct,
        unit_price_floor=pricing_result.cpi_adjusted_unit_price_floor,
    )

    # 4. Scheme Optimization Table (Top 5)
    scheme_entries: list[SchemeOptimizationEntry] = []
    for s in ranked_schemes[:5]:
        scheme_entries.append(SchemeOptimizationEntry(
            rank=s.rank,
            scheme_id=s.scheme_id,
            full_name=s.full_name,
            eligible=s.eligible,
            ineligibility_reason=s.ineligibility_reason,
            subsidy_grant_amount=round(s.subsidy_grant_amount, 2),
            effective_interest_rate_pct=round(s.effective_interest_rate_pct, 2),
            total_interest_payable=round(s.total_interest_payable, 2),
            net_financial_benefit=round(s.net_financial_benefit, 2),
            collateral_free=s.collateral_free,
        ))

    # 5. ML Viability Section
    ml_section = MLViabilitySection(
        verdict=ml_prediction.verdict,
        confidence_pct=round(ml_prediction.confidence_pct, 2),
        class_probabilities=ml_prediction.class_probabilities,
        feature_vector_audit=ml_prediction.feature_values,
        top_positive_factors=ml_prediction.top_positive_factors,
        top_risk_factors=ml_prediction.top_risk_factors,
        model_version=ml_prediction.model_version,
    )

    # 6. SWOT & Risk Sections
    swot_items = {
        "strengths": [SWOTQuadrantItem(text=i.text, data_source=i.data_source) for i in swot_matrix.strengths],
        "weaknesses": [SWOTQuadrantItem(text=i.text, data_source=i.data_source) for i in swot_matrix.weaknesses],
        "opportunities": [SWOTQuadrantItem(text=i.text, data_source=i.data_source) for i in swot_matrix.opportunities],
        "threats": [SWOTQuadrantItem(text=i.text, data_source=i.data_source) for i in swot_matrix.threats],
    }

    risk_items = [
        RiskMitigationItem(
            risk_id=r.risk_id,
            title=r.title,
            score=r.score,
            severity=r.severity,
            basis=r.basis,
            mitigation=r.mitigation,
            rupee_buffer=r.rupee_buffer,
            data_source=r.data_source,
        ) for r in risk_points
    ]

    # 7. Statutory Checklist
    checklist = _compile_statutory_checklist(
        scheme_id=top_scheme.scheme_id,
        promoter_category=promoter_category,
        sector=sector,
        business_category=business_category,
        project_cost=project_cost,
    )

    return BankDPRDocument(
        dpr_version="2.0",
        generated_at_utc=now_iso,
        section_1_header_and_profile=profile,
        section_2_capital_outlay_and_finance={
            "capital_outlay": outlay_table.model_dump(),
            "means_of_finance": means_of_finance.model_dump(),
        },
        section_3_financial_projections=projections,
        section_4_scheme_optimization=scheme_entries,
        section_5_ml_viability_appraisal=ml_section,
        section_6_swot_and_risk_matrix={
            "swot_analysis": swot_items,
            "risk_matrix": [r.model_dump() for r in risk_items],
            "overall_risk_verdict": risk_verdict,
        },
        section_7_statutory_checklist=checklist,
        tier_3_ai_synthesis=ai_synthesis.to_dict(),
    )


# ---------------------------------------------------------------------------
# Formatted Printable Markdown Export
# ---------------------------------------------------------------------------
def dpr_to_printable_markdown(dpr: BankDPRDocument) -> str:
    """
    Renders the Bank DPR as an official, bank-ready Markdown Credit Appraisal Memo.
    """
    s1 = dpr.section_1_header_and_profile
    s2 = dpr.section_2_capital_outlay_and_finance
    outlay = s2["capital_outlay"]
    finance = s2["means_of_finance"]
    s3 = dpr.section_3_financial_projections
    s4 = dpr.section_4_scheme_optimization
    s5 = dpr.section_5_ml_viability_appraisal
    s6 = dpr.section_6_swot_and_risk_matrix
    s7 = dpr.section_7_statutory_checklist
    ai = dpr.tier_3_ai_synthesis

    lines = [
        f"# 🏛️ DETAILED PROJECT REPORT (DPR) & CREDIT APPRAISAL MEMORANDUM",
        f"**Reference Number**: `{s1.dpr_reference_id}` | **Appraisal Date**: {s1.report_date} | **Format**: SCB / DIC Standard",
        f"**Enterprise Name**: **{s1.enterprise_name}** | **Constitution**: {s1.constitution}",
        f"**Target Location**: {s1.target_village}, {s1.target_block}, {s1.target_district}, {s1.target_state} (Rural: {s1.is_rural})",
        f"**Promoter Profile**: {s1.promoter_name} (Category: `{s1.promoter_category.upper()}` | Gender: {s1.gender})",
        f"\n---\n",
        f"## SECTION 1: EXECUTIVE APPRAISAL & SYNTHESIS",
        f"{ai.get('executive_summary', '')}\n",
        f"### Strategic Action Plan:",
    ]
    for idx, rec in enumerate(ai.get("strategic_recommendations", []), 1):
        lines.append(f"{idx}. {rec}")

    lines.extend([
        f"\n### Bank Loan Officer Notes:",
        f"> {ai.get('bank_appraisal_notes', '')}\n",
        f"\n---\n",
        f"## SECTION 2: CAPITAL OUTLAY & MEANS OF FINANCE",
        f"\n### Capital Outlay Breakdown:",
        f"| Component | % Outlay | Amount (₹) | Description |",
        f"| :--- | :---: | :---: | :--- |",
        f"| **Plant & Machinery** | {outlay['plant_and_machinery']['percentage_of_outlay']:.1f}% | ₹{outlay['plant_and_machinery']['amount_inr']:,.2f} | {outlay['plant_and_machinery']['description']} |",
        f"| **Electrification & Site Works** | {outlay['electrification_and_site_works']['percentage_of_outlay']:.1f}% | ₹{outlay['electrification_and_site_works']['amount_inr']:,.2f} | {outlay['electrification_and_site_works']['description']} |",
        f"| **Working Capital Reserve** | {outlay['initial_working_capital_reserve']['percentage_of_outlay']:.1f}% | ₹{outlay['initial_working_capital_reserve']['amount_inr']:,.2f} | {outlay['initial_working_capital_reserve']['description']} |",
        f"| **Contingency & Pre-Operative** | {outlay['contingency_and_pre_operative']['percentage_of_outlay']:.1f}% | ₹{outlay['contingency_and_pre_operative']['amount_inr']:,.2f} | {outlay['contingency_and_pre_operative']['description']} |",
        f"| **TOTAL CAPITAL OUTLAY** | **100.0%** | **₹{outlay['total_capital_outlay']:,.2f}** | **Total Project Investment** |",
        f"\n### Means of Finance Reconciliation:",
        f"| Financing Source | % Share | Amount (₹) | Scheme / Terms |",
        f"| :--- | :---: | :---: | :--- |",
        f"| **Promoter Margin Contribution** | {finance['promoter_margin_pct']:.1f}% | ₹{finance['promoter_margin_amount']:,.2f} | Own equity funds |",
        f"| **Government Capital Subsidy Grant** | {finance['capital_subsidy_pct']:.1f}% | ₹{finance['capital_subsidy_amount']:,.2f} | {finance['subsidy_scheme_name']} |",
        f"| **Bank Term Loan / Debt** | {finance['bank_term_loan_pct']:.1f}% | ₹{finance['bank_term_loan_amount']:,.2f} | Scheduled Commercial Bank Loan |",
        f"| **TOTAL MEANS OF FINANCE** | **100.0%** | **₹{finance['total_means_of_finance']:,.2f}** | **Balanced: {finance['reconciliation_balanced']}** |",
        f"\n---\n",
        f"## SECTION 3: 5-YEAR FINANCIAL & CASH FLOW PROJECTIONS",
        f"\n**Average 5-Year DSCR**: **{s3.average_dscr:.2f}** (RBI Solvency Benchmark $\\ge 1.33$: **{'MET' if s3.dscr_benchmark_met else 'NOT MET'}**)  ",
        f"**Break-Even Point (BEP)**: **{s3.break_even_point_pct:.1f}%** | **Recommended Price Floor**: ₹{s3.recommended_unit_price_floor:.2f}/unit\n",
        f"| Line Item (₹) | Year 1 (60%) | Year 2 (70%) | Year 3 (80%) | Year 4 (85%) | Year 5 (90%) |",
        f"| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])

    y_objs = s3.projection_years
    rows_to_render = [
        ("Gross Turnover", lambda y: f"₹{y.gross_turnover:,.0f}"),
        ("Raw Materials & Consumables", lambda y: f"₹{y.raw_materials_and_inputs:,.0f}"),
        ("Power, Fuel & Utilities", lambda y: f"₹{y.power_and_utilities:,.0f}"),
        ("Wages & Direct Labor", lambda y: f"₹{y.wages_and_labor:,.0f}"),
        ("Overheads & Administration", lambda y: f"₹{y.overheads_and_maintenance:,.0f}"),
        ("Total Operating Expenses", lambda y: f"₹{y.total_operating_expenses:,.0f}"),
        ("Operating EBITDA", lambda y: f"₹{y.ebitda:,.0f}"),
        ("Depreciation (WDV 15%)", lambda y: f"₹{y.depreciation:,.0f}"),
        ("Bank Term Loan Interest", lambda y: f"₹{y.bank_interest:,.0f}"),
        ("Net Profit After Tax (PAT)", lambda y: f"₹{y.profit_after_tax:,.0f}"),
        ("Total Debt Service (P+I)", lambda y: f"₹{y.total_debt_service:,.0f}"),
        ("Annual DSCR", lambda y: f"{y.annual_dscr:.2f}"),
    ]
    for label, fn in rows_to_render:
        vals = " | ".join(fn(y) for y in y_objs)
        lines.append(f"| **{label}** | {vals} |")

    lines.extend([
        f"\n---\n",
        f"## SECTION 4: GOVERNMENT SCHEME OPTIMIZATION MATRIX",
        f"| Rank | Scheme ID | Full Scheme Name | Grant Subsidy (₹) | Net Benefit (₹) | Collateral-Free |",
        f"| :---: | :--- | :--- | :---: | :---: | :---: |",
    ])
    for s in s4:
        lines.append(f"| #{s.rank} | **{s.scheme_id}** | {s.full_name} | ₹{s.subsidy_grant_amount:,.0f} | ₹{s.net_financial_benefit:,.0f} | {'Yes' if s.collateral_free else 'No'} |")

    lines.extend([
        f"\n---\n",
        f"## SECTION 5: MACHINE LEARNING VIABILITY & RISK ASSESSMENT",
        f"**Viability Verdict**: **`{s5.verdict}`** | **Model Confidence**: **{s5.confidence_pct:.1f}%** | **Engine**: `{s5.model_version}`\n",
        f"**Class Probabilities**: `SUITABLE`: {s5.class_probabilities.get('SUITABLE', 0)*100:.1f}% | `CAUTION`: {s5.class_probabilities.get('CAUTION', 0)*100:.1f}% | `RECONSIDER`: {s5.class_probabilities.get('RECONSIDER', 0)*100:.1f}%\n",
        f"**Primary Positive Drivers**:",
    ])
    for p in s5.top_positive_factors:
        lines.append(f"- {p}")
    lines.append(f"\n**Primary Risk Drivers**:")
    for r in s5.top_risk_factors:
        lines.append(f"- {r}")

    lines.extend([
        f"\n---\n",
        f"## SECTION 6: QUANTIFIED SWOT & 8-POINT RISK MITIGATION TABLE",
        f"\n### 8-Point Quantified Risk Mitigation Table:",
        f"| ID | Risk Title | Severity | Score (/10) | Contingency Buffer | Actionable Mitigation Procedure |",
        f"| :---: | :--- | :---: | :---: | :---: | :--- |",
    ])
    for r in s6["risk_matrix"]:
        buf_str = f"₹{r['rupee_buffer']:,.0f}" if r.get("rupee_buffer") else "Policy / Process"
        lines.append(f"| **{r['risk_id']}** | {r['title']} | `{r['severity']}` | {r['score']:.1f} | {buf_str} | {r['mitigation']} |")

    lines.extend([
        f"\n---\n",
        f"## SECTION 7: STATUTORY BANK SUBMISSION DOCUMENT CHECKLIST",
        f"| Doc Code | Document Description | Classification | Issuing Authority | Mandatory |",
        f"| :---: | :--- | :--- | :--- | :---: |",
    ])
    for doc in s7:
        lines.append(f"| `{doc.document_code}` | **{doc.document_name}** | {doc.category_requirement} | {doc.issuing_authority} | {'✅ YES' if doc.is_mandatory else 'Optional'} |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Print-Ready HTML Document Export
# ---------------------------------------------------------------------------
def dpr_to_html(dpr: BankDPRDocument) -> str:
    """
    Renders the Bank DPR into a styled, professional HTML page ready for browser printing or PDF conversion.
    """
    s1 = dpr.section_1_header_and_profile
    s2 = dpr.section_2_capital_outlay_and_finance
    outlay = s2["capital_outlay"]
    finance = s2["means_of_finance"]
    s3 = dpr.section_3_financial_projections
    s4 = dpr.section_4_scheme_optimization
    s5 = dpr.section_5_ml_viability_appraisal
    s6 = dpr.section_6_swot_and_risk_matrix
    s7 = dpr.section_7_statutory_checklist
    ai = dpr.tier_3_ai_synthesis

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Bank DPR — {s1.enterprise_name} ({s1.dpr_reference_id})</title>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 30px; color: #1e293b; background: #fff; line-height: 1.5; }}
    h1 {{ color: #0f172a; border-bottom: 2px solid #0284c7; padding-bottom: 8px; font-size: 22px; }}
    h2 {{ color: #0369a1; font-size: 16px; margin-top: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
    h3 {{ color: #334155; font-size: 14px; margin-top: 14px; }}
    .header-box {{ background: #f8fafc; border: 1px solid #cbd5e1; padding: 14px; border-radius: 6px; margin-bottom: 20px; }}
    .badge {{ display: inline-block; padding: 3px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; color: #fff; background: #0284c7; }}
    .badge-suitable {{ background: #16a34a; }}
    .badge-caution {{ background: #d97706; }}
    .badge-reconsider {{ background: #dc2626; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 12px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 6px 10px; text-align: left; }}
    th {{ background: #f1f5f9; color: #0f172a; font-weight: 600; }}
    .num {{ text-align: right; }}
    .memo-box {{ background: #eff6ff; border-left: 4px solid #2563eb; padding: 10px 14px; margin: 12px 0; font-size: 12px; }}
    @media print {{ body {{ margin: 10mm; font-size: 11px; }} h1 {{ font-size: 18px; }} h2 {{ font-size: 14px; page-break-after: avoid; }} }}
</style>
</head>
<body>

<div class="header-box">
    <h1>🏛️ DETAILED PROJECT REPORT (DPR) & CREDIT APPRAISAL MEMORANDUM</h1>
    <p><strong>DPR Ref</strong>: <code>{s1.dpr_reference_id}</code> | <strong>Date</strong>: {s1.report_date} | <strong>Enterprise</strong>: <strong>{s1.enterprise_name}</strong> ({s1.constitution})</p>
    <p><strong>Location</strong>: {s1.target_village}, {s1.target_block}, {s1.target_district}, {s1.target_state} | <strong>Promoter</strong>: {s1.promoter_name} ({s1.promoter_category.upper()})</p>
</div>

<h2>1. EXECUTIVE APPRAISAL & SYNTHESIS</h2>
<p>{ai.get('executive_summary', '').replace(chr(10), '<br>')}</p>
<div class="memo-box">
    <strong>Bank Credit Officer Note:</strong> {ai.get('bank_appraisal_notes', '')}
</div>

<h2>2. CAPITAL OUTLAY & MEANS OF FINANCE</h2>
<table>
    <tr><th>Capital Component</th><th class="num">% Outlay</th><th class="num">Amount (₹)</th><th>Description</th></tr>
    <tr><td>Plant & Machinery</td><td class="num">{outlay['plant_and_machinery']['percentage_of_outlay']:.1f}%</td><td class="num">₹{outlay['plant_and_machinery']['amount_inr']:,.2f}</td><td>{outlay['plant_and_machinery']['description']}</td></tr>
    <tr><td>Electrification & Site Works</td><td class="num">{outlay['electrification_and_site_works']['percentage_of_outlay']:.1f}%</td><td class="num">₹{outlay['electrification_and_site_works']['amount_inr']:,.2f}</td><td>{outlay['electrification_and_site_works']['description']}</td></tr>
    <tr><td>Working Capital Reserve</td><td class="num">{outlay['initial_working_capital_reserve']['percentage_of_outlay']:.1f}%</td><td class="num">₹{outlay['initial_working_capital_reserve']['amount_inr']:,.2f}</td><td>{outlay['initial_working_capital_reserve']['description']}</td></tr>
    <tr><td>Contingency & Pre-Operative</td><td class="num">{outlay['contingency_and_pre_operative']['percentage_of_outlay']:.1f}%</td><td class="num">₹{outlay['contingency_and_pre_operative']['amount_inr']:,.2f}</td><td>{outlay['contingency_and_pre_operative']['description']}</td></tr>
    <tr style="font-weight:bold; background:#f8fafc;"><td>TOTAL CAPITAL OUTLAY</td><td class="num">100.0%</td><td class="num">₹{outlay['total_capital_outlay']:,.2f}</td><td>Total Investment</td></tr>
</table>

<table>
    <tr><th>Financing Means</th><th class="num">% Share</th><th class="num">Amount (₹)</th><th>Terms / Source</th></tr>
    <tr><td>Promoter Margin</td><td class="num">{finance['promoter_margin_pct']:.1f}%</td><td class="num">₹{finance['promoter_margin_amount']:,.2f}</td><td>Own equity funds</td></tr>
    <tr><td>Govt Capital Subsidy</td><td class="num">{finance['capital_subsidy_pct']:.1f}%</td><td class="num">₹{finance['capital_subsidy_amount']:,.2f}</td><td>{finance['subsidy_scheme_name']}</td></tr>
    <tr><td>Bank Term Loan</td><td class="num">{finance['bank_term_loan_pct']:.1f}%</td><td class="num">₹{finance['bank_term_loan_amount']:,.2f}</td><td>Term debt facility</td></tr>
    <tr style="font-weight:bold; background:#f8fafc;"><td>TOTAL MEANS OF FINANCE</td><td class="num">100.0%</td><td class="num">₹{finance['total_means_of_finance']:,.2f}</td><td>Balanced: {finance['reconciliation_balanced']}</td></tr>
</table>

<h2>3. 5-YEAR FINANCIAL & CASH FLOW PROJECTIONS</h2>
<p><strong>Average 5-Year DSCR</strong>: <strong>{s3.average_dscr:.2f}</strong> (RBI Solvency Benchmark: {'MET' if s3.dscr_benchmark_met else 'NOT MET'}) | <strong>Break-Even</strong>: {s3.break_even_point_pct:.1f}%</p>
<table>
    <tr>
        <th>Metric (₹)</th>
        {" ".join(f"<th class='num'>Yr {y.year} ({y.capacity_utilization_pct:.0f}%)</th>" for y in s3.projection_years)}
    </tr>
    <tr><td>Gross Revenue</td>{" ".join(f"<td class='num'>₹{y.gross_turnover:,.0f}</td>" for y in s3.projection_years)}</tr>
    <tr><td>Operating Expenses</td>{" ".join(f"<td class='num'>₹{y.total_operating_expenses:,.0f}</td>" for y in s3.projection_years)}</tr>
    <tr><td>Operating EBITDA</td>{" ".join(f"<td class='num'>₹{y.ebitda:,.0f}</td>" for y in s3.projection_years)}</tr>
    <tr><td>Depreciation</td>{" ".join(f"<td class='num'>₹{y.depreciation:,.0f}</td>" for y in s3.projection_years)}</tr>
    <tr><td>Bank Interest</td>{" ".join(f"<td class='num'>₹{y.bank_interest:,.0f}</td>" for y in s3.projection_years)}</tr>
    <tr><td>Net Profit After Tax</td>{" ".join(f"<td class='num'>₹{y.profit_after_tax:,.0f}</td>" for y in s3.projection_years)}</tr>
    <tr><td>Debt Service (P+I)</td>{" ".join(f"<td class='num'>₹{y.total_debt_service:,.0f}</td>" for y in s3.projection_years)}</tr>
    <tr style="font-weight:bold; background:#f8fafc;"><td>Annual DSCR</td>{" ".join(f"<td class='num'>{y.annual_dscr:.2f}</td>" for y in s3.projection_years)}</tr>
</table>

<h2>4. MACHINE LEARNING VIABILITY APPRAISAL</h2>
<p><strong>Viability Rating</strong>: <span class="badge badge-{'suitable' if s5.verdict == 'SUITABLE' else 'caution' if s5.verdict == 'CAUTION' else 'reconsider'}">{s5.verdict} ({s5.confidence_pct:.1f}% Confidence)</span></p>

<h2>5. STATUTORY BANK SUBMISSION DOCUMENT CHECKLIST</h2>
<table>
    <tr><th>Code</th><th>Document Name</th><th>Classification</th><th>Issuing Authority</th><th>Mandatory</th></tr>
    {" ".join(f"<tr><td><code>{d.document_code}</code></td><td><strong>{d.document_name}</strong></td><td>{d.category_requirement}</td><td>{d.issuing_authority}</td><td>{'Yes' if d.is_mandatory else 'Optional'}</td></tr>" for d in s7)}
</table>

</body>
</html>
"""
    return html


if __name__ == "__main__":
    print("dpr_generator module compiled successfully.")
